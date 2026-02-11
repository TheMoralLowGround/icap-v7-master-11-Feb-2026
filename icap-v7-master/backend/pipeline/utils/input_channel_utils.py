import os
import requests
from datetime import datetime, timezone
from utils.redis_utils import redis_instance

INPUT_CHANNEL_BASE_URL = os.getenv("INPUT_CHANNEL_BASE_URL")
INPUT_CHANNEL_USERNAME = os.getenv("INPUT_CHANNEL_USERNAME")
INPUT_CHANNEL_PASSWORD = os.getenv("INPUT_CHANNEL_PASSWORD")


def get_input_channel_token():
    """Fetch token from Redis or request new one"""
    token = redis_instance.get("input_channel_token")
    expiry = redis_instance.get("input_channel_token_expiry")

    if token and expiry:
        now = datetime.now(timezone.utc)
        expiry_str = expiry.decode("utf-8")
        expiry_time = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))

        if now < expiry_time:
            token = token.decode("utf-8")
            return token

    auth_payload = {
        "username": INPUT_CHANNEL_USERNAME,
        "password": INPUT_CHANNEL_PASSWORD
    }
    auth_url = f"{INPUT_CHANNEL_BASE_URL}/api/access_control/login/"

    response = requests.post(auth_url, data=auth_payload)
    if response.status_code != 200:
        raise Exception(f"Input Channel Authentication failed.")

    data = response.json()
    token = data.get("token")
    expiry = data.get("expiry")

    if not token:
        raise Exception("Invalid response from input_channel API.")

    redis_instance.set("input_channel_token", token)
    redis_instance.set("input_channel_token_expiry", expiry)

    return token