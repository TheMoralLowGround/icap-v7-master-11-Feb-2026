"""
Organization: AIDocbuilder Inc.
File: disable_inactive_users.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2024-12-04
 
Description:
    This script helps to disable inactive users after 120 days of inactivity.
 
Dependencies:
    - os, django
    - timezone from django.utils
    - timedelta from datetime
    - get_user_model from django.contrib.auth
 
Main Features:
    - Disbale inactive user from database.
"""
import os
import django
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

django.setup()

# ANSI escape code for colored text
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


def main_process():
    """Disable inactive users after 120 days of inactivity."""
    User = get_user_model()
    threshold_date = timezone.now() - timedelta(days=120)
    inactive_users = User.objects.filter(last_login__lt=threshold_date, is_active=True)

    count = inactive_users.update(is_active=False)

    if count:
        print(
            GREEN + f"Successfully disabled {count} user(s) due to inactivity." + RESET
        )
    else:
        print(RED + "No inactive users were found to be disabled." + RESET)


if __name__ == "__main__":
    main_process()
