"""
Discharge Simplification Chain - The core of the system
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from ..schemas import DischargeOutputSchema


class DischargeSimplifierChain:
    """
    Transform complex medical discharge summaries into plain language (6th-8th grade level).
    Generates action plans, danger signs, and follow-up schedules.
    
    This is the PRIMARY agent in the system.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Medical Discharge Instruction Simplifier. 
Your goal is to transform complex clinical discharge notes into a clear, safe, and actionable guide for the patient.

**INPUT DATA:**
- Use the provided discharge note text.
- Incorporate general medical knowledge from public care instructions (CDC/MedlinePlus equivalent).

**OUTPUT REQUIREMENTS (Strict JSON Schema):**

1. **simplified_summary** (REQUIRED):
   - Write a plain-language summary at 6th-8th grade reading level
   - Avoid medical jargon - use simple words
   - Explain WHY they were admitted and WHAT happened
   - Examples of simplification:
     * "Edema" → "Swelling"
     * "Utilize" → "Use"  
     * "Ambulate" → "Walk"
     * "Hypertension" → "High blood pressure"

2. **action_plan** (REQUIRED):
   - Break down by specific timeframes: "Day 1 (Today)", "Day 2", "Week 1", "Week 2", etc.
   - Each day should have:
     * **tasks**: Specific, clear actions (e.g., "Take 1 blue pill with breakfast", "Change bandage at 8 PM", "Walk for 10 minutes")
     * **medications**: List of medications for that timeframe
   - Be VERY specific with times and quantities

3. **danger_signs** (REQUIRED):
   - List immediate "Red Flags" that require calling doctor/911
   - Be specific (e.g., "Fever over 101°F", "Chest pain", "Difficulty breathing")
   - Include "Call 911 if you experience any of these"

4. **medication_list** (REQUIRED):
   - Format: "Name - Purpose - Usage"
   - Example: "Metformin - For blood sugar - Take 1 pill with breakfast and dinner"
   - Include ALL medications mentioned in discharge notes

5. **wound_care** (OPTIONAL):
   - Specific wound care instructions if applicable
   - Include frequency and technique

6. **activity_restrictions** (OPTIONAL):
   - What they CANNOT do
   - Examples: "No lifting over 5 lbs", "No driving for 2 weeks"

7. **follow_up_schedule** (REQUIRED):
   - Who to see, when, and why
   - Format: 
     * specialist: "Cardiologist", "Primary Care Doctor"
     * when: "Within 1 week", "In 2 weeks"
     * purpose: "Check heart function", "Remove stitches"

8. **lifestyle_changes** (REQUIRED):
   - Diet modifications, exercise, smoking cessation, etc.
   - Be specific and actionable

9. **citations** (REQUIRED):
   - Add links to trusted public sources relevant to their condition
   - Examples: "MedlinePlus: Heart Failure Care", "CDC: Diabetes Management"

**TONE:**
- Empathetic, clear, and directive
- Use "you" language (e.g., "You should take...")
- Be encouraging but realistic

**SAFETY:**
- If critical values or severe conditions are mentioned, highlight them in danger signs
- Do NOT make up medications not in the text
- If information is missing, say "Ask your doctor about..."

**READABILITY:**
- Target 6th-8th grade reading level (Flesch-Kincaid)
- Short sentences (under 20 words)
- Active voice
- Common words only
"""),
            ("user", "Here are the discharge instructions/medical notes:\n\n{input_text}")
        ])
    
    def run(self, document_text: str) -> DischargeOutputSchema:
        """
        Process discharge document and return structured output.
        
        Args:
            document_text: Raw discharge note text
            
        Returns:
            DischargeOutputSchema with all required fields
        """
        print(f"      → DischargeSimplifier: Processing {len(document_text)} chars of text...")
        
        # Use structured output for strict schema validation
        structured_llm = self.llm.with_structured_output(DischargeOutputSchema)
        chain = self.prompt | structured_llm
        
        try:
            result = chain.invoke({"input_text": document_text})
            print(f"      ← Simplification complete. Summary length: {len(result.simplified_summary)}")
            print(f"      ← Action plan has {len(result.action_plan)} days")
            print(f"      ← {len(result.danger_signs)} danger signs identified")
            return result
        except Exception as e:
            print(f"      ❌ DischargeSimplifier failed: {e}")
            raise e


class PatientEducationChain:
    """
    Suggests patient education videos and resources for recovery.
    Replacement for the old Yoga/Exercise recommendation feature.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Patient Education Expert.
Your goal is to find the best Search Queries to find helpful RECOVERY and REHABILITATION videos on YouTube for a patient.

**INPUT:**
- Patient's condition or procedure (e.g., "Total Knee Replacement", "Heart Failure", "Type 2 Diabetes")

**OUTPUT requirements (JSON):**
1. **search_queries**: Generate 3-5 specific, safe search queries for YouTube.
   - Focus on: "Exercises for...", "Diet for...", "Recovery tips for...", "What to expect after..."
   - AVOID generic "Yoga" unless specifically helpful for mobility.
   - Example: ["Post-op knee exercises phase 1", "How to climb stairs after knee replacement", "Anti-inflammatory diet for knee pain"]

2. **recovery_tips**: List 3 key quick tips for this condition.

**JSON FORMAT:**
{{
    "search_queries": ["query1", "query2", "query3"],
    "recovery_tips": ["tip1", "tip2", "tip3"]
}}"""),
            ("user", "Patient condition/context: {context}")
        ])
        
    def run(self, context: str) -> Dict[str, Any]:
        """
        Generate video search queries for the condition.
        """
        from langchain_core.output_parsers import JsonOutputParser
        
        chain = self.prompt | self.llm | JsonOutputParser()
        try:
            return chain.invoke({"context": context})
        except Exception as e:
            print(f"Error in PatientEducationChain: {e}")
            return {"search_queries": [f"{context} recovery exercises", f"{context} diet tips"], "recovery_tips": []}