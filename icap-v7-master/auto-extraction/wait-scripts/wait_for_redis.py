import redis
import time
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Config

print('Waiting for redis...')
sleep_time = 5

redis_up = False
while redis_up is False:
    try:
        redis_instance = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            client_name='extraction_wait'
        )
        redis_instance.get('TEST')
        redis_up = True
    except:
        print(f'redis unavailable, waiting {sleep_time} second...')
        time.sleep(sleep_time)

print('redis available!')
