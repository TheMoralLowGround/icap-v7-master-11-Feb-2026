"""
Organization: AIDocbuilder Inc.
File: wait_for_redis.py
Version: 6.0
 
Authors:
    - Vinay - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2023-11-08
 
Description:
    This script ensures that the Redis service is available before proceeding.
 
Dependencies:
    - os, time, redis
 
Main Features:
    - Continue execution only when the Redis server is available.
"""
import os
import time

import redis

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

print("Waiting for redis...")
sleep_time = 5

redis_up = False
while redis_up is False:
    try:
        redis_instance = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=0, client_name="docbuilder_wait"
        )
        redis_instance.get("TEST")
        redis_up = True
    except:
        print(f"redis unavailable, waiting {sleep_time} second...")
        time.sleep(sleep_time)

print("redis available!")
