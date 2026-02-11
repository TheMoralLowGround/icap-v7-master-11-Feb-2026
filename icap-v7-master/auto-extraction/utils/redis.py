"""
Redis utilities for auto-extraction service.

Provides centralized Redis connection and data operations.
"""

import json
import redis
from .config import Config


# Connect to Redis instance using centralized config
redis_instance = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    client_name='auto-extraction'
)


def get_redis_data(job_id):
    """Retrieve information from redis"""
    data = redis_instance.get(job_id)
    if data:
        return json.loads(data)
    return None


def set_redis_data(job_id, key_name, result_data):
    """Set partial information in redis for given key"""
    data = redis_instance.get(job_id)
    if data:
        data = json.loads(data)
    else:
        data = {}
    
    data[key_name] = result_data
    data = json.dumps(data)
    redis_instance.set(job_id, data)
