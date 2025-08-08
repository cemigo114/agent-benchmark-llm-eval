"""Factory for creating agent instances."""

from typing import Dict, Any

from ..utils.config import get_config, ModelConfig
from .base import BaseAgent
from .openai_agent import OpenAIAgent
from .anthropic_agent import AnthropicAgent


def create_agent(model_name: str, config_override: Dict[str, Any] = None) -> BaseAgent:
    """Create an agent instance based on the model configuration."""
    
    config = get_config()
    
    if model_name not in config.models:
        raise ValueError(f"Unknown model: {model_name}")
    
    model_config = config.models[model_name]
    
    # Apply any overrides
    if config_override:
        model_config = ModelConfig(
            **{**model_config.dict(), **config_override}
        )
    
    # Get API key for the provider
    api_key = config.api_keys.get(model_config.provider)
    if not api_key:
        raise ValueError(f"No API key configured for provider: {model_config.provider}")
    
    # Create the appropriate agent
    if model_config.provider == "openai":
        return OpenAIAgent(
            api_key=api_key,
            model_name=model_config.model_name,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature,
            timeout=model_config.timeout
        )
    elif model_config.provider == "anthropic":
        return AnthropicAgent(
            api_key=api_key,
            model_name=model_config.model_name,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature,
            timeout=model_config.timeout
        )
    else:
        raise ValueError(f"Unsupported provider: {model_config.provider}")


def list_available_models() -> Dict[str, ModelConfig]:
    """List all available models from configuration."""
    config = get_config()
    return config.models