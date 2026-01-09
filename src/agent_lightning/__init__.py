"""
Agent Lightning Integration Module

This module provides integration with Microsoft's Agent Lightning framework
for training and optimizing the healthcare agents using Automatic Prompt
Optimization (APO) and Reinforcement Learning algorithms.

Components:
- config: Configuration for Agent Lightning training
- prompt_templates: Optimizable prompt templates as resources  
- rollouts: Agent rollout wrappers with @rollout decorator
- graders: Reward/grading functions for training
- datasets: Training and validation dataset loaders

Note: On Windows, full Agent Lightning functionality may be limited due to
gunicorn's dependency on Unix-specific modules (fcntl). The graders and
datasets modules work independently of Agent Lightning.
"""

# Import graders first - they work without Agent Lightning
from .graders import (
    grade_discharge_simplification,
    grade_patient_education,
    grade_safety_check,
)

# Import config without Agent Lightning dependency
from .config import AgentLightningConfig

# Try to import Agent Lightning-dependent modules
AGENT_LIGHTNING_AVAILABLE = False
IMPORT_ERROR = None

try:
    from .prompt_templates import (
        DISCHARGE_SIMPLIFIER_PROMPT,
        PATIENT_EDUCATION_PROMPT,
        SAFETY_GUARDRAIL_PROMPT,
    )
    from .rollouts import (
        discharge_simplifier_rollout,
        patient_education_rollout,
        safety_check_rollout,
    )
    AGENT_LIGHTNING_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    IMPORT_ERROR = str(e)
    # Define placeholders
    DISCHARGE_SIMPLIFIER_PROMPT = None
    PATIENT_EDUCATION_PROMPT = None
    SAFETY_GUARDRAIL_PROMPT = None
    discharge_simplifier_rollout = None
    patient_education_rollout = None
    safety_check_rollout = None

__all__ = [
    "AgentLightningConfig",
    "DISCHARGE_SIMPLIFIER_PROMPT",
    "PATIENT_EDUCATION_PROMPT", 
    "SAFETY_GUARDRAIL_PROMPT",
    "discharge_simplifier_rollout",
    "patient_education_rollout",
    "safety_check_rollout",
    "grade_discharge_simplification",
    "grade_patient_education",
    "grade_safety_check",
    "AGENT_LIGHTNING_AVAILABLE",
    "IMPORT_ERROR",
]
