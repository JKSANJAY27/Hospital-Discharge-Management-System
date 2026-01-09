"""
Windows-Compatible APO Training Script for Hospital Discharge Management System

This script provides a Windows-compatible training approach that works without
Agent Lightning's full server infrastructure (which requires Unix-only modules).

It uses OpenAI's API directly to implement a simplified version of Automatic 
Prompt Optimization (APO) that runs entirely on Windows.

Usage:
    # Run optimization
    python train_apo_windows.py
    
    # Specify agent and rounds
    python train_apo_windows.py --agent discharge --rounds 3
    
    # Dry run (single iteration)
    python train_apo_windows.py --dry-run
"""

import asyncio
import argparse
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# Import our graders and datasets (these work on Windows)
from src.agent_lightning.graders import (
    grade_discharge_simplification,
    grade_patient_education,
    grade_safety_check,
)
from src.agent_lightning.datasets import (
    load_discharge_dataset,
    load_education_dataset,
)


# =============================================================================
# Prompt Templates (copied from prompt_templates.py to avoid agentlightning import)
# =============================================================================

DISCHARGE_SIMPLIFIER_TEMPLATE = """You are an expert Medical Discharge Instruction Simplifier. 
Your goal is to transform complex clinical discharge notes into a clear, safe, and actionable guide for the patient.

**INPUT DATA:**
- Use the provided discharge note text.
- Incorporate general medical knowledge from public care instructions (CDC/MedlinePlus equivalent).

**OUTPUT REQUIREMENTS (Strict JSON Schema):**

1. **simplified_summary** (REQUIRED):
   - Write a plain-language summary at 6th-8th grade reading level
   - Avoid medical jargon - use simple words
   - Explain WHY they were admitted and WHAT happened

2. **action_plan** (REQUIRED):
   - Break down by specific timeframes: "Day 1 (Today)", "Day 2", "Week 1", etc.
   - Each day should have tasks and medications

3. **danger_signs** (REQUIRED):
   - List immediate "Red Flags" that require calling doctor/911
   - Be specific (e.g., "Fever over 101°F", "Chest pain")

4. **medication_list** (REQUIRED):
   - Format: "Name - Purpose - Usage"

5. **follow_up_schedule** (REQUIRED):
   - Who to see, when, and why

6. **lifestyle_changes** (REQUIRED):
   - Diet modifications, exercise, smoking cessation, etc.

7. **citations** (REQUIRED):
   - Links to trusted public sources

**TONE:** Empathetic, clear, directive. Use "you" language.
**READABILITY:** Target 6th-8th grade level. Short sentences. Active voice.

Here are the discharge instructions:

{input_text}"""


@dataclass
class APOConfig:
    """Configuration for Windows APO training."""
    optimization_rounds: int = 3
    samples_per_round: int = 3
    temperature_gradient: float = 0.7  # For generating prompt improvements
    temperature_apply: float = 0.3     # For applying changes
    model: str = "gpt-4o-mini"


def run_agent(client: OpenAI, prompt_template: str, input_text: str) -> Dict[str, Any]:
    """Run the agent with a given prompt template."""
    prompt = prompt_template.replace("{input_text}", input_text)
    
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
        result = json.loads(response.choices[0].message.content)
        result["status"] = "success"
        return result
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def evaluate_prompt(client: OpenAI, prompt_template: str, 
                    samples: List[Dict], grader_fn) -> Tuple[float, List[Dict]]:
    """Evaluate a prompt template on samples."""
    results = []
    total_reward = 0.0
    
    for sample in samples:
        input_text = sample.get("document_text") or sample.get("context") or sample.get("text", "")
        output = run_agent(client, prompt_template, input_text)
        reward = grader_fn(output)
        
        results.append({
            "input": input_text[:100] + "...",
            "reward": reward,
            "output_status": output.get("status")
        })
        total_reward += reward
    
    avg_reward = total_reward / len(samples) if samples else 0
    return avg_reward, results


def generate_gradient(client: OpenAI, prompt: str, samples: List[Dict], 
                      results: List[Dict], config: APOConfig) -> str:
    """Generate a textual gradient for prompt improvement."""
    
    gradient_prompt = f"""You are an expert at optimizing prompts for medical AI systems.

CURRENT PROMPT:
{prompt}

EVALUATION RESULTS:
{json.dumps(results, indent=2)}

The average reward score is {sum(r['reward'] for r in results) / len(results):.3f} (target: 0.8+)

SCORING CRITERIA:
- Readability (0-0.3): Output should be at 6th-8th grade reading level
- Completeness (0-0.4): All required fields present and detailed
- Safety (0-0.3): Danger signs should be specific and comprehensive

TASK:
Analyze why the current prompt may not be achieving top scores. Provide:
1. Specific weaknesses in the current prompt
2. Concrete suggestions for improvement
3. Focus on areas with lowest scores

Be specific and actionable. Your analysis will be used to improve the prompt."""

    response = client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": gradient_prompt}],
        temperature=config.temperature_gradient,
        max_tokens=1000
    )
    
    return response.choices[0].message.content


def apply_gradient(client: OpenAI, prompt: str, gradient: str, 
                   config: APOConfig) -> str:
    """Apply the textual gradient to improve the prompt."""
    
    apply_prompt = f"""You are an expert at rewriting prompts for medical AI systems.

CURRENT PROMPT:
{prompt}

IMPROVEMENT SUGGESTIONS:
{gradient}

TASK:
Rewrite the prompt incorporating the suggested improvements. 
Keep the same overall structure and required outputs.
Make specific, targeted changes based on the feedback.

Output ONLY the improved prompt, nothing else."""

    response = client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": apply_prompt}],
        temperature=config.temperature_apply,
        max_tokens=3000
    )
    
    return response.choices[0].message.content


def train_apo_windows(agent_type: str, config: APOConfig, dry_run: bool = False):
    """Main APO training loop for Windows."""
    
    print("=" * 80)
    print("WINDOWS-COMPATIBLE APO TRAINING")
    print("=" * 80)
    print(f"\nAgent: {agent_type}")
    print(f"Optimization Rounds: {config.optimization_rounds}")
    print(f"Samples per Round: {config.samples_per_round}")
    print()
    
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized")
    
    # Load data and select grader
    if agent_type == "discharge":
        train_data, val_data = load_discharge_dataset()
        grader_fn = grade_discharge_simplification
        current_prompt = DISCHARGE_SIMPLIFIER_TEMPLATE
    else:
        print(f"❌ Agent type '{agent_type}' not yet supported")
        return
    
    print(f"✓ Loaded {len(train_data)} training samples")
    
    if dry_run:
        config.optimization_rounds = 1
        config.samples_per_round = 2
        print("🔧 DRY RUN: Using 1 round with 2 samples")
    
    # Training loop
    best_prompt = current_prompt
    best_reward = 0.0
    
    for round_num in range(config.optimization_rounds):
        print(f"\n{'=' * 60}")
        print(f"ROUND {round_num + 1}/{config.optimization_rounds}")
        print("=" * 60)
        
        # Select samples for this round
        samples = train_data[:config.samples_per_round]
        
        # Evaluate current prompt
        print("\n📊 Evaluating current prompt...")
        avg_reward, results = evaluate_prompt(client, current_prompt, samples, grader_fn)
        print(f"   Average reward: {avg_reward:.3f}")
        
        for i, r in enumerate(results):
            print(f"   Sample {i+1}: reward={r['reward']:.3f} status={r['output_status']}")
        
        if avg_reward > best_reward:
            best_reward = avg_reward
            best_prompt = current_prompt
            print(f"   🏆 New best reward: {best_reward:.3f}")
        
        # Generate improvement gradient
        print("\n🔍 Generating improvement suggestions...")
        gradient = generate_gradient(client, current_prompt, samples, results, config)
        print(f"   Gradient length: {len(gradient)} chars")
        
        # Apply gradient to get improved prompt
        print("\n✏️ Applying improvements...")
        improved_prompt = apply_gradient(client, current_prompt, gradient, config)
        
        # Evaluate improved prompt
        print("\n📊 Evaluating improved prompt...")
        new_reward, new_results = evaluate_prompt(client, improved_prompt, samples, grader_fn)
        print(f"   New average reward: {new_reward:.3f}")
        
        if new_reward > avg_reward:
            print(f"   ✅ Improvement: {new_reward - avg_reward:.3f}")
            current_prompt = improved_prompt
        else:
            print(f"   ⚠️ No improvement, keeping current prompt")
    
    # Save best prompt
    output_dir = Path("trained_prompts")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{agent_type}_optimized_prompt.txt"
    output_file.write_text(best_prompt, encoding="utf-8")
    
    print(f"\n{'=' * 80}")
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"\n✅ Best reward achieved: {best_reward:.3f}")
    print(f"✅ Optimized prompt saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Windows-compatible APO training")
    parser.add_argument("--agent", type=str, default="discharge",
                        choices=["discharge", "education"],
                        help="Agent to train")
    parser.add_argument("--rounds", type=int, default=3,
                        help="Number of optimization rounds")
    parser.add_argument("--samples", type=int, default=3,
                        help="Samples per round")
    parser.add_argument("--dry-run", action="store_true",
                        help="Quick test run")
    
    args = parser.parse_args()
    
    config = APOConfig(
        optimization_rounds=args.rounds,
        samples_per_round=args.samples
    )
    
    train_apo_windows(args.agent, config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
