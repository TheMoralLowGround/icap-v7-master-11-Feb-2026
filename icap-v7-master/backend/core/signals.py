"""
Organization: AIDocbuilder Inc.
File: core/signals.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Add feaures

Last Updated By: Nayem
Last Updated At: 2024-07-28

Description:
    This file defines signals for handling specific events in the application
    such as profile save, profile delete and email batch delete handling.

Dependencies:
    - from django.db.models.signals import post_save, pre_delete
    - receiver from django.dispatch
    - LDAPBackend, ldap_error, populate_user from django_auth_ldap.backend
    - ProfileDocument, Template, Profile from dashboard.models

Main Features:
    - Django Signal handler that assign user to Group and Market.
    - Django Signal handler to print LDAP exception.
"""
import json
from django.db.models.signals import pre_delete, post_save, post_delete
from django.dispatch import receiver
from django_auth_ldap.backend import LDAPBackend, ldap_error, populate_user

from core.models import Batch, EmailBatch, EmailToBatchLink, Definition
from dashboard.models import ProfileDocument, Template, Profile
from utils.utils import get_selected_dataset_batches_info

@receiver(post_delete, sender=Batch, dispatch_uid="batch_delete_handling")
def batch_delete_handling(sender, instance, **kwargs):
    """Called after a Batch instance is deleted."""
    selected_dataset_batches, selected_dataset_batches_path = get_selected_dataset_batches_info()

    selected_dataset_batches = [i for i in selected_dataset_batches if i != instance.id]

    with open(selected_dataset_batches_path, "w") as json_file:
        json.dump(selected_dataset_batches, json_file, indent=2)


@receiver(pre_delete, sender=EmailBatch, dispatch_uid="email_batch_delete_handling")
def email_batch_delete_handling(sender, instance, using, **kwargs):
    """Remove related batches upon deletion of Email Batch."""
    batches_to_delete = list(
        EmailToBatchLink.objects.filter(email__id=instance.id).values_list(
            "batch_id", flat=True
        )
    )
    Batch.objects.filter(id__in=batches_to_delete).delete()


@receiver(pre_delete, sender=Profile, dispatch_uid="profile_delete_handling")
def profile_delete_handling(sender, instance, using, **kwargs):
    """Remove templates upon deletion of Profile."""
    docs = ProfileDocument.objects.filter(profile=instance)
    for doc in docs:
        template = Template.objects.filter(template_name=doc.template)
        if template.exists():
            template = template.first()
            if instance.name not in template.linked_profiles:
                return
            template.linked_profiles.remove(instance.name)
            template.save()


# ###### LDAP SIGNALS ###########


@receiver(populate_user, sender=LDAPBackend)
def ldap_auth_handler(user, ldap_user, **kwargs):
    """
    Django Signal handler that assign user to Group and Market.

    This signal gets called after Django Auth LDAP Package have populated
    the user with its data, but before the user is saved to the database.
    """
    # Check all of the user's group names to see if they belong
    # in a group that match what we're looking for.

    for group_name in ldap_user.group_names:
        print(group_name)


@receiver(ldap_error, sender=LDAPBackend)
def ldap_error_handler(**kwargs):
    """
    Django Signal handler to print LDAP exception.

    like: Can not contact to server.
    If user credentials are wrong, It will not be considered as error.
    """
    print("LDAP ERROR:", kwargs)


@receiver(post_save, sender=Profile, dispatch_uid="profile_update_handling")
def profile_update_handling(sender, instance: Profile, **kwargs):
    """Update Definition based on Profile keys."""

    keys_labels = [i.get("keyValue") for i in instance.keys if i.get("type") != "table"]
    table_labels = [
        i.get("keyValue") for i in instance.keys if i.get("type") == "table"
    ]

    profile_definitions = Definition.objects.filter(definition_id=instance.name)

    for definition in profile_definitions:
        definition_data = definition.data
        try:
            for section_key, section_data in definition_data.items():
                # Filter key["items"]
                original_key_items = section_data.get("key", {}).get("items", [])
                filtered_key_items = [
                    item
                    for item in original_key_items
                    if item.get("keyLabel") in keys_labels
                ]
                section_data["key"]["items"] = filtered_key_items

                # Filter table_definition_data["keyItems"]
                for table in section_data.get("table", []):
                    table_def_data = table.get("table_definition_data", {})
                    original_table_keys = table_def_data.get("keyItems", [])
                    filtered_table_keys = [
                        item
                        for item in original_table_keys
                        if item.get("keyLabel") in table_labels
                    ]
                    table_def_data["keyItems"] = filtered_table_keys
                    original_table_columns = table_def_data.get("columns", [])
                    filtered_table_keys = [
                        item
                        for item in original_table_columns
                        if item.get("keyLabel") in table_labels
                    ]
                    table_def_data["columns"] = filtered_table_keys

        except Exception:
            pass

        definition.data = definition_data
        definition.save()
