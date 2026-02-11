"""
Organization: AIDocbuilder Inc.
File: redis_utils.py
Version: 6.0
 
Authors:
    - Vinay - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2023-11-08
 
Description:
    This script has functions to interacting with a Redis instance.
 
Dependencies:
    - os, json, redis
 
Main Features:
    - Retrieve data from redis and decode it into a dictionary.
    - Update specific keys in redis stored JSON data and save the updated structure.
"""
import json
import os

import redis

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

# Connect to our Redis instance
redis_instance = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=0, client_name="docbuilder"
)


def get_redis_data(job_id):
    """Retvie information from redis"""
    data = redis_instance.get(job_id)
    data = json.loads(data)
    return data


def set_redis_data(job_id, key_name, result_data):
    """Set partial information in redis for given key"""
    data = redis_instance.get(job_id)
    data = json.loads(data)
    data[key_name] = result_data
    data = json.dumps(data)
    redis_instance.set(job_id, data)
