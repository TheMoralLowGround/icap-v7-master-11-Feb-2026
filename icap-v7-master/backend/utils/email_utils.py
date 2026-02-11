"""
Organization: AIDocbuilder Inc.
File: utils/email_utils.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-11

Description:
    This file contain helper functions to send email notifications.

Dependencies:
    - traceback
    - settings from django.conf
    - EmailMultiAlternatives from django.core.mail
    - get_template from django.template.loader
    - EmailBatch, EmailParsedDocument from core.models
    - Profile from dashboard.models

Main Features:
    - Send Email based on profile settings.
    - Send success or failure notifications.
"""
import re
import os
import traceback
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

from core.models import EmailBatch, EmailParsedDocument
from dashboard.models import Profile

def load_comma_separated_list(input_string):
    """make list from string separated by comma"""
    items = input_string.split(",")
    items = [i.strip().lower() for i in items if i]
    return items


def is_valid_email(email):
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        if "icap" in email.lower():
            return False
        return True
    return False


def __send_email(
    subject, html_message, from_email, recipient_list, cc_list, attachment_path=[]
):
    """Sends email with the specified information"""
    msg = EmailMultiAlternatives(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=recipient_list,
        cc=cc_list,
    )
    [msg.attach_file(path) for path in attachment_path if attachment_path]
    msg.content_subtype = "html"
    msg.send(fail_silently=False)


def send_email_notification(
    notify_type, event_type, email_batch_id, context={}, send_attachment=False
):
    """
    Send Email notification based on profile settings.
    notify_type: "success" or "failure"

    Args:
        notify_type (str): Notification type either 'success' or 'failure'.
        event_type (str): HTML template for the email.
        email_batch_id (str): Object of EmailBatch.
        context (dict): Data to render in the email template.
        send_attachment (bool): Include attachments in the email or not.

    Returns:
        Send the email notification.

    Process Details:
        - Validate that email notifications are enabled in settings.
        - Validate the 'notify_type' argument.
        - Retrieve the 'EmailBatch' object using 'email_batch_id'.
        - Retrieve matched profile name.
        - Configure email metadata such as subject, recipients, CC list based on the profile.
        - Remove 'from_email' from the recipient if present.
        - Render the HTML email message using the specified template and context.
        - If 'send_attachment' is True, attach files related to the email batch and send the email.
        - Email sending functionality is working through function '__send_email'.

    Notes:
        - Attachments are fetched from 'EmailParsedDocument' objects.
        - Email sending functionality is working through function '__send_email'.
    """
    try:
        # Check if email sending is enabled
        if settings.SEND_EMAILS == 0:
            return

        # Input Validations
        assert (
            notify_type == "success" or notify_type == "failure"
        ), f"Invalid notify_type {notify_type}"

        email_batch = EmailBatch.objects.get(id=email_batch_id)
        # skip email notification for manual upload batches
        if email_batch.parsed_file_type != "email":
            return
        profile = email_batch.matched_profile_name
        profile_instance = Profile.objects.filter(name=profile)
        # profile_customer = None
        # if email_batch.object_id and email_batch.content_type:
        #     profile_customer = email_batch.customer

        from_email = settings.EMAIL_HOST_USER
        subject = email_batch.email_subject
        if notify_type == "success":
            confirmation_numbers = email_batch.confirmation_numbers
            shipment_id = ",".join(confirmation_numbers)
            subject = f"[SUCCESS] Confirmation Number: {shipment_id} | {subject}"
        elif notify_type == "failure":
            subject = f"[FAILED] {subject}"

        recipient_list = [email_batch.email_from]
        cc_list = []

        if profile_instance.exists():
            profile_instance = profile_instance.first()

            # notification_with_same_subject = profile_instance.__getattribute__(
            #     f"{notify_type}_notification_with_same_subject"
            # )
            # notification_subject = profile_instance.__getattribute__(
            #     f"{notify_type}_notification_subject"
            # )
            notify_email_sender = profile_instance.__getattribute__(
                f"{notify_type}_notify_email_sender"
            )
            notify_email_recipients = profile_instance.__getattribute__(
                f"{notify_type}_notify_email_recipients"
            )
            notify_additional_emails = profile_instance.__getattribute__(
                f"{notify_type}_notify_additional_emails"
            )
            notify_exclude_emails = profile_instance.__getattribute__(
                f"{notify_type}_notify_exclude_emails"
            )
            # notify_cc_users = profile_instance.__getattribute__(
            #     f"{notify_type}_notify_cc_users"
            # )

            # Derive Subject
            # if not notification_with_same_subject:
            #     subject = notification_subject

            if not (notify_email_sender or notify_email_recipients):
                return

            recipient_list = []
            if notify_email_sender:
                recipient_list.append(email_batch.email_from)

            if notify_email_recipients:
                to_emails = load_comma_separated_list(email_batch.email_to)
                recipient_list += to_emails

                cc_users = load_comma_separated_list(email_batch.email_cc)
                recipient_list += cc_users

            if notify_additional_emails:
                additional_emails = load_comma_separated_list(notify_additional_emails)
                cc_list += additional_emails

            if notify_exclude_emails:
                notify_exclude_emails = load_comma_separated_list(notify_exclude_emails)
                recipient_list = [i for i in recipient_list if i not in notify_exclude_emails]
                cc_list = [i for i in cc_list if i not in notify_exclude_emails]

            # if notify_cc_users:
            #     cc_users = load_comma_separated_list(email_batch.email_cc)
            #     cc_list += cc_users

            recipient_list = list(set(recipient_list))
            cc_list = list(set(cc_list))
        else:
            print("Process not found.")

        if from_email in recipient_list:
            recipient_list.remove(from_email)
        if from_email in cc_list:
            cc_list.remove(from_email)

        recipient_list = [i for i in recipient_list if is_valid_email(i)]
        cc_list = [i for i in cc_list if is_valid_email(i)]

        if not (recipient_list or cc_list):
            print("Recipient not found. Skipping email sending.")
            return

        template = get_template(f"{event_type}.html")
        context["transaction_id"] = email_batch_id
        html_message = template.render(context)
        if send_attachment == True:
            # email_batch = EmailBatch.objects.get(id=email_batch_id)
            # attachments = EmailParsedDocument.objects.filter(email=email_batch)
            # attachment_path = [i.path for i in attachments]
            batch_path = os.path.join(settings.BATCH_INPUT_PATH_DOCKER, "email-batches", email_batch_id)
            files = os.listdir(batch_path)
            files = [
                i for i in files if i.lower().endswith(".eml") or i.lower().endswith(".msg")
            ]
            attachment_path = [os.path.join(batch_path, i) for i in files]
            print(attachment_path)
            __send_email(
                subject,
                html_message,
                from_email,
                recipient_list,
                cc_list,
                attachment_path,
            )
        else:
            __send_email(subject, html_message, from_email, recipient_list, cc_list)

    except:
        print("Exception occured while sending email notification")
        traceback.print_exc()


def send_failure_notification(email_batch_id, error_message):
    """
    Wrapper function to send_email_notification for failure cases.
    """
    notify_type = "failure"
    event_type = "unexpected_error"
    context = {"error_message": error_message}
    send_email_notification(
        notify_type, event_type, email_batch_id, context, send_attachment=True
    )


def send_success_notification(email_batch_id, context):
    """
    Wrapper function to send_email_notification for success cases.
    """
    notify_type = "success"
    event_type = "transaction_successful"

    if context.get("multi_shipment_info"):
        event_type = "transaction_multi_shipment"

    send_email_notification(
        notify_type, event_type, email_batch_id, context, send_attachment=True
    )
