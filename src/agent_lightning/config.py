"""
Agent Lightning Configuration

Provides configuration dataclass and initialization utilities for Agent Lightning
training infrastructure.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
import os


@dataclass
class AgentLightningConfig:
    """
    Configuration for Agent Lightning training.
    
    This class centralizes all the hyperparameters and settings needed
    for training healthcare agents using APO or RL algorithms.
    """
    
    # APO Algorithm Configuration
    gradient_model: str = "gpt-4o-mini"  # Model for computing textual gradients
    apply_edit_model: str = "gpt-4o-mini"  # Model for applying edits
    
    beam_width: int = 4  # Number of top prompts to keep per round
    branch_factor: int = 4  # New candidates per parent prompt
    beam_rounds: int = 3  # Number of optimization rounds
    
    gradient_batch_size: int = 4  # Samples for gradient computation
    val_batch_size: int = 10  # Validation samples per evaluation
    
    rollout_batch_timeout: float = 600.0  # Timeout for batch completion (seconds)
    
    # Training Configuration  
    n_runners: int = 4  # Parallel rollout workers
    n_epochs: int = 1  # Dataset passes
    
    # Store Configuration
    store_type: Literal["memory", "mongo"] = "memory"
    mongo_uri: Optional[str] = None
    
    # Tracer Configuration
    tracer_type: Literal["agentops", "otel"] = "agentops"
    
    # LLM Proxy Configuration (for VERL/RL algorithms)
    llm_proxy_port: int = 4747
    
    # Logging
    log_level: str = "INFO"
    
    # Resource naming
    prompt_resource_key: str = "prompt_template"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.store_type == "mongo" and not self.mongo_uri:
            # Try to get from environment
            self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0")
        
        if self.beam_width < 1:
            raise ValueError("beam_width must be at least 1")
        if self.branch_factor < 1:
            raise ValueError("branch_factor must be at least 1")
        if self.n_runners < 1:
            raise ValueError("n_runners must be at least 1")


def get_openai_client():
    """
    Get AsyncOpenAI client for APO algorithm.
    
    Returns:
        AsyncOpenAI client configured from environment.
    """
    from openai import AsyncOpenAI
    
    api_key = os.getenv("OPENAI_API_KEY_1") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in environment.")
    
    return AsyncOpenAI(api_key=api_key)


def create_apo_algorithm(config: AgentLightningConfig):
    """
    Create an APO algorithm instance with the given configuration.
    
    Args:
        config: AgentLightningConfig with APO hyperparameters
        
    Returns:
        agentlightning.APO instance
        
    Raises:
        ImportError: If agentlightning is not available (e.g., on Windows)
    """
    try:
        import agentlightning as agl
    except (ImportError, ModuleNotFoundError) as e:
        raise ImportError(
            f"Agent Lightning is not available: {e}\n"
            "On Windows, full Agent Lightning functionality may be limited due to gunicorn's Unix dependencies.\n"
            "Consider using WSL or a Linux environment for training."
        )
    
    client = get_openai_client()
    
    return agl.APO(
        client,
        gradient_model=config.gradient_model,
        apply_edit_model=config.apply_edit_model,
        beam_width=config.beam_width,
        branch_factor=config.branch_factor,
        beam_rounds=config.beam_rounds,
        gradient_batch_size=config.gradient_batch_size,
        val_batch_size=config.val_batch_size,
        rollout_batch_timeout=config.rollout_batch_timeout,
    )


def create_trainer(config: AgentLightningConfig, algorithm, initial_resources: Dict[str, Any]):
    """
    Create a Trainer instance with the given configuration.
    
    Args:
        config: AgentLightningConfig with trainer settings
        algorithm: Agent Lightning algorithm (APO, VERL, etc.)
        initial_resources: Dict of initial resources (prompt templates, etc.)
        
    Returns:
        agentlightning.Trainer instance
    """
    import agentlightning as agl
    
    # Select tracer
    if config.tracer_type == "agentops":
        tracer = agl.AgentOpsTracer()
    else:
        tracer = agl.OtelTracer()
    
    # Select store
    store = None
    if config.store_type == "mongo":
        from agentlightning.store.mongo import MongoLightningStore
        store = MongoLightningStore(mongo_uri=config.mongo_uri)
    
    trainer_kwargs = {
        "algorithm": algorithm,
        "n_runners": config.n_runners,
        "initial_resources": initial_resources,
        "adapter": agl.TraceToMessages(),
    }
    
    # Only add optional parameters if they're non-default
    if store is not None:
        trainer_kwargs["store"] = store
    
    return agl.Trainer(**trainer_kwargs)
