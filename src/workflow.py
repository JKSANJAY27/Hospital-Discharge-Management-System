"""
Main healthcare workflow with optimized discharge simplification
"""
import asyncio
from typing import Dict, Any, List, Optional
from .config import HealthcareConfig
from .chains import (
    GuardrailAndIntentChain,
    DischargeSimplifierChain,
    HospitalLocatorChain,
    SymptomCheckerChain
)
from .schemas import DischargeOutputSchema

class HealthcareWorkflow:
    """Main workflow orchestrator for Discharge Simplification system"""
    
    def __init__(self, config: HealthcareConfig):
        self.config = config
        
        # === KEY 1 (PRIMARY): Critical path ===
        print("   -> Initializing workflows...")
        self.guardrail_and_intent = GuardrailAndIntentChain(config.llm_primary)
        self.symptom_chain = SymptomCheckerChain(config.llm_primary)
        
        # === KEY 2 (SECONDARY): specialized chains ===
        self.discharge_chain = DischargeSimplifierChain(config.llm_secondary)
        self.hospital_chain = HospitalLocatorChain(config.llm_secondary, config.search_tool)
        
        print("   ✓ All chains initialized")

    async def process_discharge_document(self, text: str) -> Dict[str, Any]:
        """
        Direct entry point for processing discharge documents.
        Bypasses intent classification.
        """
        print(f"📄 Processing discharge document ({len(text)} chars)...")
        
        # Run safety check ONLY - skipping intent classification as we know the intent
        # using the internal chain of GuardrailAndIntentChain if possible, or just trusting the source for now.
        # Ideally we check for PII here if we were storing it, but for simplification we just process.
        
        try:
            # Run the simplification chain
            # Run in thread executor because LangChain invoke is sync
            result_schema = await asyncio.to_thread(self.discharge_chain.run, text)
            
            # Convert Pydantic model to dict
            return result_schema.dict()
            
        except Exception as e:
            print(f"❌ Error processing discharge document: {e}")
            return {"error": str(e)}

    async def run(self, user_input: str, query_for_classification: str, user_profile: Any = None, conversation_history: str = "", user_location: Optional[tuple] = None, response_language: str = "English") -> Dict[str, Any]:
        """Execute the workflow based on user chat input"""
        
        print(f"🔍 [WORKFLOW] run() called for input: '{user_input[:50]}...'")

        # Step 1: Safety Check & Intent Classification
        print("🛡️🎯 [STEP 1] Safety Check & Intent Classification...")
        combined_result = self.guardrail_and_intent.check_and_classify(query_for_classification)
        
        if not combined_result.get("is_safe", True):
            return {"status": "blocked", "reason": combined_result.get("safety_reason")}
        
        primary_intent = combined_result.get("primary_intent")
        print(f"   → Primary Intent: {primary_intent}")
        
        result = {
            "intent": primary_intent, 
            "reasoning": combined_result.get("reasoning"), 
            "output": None
        }
        
        # Step 2: Route to appropriate agent
        if primary_intent == "discharge_simplification":
             # If user pasted text in chat, we can try to process it. 
             # But usually this intent might trigger a prompt to upload a document.
             if len(user_input) > 200: # heuristic: if long text, maybe it IS the note
                 processed = await self.process_discharge_document(user_input)
                 # Format the simplified summary for chat response
                 summary = processed.get("simplified_summary", "")
                 result["output"] = f"**Simplified Summary:**\n{summary}\n\n(See the 'Discharge' tab for the full action plan)"
                 result["data"] = processed
             else:
                 result["output"] = "Please upload your discharge summary using the 'Discharge Simplifier' tab, or paste the text here if you'd like me to simplify it."
        
        elif primary_intent == "facility_locator_support":
            result["output"] = await asyncio.to_thread(self.hospital_chain.run, user_input)
            
        elif primary_intent == "symptom_checker":
            # Simple symptom checker run
            symptom_data = await asyncio.to_thread(self.symptom_chain.run, user_input)
            if symptom_data.is_emergency:
                result["output"] = "🚨 **POSSIBLE EMERGENCY DETECTED**\n\nBased on your symptoms, please seek immediate medical attention or go to the nearest emergency room."
            else:
                result["output"] = "I've noted your symptoms. Since I am an AI, I cannot provide a diagnosis. However, based on what you described, you should monitor these symptoms. If they worsen, please consult a doctor."
                
        elif primary_intent == "general_conversation":
             result["output"] = "I am your Discharge Support Agent. I can help you understand your medical notes, create action plans, or find nearby clinics. How can I help?"
             
        else:
            result["output"] = "I'm not sure how to help with that. I specialize in simplifying discharge instructions and finding healthcare facilities."

        print("   ✓ Workflow execution complete\n")
        return result