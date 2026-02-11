import json
import random
import string
import redis
from django.conf import settings


redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="input_channel"
)


def gerenate_job_id():
    # Generate unique job_id
    random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    job_id = f"input_channel:job:{random_string}"
    return job_id


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

