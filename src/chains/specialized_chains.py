"""
Specialized chain implementations for Discharge Simplification and Follow-up
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from ..schemas import DischargeOutputSchema

class SearchBasedChain:
    """Base class for chains that use web search"""
    
    def __init__(self, llm, search_tool, system_prompt: str):
        self.llm = llm
        self.search_tool = search_tool
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
    
    def search_and_generate(self, query: str, search_query: str) -> str:
        """Perform search and generate response"""
        print(f"      → Searching for '{search_query}'...")
        if self.search_tool:
            search_results = self.search_tool.invoke(search_query)
            print(f"      → Found {len(search_results) if isinstance(search_results, list) else 'some'} results")
        else:
            search_results = "No search tool configured."

        print(f"      → Generating response...")
        chain = self.prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "input": query,
            "search_results": json.dumps(search_results, indent=2)
        })
        return response

class HospitalLocatorChain(SearchBasedChain):
    def __init__(self, llm, search_tool):
        system_prompt = "You are a healthcare facility locator. Extract location from the query, search for nearby facilities, and list them with details.\nSearch results:\n{search_results}"
        super().__init__(llm, search_tool, system_prompt)
    def run(self, user_input: str) -> str:
        search_query = f"hospitals healthcare facilities near {user_input}"
        return self.search_and_generate(user_input, search_query)


class DischargeSimplifierChain:
    """
    Chain to simplify medical discharge summaries into plain language (6th-8th grade level).
    Generates action plans, danger signs, and follow-up schedules.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Medical Discharge Instruction Simplifier. 
Your goal is to transform complex clinical discharge notes into a clear, safer, and actionable guide for the patient.

**INPUT DATA:**
- Use the provided discharge note text.
- Optionally, incorporate general medical knowledge for public care instructions (CDC/MedlinePlus equivalent).

**OUTPUT REQUIREMENTS (Strict JSON):**
1. **simplified_summary**: Write a plain-language summary (6th-8th grade reading level). Avoid jargon. Explain *why* they were admitted and *what* happened, simply.
2. **action_plan**: specific daily tasks. 
   - Break down by "Day 1 (Today)", "Day 2", "Week 1", etc.
   - Include specific clear actions like "Take 1 blue pill", "Change bandage", "Walk for 10 mins".
3. **danger_signs**: List of immediate "Red Flags". If the patient sees these, they must call a doctor/911.
4. **medication_list**: Simplified list. Format: "Name - Purpose - Usage". (e.g., "Metformin - For sugar - Take 1 with breakfast")
5. **wound_care**: Specific instructions if mentioned.
6. **activity_restrictions**: What they CANNOT do (e.g., "No lifting > 5 lbs").
7. **follow_up_schedule**: Who to see and when.
8. **lifestyle_changes**: Diet, smoking, etc.
9. **citations**: Add general trusted sources (e.g., "See MedlinePlus on Heart Failure") if relevant to the condition.

**TONE:**
- Empathetic, clear, and directive.
- Use simple words ("Use" instead of "Utilize", "Swelling" instead of "Edema").

**SAFETY:**
- If the note mentions critical values or severe conditions, highlight them in danger signs.
- Do not make up medications not in the text.
"""),
            ("user", "Here are the discharge instructions/medical notes:\n\n{input_text}")
        ])
    
    def run(self, document_text: str) -> DischargeOutputSchema:
        print(f"      → DischargeSimplifier: Processing {len(document_text)} chars of text...")
        
        # Use structured output for strict schema validation
        structured_llm = self.llm.with_structured_output(DischargeOutputSchema)
        chain = self.prompt | structured_llm
        
        try:
            result = chain.invoke({"input_text": document_text})
            print(f"      ← Simplification complete. Summary length: {len(result.simplified_summary)}")
            return result
        except Exception as e:
            print(f"      ❌ DischargeSimplifier failed: {e}")
            # Return a fallback or re-raise depending on strictness
            raise e