import os
import traceback
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
import json
from typing import Optional, Dict, Any, List, Tuple
from django.forms.models import model_to_dict

from dashboard import serializers

CHANGE_LOGS_PATH = settings.CHANGE_LOGS_DOCKER_PATH


PROFILE_ATTRIBUTES = {
    'GENERAL': [
            "name",
            "free_name",
            "country",
            # "mode_of_transport",
            "manual_validation",
            "multi_shipment",
            "send_time_stamp",
            "automatic_splitting",
            "ignore_dense_pages",
            "exceptional_excel",
            "email_domains",
            "email_from",
            "email_subject_match_option",
            "email_subject_match_text",
        ],
    'PROJECT': ["project"],
    'KEYS': ["keys"],
    'DOCUMENTS': ["documents"],
    'TRANSLATED_DOCUMENTS': ["translated_documents"],
    'PARTIES': ["customers"],
    'UNKNOWN': [],
    'MISCELLANEOUS': []
}

class ChangeLogger:
    
    @staticmethod
    def track_changes(new_data, old_data, instance, old_instance) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Track changes and return old and new values in separate dictionaries
        Returns: {'old_values': {...}, 'new_values': {...}} or None if no changes
        """
        if not old_data:
            return None

        old_values = {}
        new_values = {}
        has_changes = False

        # Get union of all field names from both old and new data
        all_field_names = set(new_data.keys()) | set(old_data.keys())

        IGNORE_TIMESTAMP_FIELDS = {'id','updated_at', 'created_at', 'last_modified', 'timestamp'}
        change_categories = set()

        for field_name in all_field_names:
            # Skip fields that shouldn't be tracked
            if field_name in ['id', 'process_id', 'created_at', 'updated_at', 'last_modified']:
                continue

            try:
                old_value = old_data.get(field_name, None)
                new_value = new_data.get(field_name, None)

                # Check if the value has changed
                if not ChangeLogger._values_equal_deep(old_value, new_value, IGNORE_TIMESTAMP_FIELDS):
                    # Store both old and new values in their original format
                    old_values[field_name] = ChangeLogger._prepare_value_for_storage(old_value)
                    new_values[field_name] = ChangeLogger._prepare_value_for_storage(new_value)
                    has_changes = True

                    if instance._meta.model_name.upper() == "PROFILE":
                        if field_name in PROFILE_ATTRIBUTES["GENERAL"]:
                            change_categories.add("GENERAL")
                        elif field_name in PROFILE_ATTRIBUTES["PROJECT"]:
                            change_categories.add("PROJECT")
                        elif field_name in PROFILE_ATTRIBUTES["KEYS"]:
                            change_categories.add("KEYS")
                        elif field_name in PROFILE_ATTRIBUTES["DOCUMENTS"]:
                            change_categories.add("DOCUMENTS")
                        elif field_name in PROFILE_ATTRIBUTES["TRANSLATED_DOCUMENTS"]:
                            change_categories.add("TRANSLATED_DOCUMENTS")
                        elif field_name in PROFILE_ATTRIBUTES["PARTIES"]:
                            change_categories.add("PARTIES")
                        else:
                            change_categories.add("UNKNOWN")

                    if instance._meta.model_name.upper() == "PROJECT":
                        change_categories.add("PROJECT")

            except (AttributeError, ValueError) as e:
                print(f"Error accessing field '{field_name}': {e}")
                # Skip fields that can't be accessed
                continue
        if has_changes:
            change_categories = list(change_categories)
            if not change_categories:
                change_categories.append("UNKNOWN")
            change_categories.sort()
            
            return {
                'old_values': old_values,
                'new_values': new_values,
                'change_category': ", ".join(change_categories)
            }
        return None

    @staticmethod
    def _prepare_value_for_storage(value) -> Any:
        """
        Prepare values for JSON storage while preserving their original types
        when possible, but converting complex objects to serializable formats
        """
        if value is None:
            return None

        # Handle model instances (convert to ID or string representation)
        if hasattr(value, 'pk'):
            return str(value.pk)  # Store the primary key

        # Handle dates and times (convert to ISO format)
        if hasattr(value, 'strftime'):
            return value.isoformat()

        # Handle Django model managers and querysets
        if hasattr(value, 'all'):  # Queryset-like objects
            try:
                # Try to get the count and first few items
                count = value.count()
                sample_items = list(value[:3].values_list('pk', flat=True))
                return {
                    '_type': 'queryset',
                    'count': count,
                    'sample_items': sample_items,
                    'representation': str(value)
                }
            except:
                return str(value)

        # Handle file fields and images
        if hasattr(value, 'url'):
            return {
                '_type': 'file',
                'name': str(value),
                'url': value.url if value else None
            }

        # For lists and dicts, ensure they're JSON serializable
        if isinstance(value, (list, dict)):
            # Recursively prepare nested values
            return ChangeLogger._make_json_serializable(value)

        # For other types, return as-is (strings, numbers, booleans will serialize fine)
        return value

    @staticmethod
    def _make_json_serializable(obj):
        """
        Recursively make an object JSON serializable
        """
        if isinstance(obj, dict):
            return {k: ChangeLogger._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ChangeLogger._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            # For other types, convert to string
            return str(obj)

    @staticmethod
    def _values_equal_deep(old_val, new_val, ignore_fields=None):
        """
        Optimized deep comparison with order-independent list handling
        """
        if ignore_fields is None:
            ignore_fields = {'id', 'updated_at', 'created_at'}

        # Quick checks first
        if old_val is new_val:
            return True
        if type(old_val) != type(new_val):
            return False
        if old_val == new_val:
            return True

        # Handle dictionaries
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            keys1 = set(old_val.keys()) - ignore_fields
            keys2 = set(new_val.keys()) - ignore_fields
            
            if keys1 != keys2:
                return False
                
            for key in keys1:
                if not ChangeLogger._values_equal_deep(old_val[key], new_val[key], ignore_fields):
                    return False
            return True

        # Handle lists with order-independent comparison
        elif isinstance(old_val, list) and isinstance(new_val, list):
            if len(old_val) != len(new_val):
                return False
                
            # Convert lists to sets of hashable representations
            def _make_hashable(item):
                if isinstance(item, dict):
                    return tuple(sorted(
                        (k, _make_hashable(v)) 
                        for k, v in item.items() 
                        if k not in ignore_fields
                    ))
                elif isinstance(item, list):
                    return tuple(sorted(_make_hashable(i) for i in item))
                else:
                    return item
                    
            set1 = set(_make_hashable(item) for item in old_val)
            set2 = set(_make_hashable(item) for item in new_val)
            
            return set1 == set2

        # Handle other types
        else:
            return old_val == new_val
    @staticmethod
    def log_activity(
        user,
        action: str,
        module: str,
        module_id: str,
        module_object_name: str,
        object_type: str,
        object_id: str,
        object_name: str,
        change_category: Optional[str] = None,
        old_data_path: Optional[Dict] = None,
        new_data_path: Optional[Dict] = None,
        description: Optional[str] = None,
        request=None
    ):
        """
        Log user activity with separate old and new values
        """
        from core.models import ChangeLog

        # Get IP and user agent from request if provided
        ip_address = None
        user_agent = None

        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORRAYED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create the log entry with separate old/new values
        log_entry = None
        try:
            # Check and clean up old entries in a single transaction
            existing_entries = ChangeLog.objects.filter(
                module_id=module_id
            ).order_by('-created_at')
            
            # If there are 3 or more
            # delete the excess
            if existing_entries.count() >= 3:
                # Keep only the 2 most recent
                entries_to_keep = existing_entries[:2]
                # Delete the rest
                ChangeLog.objects.filter(
                    module_id=module_id
                ).exclude(
                    id__in=entries_to_keep.values_list('id', flat=True)
                ).delete()

            log_entry = ChangeLog.objects.create(
                user=user,
                action=action,
                module=module,
                module_id=module_id,
                module_object_name=module_object_name,
                object_type=object_type,
                object_id=object_id,
                object_name=object_name,
                change_category=change_category,
                old_data_path=old_data_path,
                new_data_path=new_data_path,
                ip_address=ip_address,
                user_agent=user_agent,
                description=description or f"{action} {object_type}"
            )
        except Exception as e:
            print(f"Error creating log entry: {e}")
            return None

        return log_entry

    @staticmethod
    def log_model_changes(instance, old_instance,new_data, old_data, user = None, request=None):
        """
        Convenience method to log changes for a model instance with separate old/new values
        """

        changes = None
        old_data_path = ""
        new_data_path = ""
        change_category = ""

        changes = ChangeLogger.track_changes(new_data, old_data, instance, old_instance)

        if not os.path.exists(CHANGE_LOGS_PATH):
            os.mkdir(CHANGE_LOGS_PATH)

        if changes:
            change_category = changes.get('change_category', 'General')
            if changes.get('old_values'):
                log_id = str(uuid.uuid4())
                old_data_path = f"{CHANGE_LOGS_PATH}/{log_id}.json"

                with open(old_data_path, "w") as f:
                    json.dump(old_data, f, indent=2)

            if changes.get('new_values'):
                log_id = str(uuid.uuid4())
                new_data_path = f"{CHANGE_LOGS_PATH}/{log_id}.json"

                with open(new_data_path, "w") as f:
                    json.dump(new_data, f, indent=2)

        module = None
        module_id = None
        module_object_name = None
        try:
            module = instance._meta.model_name.upper()
            module_id = str(instance.pk)
            module_object_name = str(instance)
        except Exception as e:
            module = instance._meta.model_name.upper()
            module_id = str(instance.pk)
            module_object_name = str(instance)
            print(f"Error getting module: {e}")

        if changes:
            return ChangeLogger.log_activity(
                user=user,
                action='UPDATE',
                module=module,
                module_id=module_id,
                module_object_name=module_object_name,
                object_type=instance._meta.model_name,
                object_id=str(instance.pk),
                object_name=str(instance),
                change_category=change_category,
                old_data_path=old_data_path,
                new_data_path=new_data_path,
                request=request,
                description=f"Updated {instance._meta.model_name}: {instance}"
            )
        return None

    @staticmethod
    def log_model_creation(instance, user, request=None):
        """
        Log creation of a model instance (only new values)
        """
        # Get all field values for the new instance
        new_values = {}
        for field in instance._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at']:
                value = getattr(instance, field.name)
                new_values[field.name] = ChangeLogger._prepare_value_for_storage(value)

        module = None
        module_id = None
        module_object_name = None
        try:
            module = instance._meta.model_name.upper()
            module_id = str(instance.pk)
            module_object_name = str(instance)
        except Exception as e:
            module = instance._meta.model_name.upper()
            module_id = str(instance.pk)
            module_object_name = str(instance)
            print(f"Error getting module: {e}")

        return ChangeLogger.log_activity(
            user=user,
            action='CREATE',
            module=module,
            module_id=module_id,
            module_object_name=module_object_name,
            object_type=instance._meta.model_name,
            object_id=str(instance.pk),
            object_name=str(instance),
            fields_category="General",
            old_values=None,
            new_values=new_values,
            request=request,
            description=f"Created {instance._meta.model_name}: {instance}"
        )

    @staticmethod
    def log_model_deletion(instance, user, request=None):
        """
        Log deletion of a model instance (only old values)
        """
        # Get all field values for the deleted instance

        try:
            print("instance", instance)
            print(instance.activity_log_module)
        except Exception as e:
            print(f"Error creating log entry: {e}")

        old_values = {}
        for field in instance._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at']:
                value = getattr(instance, field.name)
                old_values[field.name] = ChangeLogger._prepare_value_for_storage(value)

        module = None
        module_id = None
        module_object_name = None
        try:
            module = instance._meta.model_name.upper()
            module_id = str(instance.pk)
            module_object_name = str(instance)
        except Exception as e:
            module = instance._meta.model_name.upper()
            module_id = str(instance.pk)
            module_object_name = str(instance)
            print(f"Error getting module: {e}")

        return ChangeLogger.log_activity(
            user=user,
            action='DELETE',
            module=module,
            module_id=module_id,
            module_object_name=module_object_name,
            object_type=instance._meta.model_name,
            object_id=str(instance.pk),
            object_name=str(instance),
            fields_category="General",
            old_values=old_values,
            new_values={},  # No new values for deletion
            request=request,
            description=f"Deleted {instance._meta.model_name}: {instance}"
        )
