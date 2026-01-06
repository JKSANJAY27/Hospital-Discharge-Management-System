"""
Minimal chain implementations for Discharge Simplification workflow
"""

from typing import Dict, Any
import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def robust_json_parse(text: str) -> Dict[str, Any]:
    """Parse JSON with comment removal and error handling"""
    try:
        # Remove // comments
        text = re.sub(r'//.*?(?=\n|$)', '', text)
        # Remove /* */ comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Parse JSON
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try to extract JSON from markdown code blocks
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise e


class SafetyGuardrailChain:
    """
    Minimal safety check for discharge document processing.
    Only checks for PII and harmful content - no intent classification needed.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a safety checker for medical discharge documents.

**YOUR ONLY JOB:**
Check if the input contains:
1. Personal identifiable information that should be redacted: credit cards, SSN, Aadhaar numbers, passport numbers
2. Harmful content: violence, hate speech, illegal activities

**IMPORTANT:**
- Medical conditions, symptoms, and health information are SAFE and expected.
- Return JSON: {"is_safe": true/false, "reason": "explanation"}
"""),
            ("user", "{input}")
        ])
    
    def check(self, text: str) -> Dict[str, Any]:
        """Check if text is safe to process"""
        chain = self.prompt | self.llm | StrOutputParser()
        result_str = chain.invoke({"input": text})
        
        try:
            result = robust_json_parse(result_str)
            return result
        except Exception as e:
            print(f"⚠️ Safety check parsing failed: {e}")
            # Default to safe if parsing fails
            return {"is_safe": True, "reason": "Parsing error - defaulting to safe"}
