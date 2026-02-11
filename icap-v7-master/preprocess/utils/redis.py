import redis
import json
import os


REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

# Connect to our Redis instance
redis_instance = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    client_name='utility'
)


def get_redis_data(job_id):
    """Retrieve information from redis"""
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