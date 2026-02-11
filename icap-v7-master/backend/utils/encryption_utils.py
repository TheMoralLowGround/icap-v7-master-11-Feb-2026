import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet():
    key_bytes = hashlib.sha256(settings.FERNET_SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

def encrypt_value(value):
    if not value:
        return value
    return get_fernet().encrypt(value.encode()).decode()

def decrypt_value(value):
    if not value:
        return value
    return get_fernet().decrypt(value.encode()).decode()
