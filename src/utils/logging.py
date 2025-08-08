"""Logging utilities for the evaluation framework."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import get_config


def setup_logging(config_override: Optional[dict] = None) -> None:
    """Set up logging configuration."""
    config = get_config()
    log_config = config.logging
    
    if config_override:
        # Update with any overrides
        for key, value in config_override.items():
            setattr(log_config, key, value)
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        level=log_config.level,
        format=log_config.format,
        colorize=True,
    )
    
    # Add file logger
    log_file = Path(log_config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_config.file,
        level=log_config.level,
        format=log_config.format,
        rotation=log_config.rotation,
        retention=log_config.retention,
        compression="zip",
    )
    
    # Enable debug logging if configured
    if config.debug.verbose_logging:
        logger.add(
            "logs/debug.log",
            level="DEBUG",
            format=log_config.format,
            rotation="1 day",
            retention="1 week",
        )


def get_logger(name: str) -> "logger":
    """Get a logger instance with the specified name."""
    return logger.bind(name=name)


# Set up logging on module import
setup_logging()