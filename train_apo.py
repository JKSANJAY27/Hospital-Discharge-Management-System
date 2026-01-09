"""
APO Training Script for Hospital Discharge Management System

This script trains the discharge simplification agents using Agent Lightning's
Automatic Prompt Optimization (APO) algorithm.

Usage:
    # Full training
    python train_apo.py
    
    # Dry run (test without full optimization)
    python train_apo.py --dry-run
    
    # Custom settings
    python train_apo.py --beam-rounds 2 --n-runners 2
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# CRITICAL: Install Unix stub modules for Windows compatibility BEFORE importing agentlightning
if sys.platform == 'win32':
    print("🔧 Setting up Windows compatibility stubs...")
    
    # Install fcntl stub
    try:
        import fcntl
    except ImportError:
        from src import fcntl_stub
        sys.modules['fcntl'] = fcntl_stub
        print("   ✓ fcntl stub installed")
    
    # Install pwd stub
    try:
        import pwd
    except ImportError:
        from src import pwd_stub
        sys.modules['pwd'] = pwd_stub
        print("   ✓ pwd stub installed")
    
    # Install grp stub
    try:
        import grp
    except ImportError:
        from src import grp_stub
        sys.modules['grp'] = grp_stub
        print("   ✓ grp stub installed")
    
    print("✓ Windows compatibility stubs ready")

from dotenv import load_dotenv
load_dotenv()

import agentlightning as agl

from src.agent_lightning.config import (
    AgentLightningConfig,
    create_apo_algorithm,
    create_trainer,
)
from src.agent_lightning.prompt_templates import (
    DISCHARGE_SIMPLIFIER_PROMPT,
    PATIENT_EDUCATION_PROMPT,
)
from src.agent_lightning.rollouts import (
    discharge_simplifier_rollout,
    patient_education_rollout,
    discharge_workflow_rollout,
)
from src.agent_lightning.datasets import (
    load_discharge_dataset,
    load_education_dataset,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train discharge agents using APO"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (use Baseline algorithm for testing)"
    )
    
    parser.add_argument(
        "--agent",
        type=str,
        default="discharge",
        choices=["discharge", "education", "workflow"],
        help="Which agent to train (default: discharge)"
    )
    
    parser.add_argument(
        "--beam-rounds",
        type=int,
        default=3,
        help="Number of APO beam search rounds (default: 3)"
    )
    
    parser.add_argument(
        "--beam-width",
        type=int,
        default=4,
        help="Beam width for APO (default: 4)"
    )
    
    parser.add_argument(
        "--n-runners",
        type=int,
        default=4,
        help="Number of parallel runners (default: 4)"
    )
    
    parser.add_argument(
        "--val-batch-size",
        type=int,
        default=10,
        help="Validation batch size (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="trained_prompts",
        help="Directory to save optimized prompts"
    )
    
    return parser.parse_args()


def save_prompt(prompt: agl.PromptTemplate, output_path: Path, agent_name: str):
    """Save optimized prompt to file."""
    output_path.mkdir(parents=True, exist_ok=True)
    
    prompt_file = output_path / f"{agent_name}_optimized_prompt.txt"
    prompt_file.write_text(prompt.template, encoding="utf-8")
    
    print(f"\n✅ Saved optimized prompt to: {prompt_file}")


def main():
    """Main training function."""
    args = parse_args()
    
    print("=" * 80)
    print("AGENT LIGHTNING - APO TRAINING")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN' if args.dry_run else 'FULL TRAINING'}")
    print(f"Agent: {args.agent}")
    print(f"Beam Rounds: {args.beam_rounds}")
    print(f"N Runners: {args.n_runners}")
    print()
    
    # Verify API key
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("   Set OPENAI_API_KEY or OPENAI_API_KEY_1 in .env file")
        sys.exit(1)
    print("✓ OpenAI API key found")
    
    # Create configuration
    config = AgentLightningConfig(
        beam_rounds=args.beam_rounds,
        beam_width=args.beam_width,
        n_runners=args.n_runners,
        val_batch_size=args.val_batch_size,
    )
    
    # Select agent and resources
    if args.agent == "discharge":
        rollout_fn = discharge_simplifier_rollout
        initial_prompt = DISCHARGE_SIMPLIFIER_PROMPT
        train_data, val_data = load_discharge_dataset()
        print(f"✓ Loaded {len(train_data)} train / {len(val_data)} val discharge samples")
        
    elif args.agent == "education":
        rollout_fn = patient_education_rollout
        initial_prompt = PATIENT_EDUCATION_PROMPT
        train_data, val_data = load_education_dataset()
        print(f"✓ Loaded {len(train_data)} train / {len(val_data)} val education samples")
        
    elif args.agent == "workflow":
        rollout_fn = discharge_workflow_rollout
        initial_prompt = DISCHARGE_SIMPLIFIER_PROMPT
        train_data, val_data = load_discharge_dataset()
        print(f"✓ Loaded {len(train_data)} train / {len(val_data)} val workflow samples")
    
    # Create algorithm
    if args.dry_run:
        print("\n🔧 Using Baseline algorithm (dry run mode)")
        algorithm = agl.Baseline(n_epochs=1, span_verbosity="keys")
    else:
        print("\n🔧 Creating APO algorithm...")
        algorithm = create_apo_algorithm(config)
    
    # Create trainer
    print("🔧 Creating trainer...")
    initial_resources = {"prompt_template": initial_prompt}
    trainer = create_trainer(config, algorithm, initial_resources)
    
    # Run training
    print("\n" + "=" * 80)
    print("STARTING TRAINING")
    print("=" * 80 + "\n")
    
    if args.dry_run:
        # Use dev mode for dry run
        trainer.dev(rollout_fn, train_data)
    else:
        # Full training with APO
        trainer.fit(
            agent=rollout_fn,
            train_dataset=train_data,
            val_dataset=val_data
        )
        
        # Save best prompt
        try:
            best_prompt = algorithm.get_best_prompt()
            output_path = Path(args.output_dir)
            save_prompt(best_prompt, output_path, args.agent)
        except ValueError as e:
            print(f"\n⚠️ Could not retrieve best prompt: {e}")
    
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
