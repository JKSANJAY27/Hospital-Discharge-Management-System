"""
Grading (Reward) Functions for Agent Lightning Training

These functions evaluate agent outputs and return reward scores [0, 1]
for training. They are used by the APO algorithm to learn which prompts
produce better results.

Note: These functions are standalone and don't import agentlightning,
making them usable even on Windows where full Agent Lightning may not work.
"""

import re
import json
from typing import Dict, Any, List, Optional


def grade_discharge_simplification(
    output: Dict[str, Any],
    expected: Optional[Dict[str, Any]] = None
) -> float:
    """
    Grade the discharge simplification output.
    
    Scoring based on:
    - Readability (0-0.3): Flesch-Kincaid grade 6-8 is optimal
    - Completeness (0-0.4): All required fields present and non-empty
    - Safety (0-0.3): Danger signs present and appropriate
    
    Args:
        output: DischargeOutputSchema dict from the agent
        expected: Optional ground truth for comparison
        
    Returns:
        float: Reward score between 0.0 and 1.0
    """
    if not output or output.get("status") == "failed":
        return 0.0
    
    total_score = 0.0
    
    # 1. Readability Score (0-0.3)
    summary = output.get("simplified_summary", "")
    if summary:
        readability = calculate_readability(summary)
        # Target is grade 6-8, penalize if too high or too low
        if 6 <= readability <= 8:
            readability_score = 0.3
        elif 4 <= readability <= 10:
            readability_score = 0.2
        elif 2 <= readability <= 12:
            readability_score = 0.1
        else:
            readability_score = 0.05
        total_score += readability_score
    
    # 2. Completeness Score (0-0.4)
    completeness = check_completeness(output)
    required_fields = ["has_summary", "has_action_plan", "has_danger_signs", 
                       "has_medications", "has_follow_up"]
    
    fields_present = sum(1 for f in required_fields if completeness.get(f, False))
    completeness_score = (fields_present / len(required_fields)) * 0.4
    total_score += completeness_score
    
    # 3. Safety Score (0-0.3)
    danger_signs = output.get("danger_signs", [])
    if len(danger_signs) >= 3:
        safety_score = 0.3
    elif len(danger_signs) >= 1:
        safety_score = 0.2
    else:
        safety_score = 0.0
    
    # Bonus: Check if danger signs are specific (contain numbers or specific conditions)
    # Handle both string items and dict items (LLM may return either)
    def extract_text(item):
        """Extract text from string or dict."""
        if isinstance(item, str):
            return item
        elif isinstance(item, dict):
            # Try common keys for text content
            return str(item.get("sign") or item.get("description") or item.get("text") or item)
        return str(item)
    
    specific_signs = []
    for s in danger_signs:
        text = extract_text(s)
        if any(c.isdigit() for c in text) or any(w in text.lower() for w in ["fever", "pain", "breathing", "call"]):
            specific_signs.append(s)
    
    if len(specific_signs) >= 2:
        safety_score = min(0.3, safety_score + 0.05)
    
    total_score += safety_score
    
    return min(1.0, total_score)


def grade_patient_education(
    output: Dict[str, Any],
    context: str = ""
) -> float:
    """
    Grade the patient education output.
    
    Scoring based on:
    - Query quality (0-0.6): Specific, actionable video search queries
    - Tip quality (0-0.4): Relevant recovery tips
    
    Args:
        output: PatientEducationChain output dict
        context: Original patient context for relevance checking
        
    Returns:
        float: Reward score between 0.0 and 1.0
    """
    if not output:
        return 0.0
    
    total_score = 0.0
    
    # 1. Query Quality (0-0.6)
    queries = output.get("search_queries", [])
    if queries:
        # Score based on number of queries (3-5 is optimal)
        if 3 <= len(queries) <= 5:
            query_count_score = 0.2
        elif 1 <= len(queries) <= 2:
            query_count_score = 0.1
        else:
            query_count_score = 0.05
        
        # Score based on specificity (contains action words)
        action_words = ["exercise", "diet", "recovery", "tips", "how to", 
                        "after", "before", "during", "phase", "steps"]
        specific_queries = [q for q in queries if any(w in q.lower() for w in action_words)]
        specificity_score = min(0.4, (len(specific_queries) / max(len(queries), 1)) * 0.4)
        
        total_score += query_count_score + specificity_score
    
    # 2. Tip Quality (0-0.4)
    tips = output.get("recovery_tips", [])
    if tips:
        if len(tips) >= 3:
            tip_count_score = 0.2
        elif len(tips) >= 1:
            tip_count_score = 0.1
        else:
            tip_count_score = 0.0
        
        # Score based on actionability (contains verbs)
        action_patterns = ["do", "avoid", "take", "eat", "drink", "rest", "walk", "call"]
        actionable_tips = [t for t in tips if any(w in t.lower() for w in action_patterns)]
        actionability_score = min(0.2, (len(actionable_tips) / max(len(tips), 1)) * 0.2)
        
        total_score += tip_count_score + actionability_score
    
    return min(1.0, total_score)


def grade_safety_check(
    output: Dict[str, Any],
    expected_is_safe: Optional[bool] = None,
    text: str = ""
) -> float:
    """
    Grade the safety check output.
    
    Scoring based on:
    - Correct classification (0-0.7): Match with expected result
    - Reason quality (0-0.3): Clear, specific reasoning
    
    Args:
        output: SafetyGuardrailChain output dict
        expected_is_safe: Ground truth for the safety check
        text: Original text that was checked
        
    Returns:
        float: Reward score between 0.0 and 1.0
    """
    if not output:
        return 0.0
    
    total_score = 0.0
    is_safe = output.get("is_safe", True)
    reason = output.get("reason", "")
    
    # 1. Classification Score (0-0.7)
    if expected_is_safe is not None:
        if is_safe == expected_is_safe:
            total_score += 0.7
        else:
            total_score += 0.0
    else:
        # No ground truth - basic heuristic
        # Medical text should generally be safe
        if is_safe:
            total_score += 0.5
        else:
            # Check if there's a good reason for marking unsafe
            pii_keywords = ["ssn", "credit card", "social security", "aadhaar", "passport"]
            if any(kw in reason.lower() for kw in pii_keywords):
                total_score += 0.5
            else:
                total_score += 0.2
    
    # 2. Reason Quality (0-0.3)
    if reason:
        if len(reason) >= 20:
            total_score += 0.15
        if len(reason) >= 50:
            total_score += 0.1
        # Bonus for specific reasoning
        if any(word in reason.lower() for word in ["medical", "health", "clinical", "safe"]):
            total_score += 0.05
    
    return min(1.0, total_score)


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_readability(text: str) -> float:
    """
    Calculate Flesch-Kincaid Grade Level.
    
    Args:
        text: Text to analyze
        
    Returns:
        float: Approximate grade level (6-8 is target for patient communication)
    """
    if not text:
        return 0.0
    
    words = text.split()
    if not words:
        return 0.0
    
    sentences = max(1, text.count('.') + text.count('!') + text.count('?'))
    syllables = sum(count_syllables(word) for word in words)
    
    # Flesch-Kincaid formula
    grade_level = 0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
    return max(0, grade_level)


def count_syllables(word: str) -> int:
    """Count syllables in a word (approximation)."""
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


def check_completeness(result: Dict[str, Any]) -> Dict[str, bool]:
    """Check if all required fields are present and non-empty."""
    return {
        "has_summary": bool(result.get("simplified_summary")),
        "has_action_plan": len(result.get("action_plan", [])) > 0,
        "has_danger_signs": len(result.get("danger_signs", [])) > 0,
        "has_medications": len(result.get("medication_list", [])) > 0,
        "has_follow_up": len(result.get("follow_up_schedule", [])) > 0,
        "has_citations": len(result.get("citations", [])) > 0
    }
