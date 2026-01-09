"""
Discharge Simplification Workflow - Streamlined for single purpose

Agent Lightning Integration:
- Set use_agent_lightning=True to enable span tracing for training
- Rewards are emitted for evaluation metrics (readability, completeness, safety)
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from .config import HealthcareConfig
from .chains.base_chains import SafetyGuardrailChain
from .chains.specialized_chains import DischargeSimplifierChain, PatientEducationChain
from .schemas import DischargeOutputSchema
from .document_processor.discharge_loader import DischargeLoader
from .utils.calendar_generator import CalendarGenerator

# Optional Agent Lightning integration
# Note: On Windows, some Agent Lightning features may be limited due to gunicorn's Unix dependency
try:
    import agentlightning as agl
    AGENT_LIGHTNING_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    AGENT_LIGHTNING_AVAILABLE = False
    agl = None
    # Don't print warning during normal import - only when explicitly trying to use it
    _AGENT_LIGHTNING_IMPORT_ERROR = str(e)


class DischargeWorkflow:
    """
    Main workflow for discharge instruction simplification.
    
    Agent Lightning Integration:
        When use_agent_lightning=True, the workflow emits rewards and traces
        that can be used for training with APO or RL algorithms.
    """
    
    def __init__(self, config: HealthcareConfig, use_agent_lightning: bool = False):
        self.config = config
        self.use_agent_lightning = use_agent_lightning and AGENT_LIGHTNING_AVAILABLE
        
        print("   → Initializing Discharge Simplification Workflow...")
        if self.use_agent_lightning:
            print("   → Agent Lightning integration ENABLED")
        
        # Safety guardrail (minimal)
        self.safety_chain = SafetyGuardrailChain(config.llm_primary)
        
        # Main discharge simplifier
        self.discharge_chain = DischargeSimplifierChain(config.llm_secondary)

        # Video/Education Chain (New)
        self.education_chain = PatientEducationChain(config.llm_secondary)
        
        print("   ✓ Discharge workflow initialized")

    async def run(
        self,
        user_input: str,
        query_for_classification: str = None,
        user_profile: dict = None,
        conversation_history: list = None,
        user_location: tuple = None,
        response_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Main chat entry point.
        """
        print(f"\n💬 Chat Request: {user_input}")
        
        intent = "general_chat"
        video_resources = None
        
        # Simple keyword detection for education/video intent
        keywords = ["video", "youtube", "exercise", "rehab", "recovery", "workout", "physio"]
        if any(k in user_input.lower() for k in keywords):
            print("   → Detected Patient Education/Video intent")
            intent = "patient_education"
            try:
                edu_result = await asyncio.to_thread(self.education_chain.run, user_input)
                video_resources = edu_result
            except Exception as e:
                print(f"   ⚠️ Education chain failed: {e}")
        
        messages = [
            ("system", "You are a helpful healthcare assistant named Swastha. You help users with discharge instructions, recovery advice, and general health queries."),
            ("user", user_input)
        ]
        
        response = await self.config.llm_primary.ainvoke(messages)
        output_text = response.content
        
        # Append video recommendations to text if found
        if video_resources and video_resources.get("search_queries"):
            output_text += "\n\n**Recommended Recovery Videos (YouTube):**\n"
            for q in video_resources["search_queries"]:
                output_text += f"- [{q}](https://www.youtube.com/results?search_query={q.replace(' ', '+')})\n"
            
            if video_resources.get("recovery_tips"):
                 output_text += "\n**Quick Recovery Tips:**\n"
                 for tip in video_resources["recovery_tips"]:
                     output_text += f"- {tip}\n"
        
        return {
            "output": output_text,
            "intent": intent,
            "confidence": 1.0,
            "sources": [],
            "nearby_hospitals": None, 
            "profile_updated": False
        }

    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a discharge summary file (PDF, TXT, DOCX).
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {"error": f"File not found: {file_path}", "status": "failed"}
            
        print(f"\n📂 Loading file: {file_path}")
        text = DischargeLoader.load_discharge_summary(path_obj)
        
        if not text:
            return {"error": "Could not extract text from file", "status": "failed"}
            
        return await self.process_with_evaluation(text)

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
            
            # Step 2a: Generate Calendar File (ICS)
            print("📅 [STEP 2a] Generating calendar reminders...")
            ics_content = CalendarGenerator.generate_ics(
                result_dict.get("action_plan", []),
                result_dict.get("follow_up_schedule", [])
            )
            result_dict["ics_content"] = ics_content
            # We don't write to file here to keep it pure, but the caller can write it
            
            print("   ✓ Simplification and Calendar generation complete\n")
            return result_dict
            
        except Exception as e:
            print(f"   ❌ Error during simplification: {e}")
            import traceback
            traceback.print_exc()
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
        
        # Agent Lightning: Emit reward for training if enabled
        if self.use_agent_lightning and agl is not None:
            # Calculate composite reward score [0, 1]
            reward = self._calculate_training_reward(evaluation)
            agl.emit_reward(reward, attributes={
                "readability_score": evaluation["readability_score"],
                "safety_warnings_present": evaluation["safety_warnings_present"],
                "completeness_ratio": sum(1 for v in evaluation["completeness"].values() if v) / len(evaluation["completeness"]),
            })
            print(f"   📊 Agent Lightning reward emitted: {reward:.3f}")
        
        return result
    
    def _calculate_training_reward(self, evaluation: Dict[str, Any]) -> float:
        """
        Calculate a training reward [0, 1] from evaluation metrics.
        
        Scoring:
        - Readability (0-0.3): Target 6-8 grade level
        - Completeness (0-0.4): All required fields present
        - Safety (0-0.3): Danger signs identified
        """
        reward = 0.0
        
        # Readability score (target 6-8)
        readability = evaluation.get("readability_score", 12)
        if 6 <= readability <= 8:
            reward += 0.3
        elif 4 <= readability <= 10:
            reward += 0.2
        elif 2 <= readability <= 12:
            reward += 0.1
        
        # Completeness score
        completeness = evaluation.get("completeness", {})
        fields_present = sum(1 for v in completeness.values() if v)
        reward += (fields_present / max(len(completeness), 1)) * 0.4
        
        # Safety score
        if evaluation.get("safety_warnings_present"):
            reward += 0.3
        
        return min(1.0, reward)

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