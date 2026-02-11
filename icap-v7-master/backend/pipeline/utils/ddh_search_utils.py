import os
import redis
import requests
from datetime import datetime, timezone
from django.conf import settings

DDH_BASE_URL = os.getenv("DDH_BASE_URL")
DDH_USERNAME = os.getenv("DDH_USERNAME")
DDH_PASSWORD = os.getenv("DDH_PASSWORD")


redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="backend"
)


def get_ddh_token():
    """Fetch token from Redis or request new one"""
    token = redis_instance.get("ddh_token")
    expiry = redis_instance.get("ddh_token_expiry")

    if token and expiry:
        now = datetime.now(timezone.utc)
        expiry_str = expiry.decode("utf-8")
        expiry_time = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))

        if now < expiry_time:
            token = token.decode("utf-8")
            return token

    auth_payload = {
        "username": DDH_USERNAME,
        "password": DDH_PASSWORD
    }
    auth_url = f"{DDH_BASE_URL}/api/access_control/login/"

    response = requests.post(auth_url, data=auth_payload)
    if response.status_code != 200:
        raise Exception(f"DDH API Authentication failed.")

    data = response.json()
    token = data.get("token")
    expiry = data.get("expiry")

    if not token:
        raise Exception("Invalid response from DDH API.")

    redis_instance.set("ddh_token", token)
    redis_instance.set("ddh_token_expiry", expiry)

    return token