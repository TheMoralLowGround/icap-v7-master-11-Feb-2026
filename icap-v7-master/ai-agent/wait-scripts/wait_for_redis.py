import redis
import time
import os


REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

print('Waiting for redis...')
sleep_time = 5

redis_up = False
while redis_up is False:
    try:
        redis_instance = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            client_name='utility_wait'
        )
        redis_instance.get('TEST')
        redis_up = True
    except:
        print(f'redis unavailable, waiting {sleep_time} second...')
        time.sleep(sleep_time)

print('redis available!')
