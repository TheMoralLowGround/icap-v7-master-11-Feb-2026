import redis
import json
import os
import pickle


REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Connect to our Redis instance
redis_instance = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    client_name="postprocess",
)


def get_redis_data(job_id):
    """Retrieve information from redis"""
    data = redis_instance.get(job_id)
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    return json.loads(data)


def set_redis_data(job_id, key_name, result_data):
    """Set partial information in redis for given key"""
    data = redis_instance.get(job_id)
    if data is None:
        data = {}
    else:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        data = json.loads(data)
    data[key_name] = result_data
    data = json.dumps(data)
    redis_instance.set(job_id, data)
