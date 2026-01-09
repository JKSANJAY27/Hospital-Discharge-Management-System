"""
Agent Rollout Wrappers for Agent Lightning

These functions wrap the existing healthcare chains with @rollout decorators,
enabling them to be trained using APO (Automatic Prompt Optimization) and
other Agent Lightning algorithms.

Each rollout:
1. Receives a task (input data) and optimizable resources (prompt templates)
2. Executes the agent logic using the provided prompt
3. Returns a reward score for training
"""

import agentlightning as agl
from openai import OpenAI
import os
import json
import re
from typing import Dict, Any, TypedDict, Optional

from .graders import (
    grade_discharge_simplification,
    grade_patient_education,
    grade_safety_check,
)


# =============================================================================
# Task Type Definitions
# =============================================================================

class DischargeTask(TypedDict):
    """Task definition for discharge simplification."""
    document_text: str
    expected_output: Optional[Dict[str, Any]]  # Ground truth for evaluation


class EducationTask(TypedDict):
    """Task definition for patient education."""
    context: str  # Patient condition or procedure
    expected_queries: Optional[list]  # Expected search queries


class SafetyTask(TypedDict):
    """Task definition for safety check."""
    text: str  # Text to check
    expected_is_safe: Optional[bool]  # Ground truth


# =============================================================================
# Discharge Simplifier Rollout
# =============================================================================

@agl.rollout
def discharge_simplifier_rollout(
    task: DischargeTask,
    prompt_template: agl.PromptTemplate
) -> float:
    """
    Rollout for DischargeSimplifierChain.
    
    This is the PRIMARY agent in the system. It transforms complex medical
    discharge summaries into plain language instructions.
    
    Args:
        task: DischargeTask with document_text and optional expected_output
        prompt_template: Optimizable prompt template from APO
        
    Returns:
        float: Reward score [0, 1] based on readability, completeness, safety
    """
    # Get OpenAI client
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Format prompt with task data
    prompt = prompt_template.format(input_text=task["document_text"])
    
    # Call LLM with structured output request
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You must respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        result["status"] = "success"
        
    except Exception as e:
        print(f"Rollout error: {e}")
        result = {"status": "failed", "error": str(e)}
    
    # Calculate reward
    reward = grade_discharge_simplification(result, task.get("expected_output"))
    
    # Emit detailed reward for tracing
    agl.emit_reward(reward, attributes={
        "agent": "discharge_simplifier",
        "readability_target": "6-8",
    })
    
    return reward


# =============================================================================
# Patient Education Rollout
# =============================================================================

@agl.rollout
def patient_education_rollout(
    task: EducationTask,
    prompt_template: agl.PromptTemplate
) -> float:
    """
    Rollout for PatientEducationChain.
    
    Generates video search queries and recovery tips for patient education.
    
    Args:
        task: EducationTask with context (patient condition)
        prompt_template: Optimizable prompt template
        
    Returns:
        float: Reward score based on query quality and tip relevance
    """
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Format prompt
    prompt = prompt_template.format(context=task["context"])
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
    except Exception as e:
        print(f"Education rollout error: {e}")
        result = {"search_queries": [], "recovery_tips": []}
    
    # Calculate reward
    reward = grade_patient_education(result, task["context"])
    
    agl.emit_reward(reward, attributes={"agent": "patient_education"})
    
    return reward


# =============================================================================
# Safety Check Rollout
# =============================================================================

@agl.rollout
def safety_check_rollout(
    task: SafetyTask,
    prompt_template: agl.PromptTemplate
) -> float:
    """
    Rollout for SafetyGuardrailChain.
    
    Checks input text for PII and harmful content.
    
    Args:
        task: SafetyTask with text to check
        prompt_template: Optimizable prompt template
        
    Returns:
        float: Reward score based on classification accuracy
    """
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Format prompt
    prompt = prompt_template.format(input=task["text"])
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a safety checker. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
    except Exception as e:
        print(f"Safety rollout error: {e}")
        result = {"is_safe": True, "reason": f"Error: {e}"}
    
    # Calculate reward
    reward = grade_safety_check(
        result,
        expected_is_safe=task.get("expected_is_safe"),
        text=task["text"]
    )
    
    agl.emit_reward(reward, attributes={"agent": "safety_guardrail"})
    
    return reward


# =============================================================================
# Combined Workflow Rollout (Advanced)
# =============================================================================

@agl.rollout
def discharge_workflow_rollout(
    task: DischargeTask,
    prompt_template: agl.PromptTemplate,
    rollout: agl.Rollout = None
) -> float:
    """
    Full workflow rollout that runs safety check + discharge simplification.
    
    This demonstrates a multi-step agent with intermediate rewards.
    
    Args:
        task: DischargeTask with document_text
        prompt_template: Main discharge simplifier prompt
        rollout: Rollout context (optional, for accessing mode)
        
    Returns:
        float: Combined reward from all steps
    """
    from .prompt_templates import SAFETY_GUARDRAIL_PROMPT
    
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Step 1: Safety Check (using fixed prompt - not optimized here)
    with agl.operation(name="safety_check") as op:
        safety_prompt = SAFETY_GUARDRAIL_PROMPT.format(input=task["document_text"])
        
        try:
            safety_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": safety_prompt}],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            safety_result = json.loads(safety_response.choices[0].message.content)
        except:
            safety_result = {"is_safe": True, "reason": "Parse error"}
        
        op.set_output(safety_result)
        
        # Emit intermediate reward
        safety_reward = grade_safety_check(safety_result, text=task["document_text"])
        agl.emit_reward(safety_reward * 0.2, attributes={"step": "safety_check"})
    
    # Step 2: Discharge Simplification (if safe)
    if not safety_result.get("is_safe", True):
        agl.emit_message("Document blocked by safety check")
        return 0.1  # Minimal reward for correct rejection
    
    with agl.operation(name="discharge_simplification") as op:
        prompt = prompt_template.format(input_text=task["document_text"])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            result["status"] = "success"
        except Exception as e:
            result = {"status": "failed", "error": str(e)}
        
        op.set_output(result)
    
    # Calculate final reward
    main_reward = grade_discharge_simplification(result, task.get("expected_output"))
    
    # Combine rewards: 20% safety, 80% main task
    final_reward = (safety_reward * 0.2) + (main_reward * 0.8)
    
    agl.emit_reward(final_reward, attributes={
        "step": "final",
        "safety_reward": safety_reward,
        "main_reward": main_reward,
    })
    
    return final_reward
