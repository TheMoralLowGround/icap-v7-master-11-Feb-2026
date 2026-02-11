import redis
from django.conf import settings

redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="backend"
)