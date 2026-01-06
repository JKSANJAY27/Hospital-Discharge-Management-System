"""
Discharge Simplification Workflow - Streamlined for single purpose
"""

import asyncio
from typing import Dict, Any
from .config import HealthcareConfig
from .chains import SafetyGuardrailChain, DischargeSimplifierChain
from .schemas import DischargeOutputSchema


class DischargeWorkflow:
    """
    Simplified workflow focused ONLY on discharge instruction simplification.
    
    This workflow:
    1. Checks for safety/PII
    2. Simplifies discharge instructions
    3. Returns structured output
    """
    
    def __init__(self, config: HealthcareConfig):
        self.config = config
        
        print("   → Initializing Discharge Simplification Workflow...")
        
        # Safety guardrail (minimal)
        self.safety_chain = SafetyGuardrailChain(config.llm_primary)
        
        # Main discharge simplifier (the core agent)
        self.discharge_chain = DischargeSimplifierChain(config.llm_secondary)
        
        print("   ✓ Discharge workflow initialized")

    async def process_discharge_document(self, text: str, skip_safety_check: bool = False) -> Dict[str, Any]:
        """
        Main entry point for processing discharge documents.
        
        Args:
            text: Raw discharge document text
            skip_safety_check: If True, skip PII check (use for trusted sources)
            
        Returns:
            Dictionary with simplified discharge instructions
        """
        print(f"\n📄 Processing discharge document ({len(text)} chars)...")
        
        # Step 1: Safety check (optional)
        if not skip_safety_check:
            print("🛡️ [STEP 1] Safety check...")
            safety_result = await asyncio.to_thread(self.safety_chain.check, text)
            
            if not safety_result.get("is_safe", True):
                print(f"   ❌ Safety check failed: {safety_result.get('reason')}")
                return {
                    "error": "Safety check failed",
                    "reason": safety_result.get("reason"),
                    "status": "blocked"
                }
            print("   ✓ Safety check passed")
        
        # Step 2: Simplify discharge instructions
        print("📋 [STEP 2] Simplifying discharge instructions...")
        try:
            result_schema: DischargeOutputSchema = await asyncio.to_thread(
                self.discharge_chain.run, 
                text
            )
            
            # Convert Pydantic model to dict
            result_dict = result_schema.dict()
            result_dict["status"] = "success"
            
            print("   ✓ Simplification complete\n")
            return result_dict
            
        except Exception as e:
            print(f"   ❌ Error during simplification: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }

    async def process_with_evaluation(self, text: str) -> Dict[str, Any]:
        """
        Process discharge document AND add evaluation metrics.
        
        This adds:
        - Readability score (Flesch-Kincaid)
        - Completeness check
        - Safety warning validation
        
        Returns:
            Dictionary with results + evaluation metrics
        """
        result = await self.process_discharge_document(text)
        
        if result.get("status") != "success":
            return result
        
        # Add evaluation metrics
        print("📊 [STEP 3] Evaluating output quality...")
        
        evaluation = {
            "readability_score": self._calculate_readability(result.get("simplified_summary", "")),
            "completeness": self._check_completeness(result),
            "safety_warnings_present": len(result.get("danger_signs", [])) > 0,
            "plan_usability": self._assess_plan_usability(result.get("action_plan", []))
        }
        
        result["evaluation"] = evaluation
        print(f"   ✓ Evaluation complete: Readability={evaluation['readability_score']:.1f}")
        
        return result

    def _calculate_readability(self, text: str) -> float:
        """
        Calculate Flesch-Kincaid Grade Level.
        Target: 6-8 grade level
        """
        if not text:
            return 0.0
        
        # Simple approximation (for production, use textstat library)
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        if sentences == 0:
            sentences = 1
        
        syllables = sum(self._count_syllables(word) for word in words)
        
        # Flesch-Kincaid formula
        grade_level = 0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
        return max(0, grade_level)

    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count"""
        word = word.lower()
        vowels = 'aeiouy'
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            count -= 1
        
        return max(1, count)

    def _check_completeness(self, result: Dict[str, Any]) -> Dict[str, bool]:
        """Check if all required fields are present and non-empty"""
        return {
            "has_summary": bool(result.get("simplified_summary")),
            "has_action_plan": len(result.get("action_plan", [])) > 0,
            "has_danger_signs": len(result.get("danger_signs", [])) > 0,
            "has_medications": len(result.get("medication_list", [])) > 0,
            "has_follow_up": len(result.get("follow_up_schedule", [])) > 0,
            "has_citations": len(result.get("citations", [])) > 0
        }

    def _assess_plan_usability(self, action_plan: list) -> Dict[str, Any]:
        """Assess if action plan is usable"""
        if not action_plan:
            return {"usable": False, "reason": "No action plan"}
        
        total_tasks = sum(len(day.get("tasks", [])) for day in action_plan)
        has_specific_times = any("AM" in str(task) or "PM" in str(task) or ":" in str(task) 
                                 for day in action_plan 
                                 for task in day.get("tasks", []))
        
        return {
            "usable": total_tasks > 0,
            "total_days": len(action_plan),
            "total_tasks": total_tasks,
            "has_specific_times": has_specific_times
        }


# Backward compatibility alias
HealthcareWorkflow = DischargeWorkflow