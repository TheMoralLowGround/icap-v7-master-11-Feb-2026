import os
import redis
import requests
from datetime import datetime, timezone
from django.conf import settings

ANNOTATION_BASE_URL = os.getenv("ANNOTATION_BASE_URL")
ANNOTATION_USERNAME = os.getenv("ANNOTATION_USERNAME")
ANNOTATION_PASSWORD = os.getenv("ANNOTATION_PASSWORD")


redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="backend"
)


def get_annotation_token():
    """Fetch token from Redis or request new one"""
    token = redis_instance.get("annotation_token")
    expiry = redis_instance.get("annotation_token_expiry")

    if token and expiry:
        now = datetime.now(timezone.utc)
        expiry_str = expiry.decode("utf-8")
        expiry_time = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))

        if now < expiry_time:
            token = token.decode("utf-8")
            return token

    auth_payload = {
        "username": ANNOTATION_USERNAME,
        "password": ANNOTATION_PASSWORD
    }
    auth_url = f"{ANNOTATION_BASE_URL}/api/access_control/login/"

    response = requests.post(auth_url, json=auth_payload)
    if response.status_code != 200:
        raise Exception(f"Annotation API Authentication failed.")

    data = response.json()
    token = data.get("token")
    expiry = data.get("expiry")

    if not token:
        raise Exception("Invalid response from Annotation API.")

    redis_instance.set("annotation_token", token)
    redis_instance.set("annotation_token_expiry", expiry)

    return token