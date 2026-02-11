"""
Utility functions for Auto Extraction Services.
"""
import os
import json
from typing import List


def get_cors_allowed_origins() -> List[str]:
    """Parse CORS_ALLOWED_ORIGINS environment variable.
    
    Supports both JSON array and comma-separated formats:
    - JSON: '["http://localhost:3000", "http://localhost:8000"]'
    - Comma: 'http://localhost:3000,http://localhost:8000'
    
    Returns:
        List of allowed origins, defaults to secure localhost origins.
    """
    default_origins = ["http://localhost:3000", "http://localhost:8000"]
    cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS")
    
    if not cors_origins_env:
        return default_origins
    
    # JSON array format: ["http://localhost:3000", "http://localhost:8000"]
    if cors_origins_env.startswith("["):
        try:
            return json.loads(cors_origins_env)
        except (json.JSONDecodeError, TypeError):
            return default_origins
    
    # Comma-separated format: http://localhost:3000,http://localhost:8000
    return [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
