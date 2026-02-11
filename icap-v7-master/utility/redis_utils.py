import redis
import json
import os
import pickle


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



def get_port_json_from_redis(key):
    if not redis_instance.exists(key):
        print(f"key {key} does not exist in Redis.")
        return None
    json_data = redis_instance.get(key)
    try:
        data = pickle.loads(json_data)
    except Exception as e:
        data = json.loads(json_data)
        
    return data


def upload_port_json_file_to_redis(key, port_data):
    if redis_instance.exists(key):
        return
    else:
        serialize_data = json.dumps(port_data)
        redis_instance.set(key, serialize_data)
        print(f"Json file with key '{key}' uploaded to Redis.")

def get_redis_keys(pattern='*'):
    return redis_instance.keys(pattern)


def update_port_dict_cache(master_dictionaries):
    for key, value in master_dictionaries.items():
        if key.startswith("airport_dict_part") or key.startswith("seaport_dict_part"):
            # data = json.loads(value['data'])
            data = json.dumps(value['data'])
            redis_instance.set(value['name'], data)
            print("redis cache updated for key:", value['name'])