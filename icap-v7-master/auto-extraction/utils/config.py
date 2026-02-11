"""
Configuration module for auto-extraction service.

Centralizes all environment variables and configuration settings.
"""

import os
from typing import Optional


class Config:
    """Configuration class for auto-extraction service."""
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USERNAME: str = os.getenv("RABBITMQ_USERNAME", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        required = [
            "REDIS_HOST",
            "RABBITMQ_HOST",
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


# Validate configuration on import
Config.validate()
