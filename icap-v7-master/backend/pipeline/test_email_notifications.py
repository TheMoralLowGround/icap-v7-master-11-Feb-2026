"""
Organization: AIDocbuilder Inc.
File: pipeline/test_email_notifications.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This script helps to test email notifications.

Dependencies:
    - send_email_notification from utils.email_utils
    - Profile from dashboard.models
    - EmailBatch from core.models

Main Features:
    - Test email notification.
"""
from utils.email_utils import send_email_notification
from dashboard.models import Profile
from core.models import EmailBatch


profile = Profile.objects.get(id=54)
email = EmailBatch.objects.get(id="20231006.00002")
send_email_notification("success", "transaction_successful", profile, email, {})
