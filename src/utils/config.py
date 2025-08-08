"""Configuration management for the evaluation framework."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a specific LLM model."""
    provider: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 60


class EvaluationConfig(BaseModel):
    """Evaluation-specific configuration."""
    k_trials: List[int] = [1, 3, 5, 8, 10]
    max_turns: int = 10
    conversation_timeout: int = 300
    max_concurrent_evaluations: int = 5
    max_retries: int = 3
    retry_delay: float = 2.0


class DomainConfig(BaseModel):
    """Configuration for a specific evaluation domain."""
    api_base_url: str
    database_url: str
    policy_file: str
    scenarios_file: str
    max_order_value: Optional[int] = None


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    file: str = "logs/evaluation.log"
    rotation: str = "1 week"
    retention: str = "4 weeks"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    results_db: str = "sqlite:///results/evaluation_results.db"
    echo_sql: bool = False
    pool_size: int = 10


class OutputConfig(BaseModel):
    """Output configuration."""
    results_dir: str = "results"
    reports_dir: str = "results/reports"
    plots_dir: str = "results/plots"
    export_formats: List[str] = ["json", "csv", "html"]


class DebugConfig(BaseModel):
    """Debug/development configuration."""
    enabled: bool = False
    verbose_logging: bool = False
    save_conversations: bool = True
    mock_apis: bool = False


class Config(BaseSettings):
    """Main configuration class."""
    
    # API Keys
    api_keys: Dict[str, Optional[str]] = {}
    
    # Model configurations
    models: Dict[str, ModelConfig] = {}
    
    # Evaluation settings
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    
    # Domain configurations
    domains: Dict[str, DomainConfig] = {}
    
    # Logging
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Output
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Debug
    debug: DebugConfig = Field(default_factory=DebugConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file."""
    if config_path is None:
        # Try to find config file
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "config.yaml"
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    # Handle environment variable substitution
    config_data = _substitute_env_vars(config_data)
    
    # Parse model configurations
    if "models" in config_data:
        models = {}
        for name, model_data in config_data["models"].items():
            models[name] = ModelConfig(**model_data)
        config_data["models"] = models
    
    # Parse domain configurations  
    if "domains" in config_data:
        domains = {}
        for name, domain_data in config_data["domains"].items():
            domains[name] = DomainConfig(**domain_data)
        config_data["domains"] = domains
    
    return Config(**config_data)


def _substitute_env_vars(data: Any) -> Any:
    """Recursively substitute environment variables in configuration."""
    if isinstance(data, dict):
        return {k: _substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Handle ${VAR_NAME} format
        if data.startswith("${") and data.endswith("}"):
            var_name = data[2:-1]
            return os.getenv(var_name)
        return data
    else:
        return data


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config