"""
Organization: AIDocbuilder Inc.
File: utils/presence_utils.py
Version: 7.0

Authors:
    - Initial implementation

Description:
    Editor presence tracking utilities using Redis.
    Tracks which users are currently editing Projects/Processes.

Dependencies:
    - redis
    - json
    - datetime

Main Features:
    - Register editor presence with auto-expiry
    - Unregister editor presence
    - Get list of active editors
    - Heartbeat to extend presence TTL
"""
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from utils.redis_utils import redis_instance
import logging

logger = logging.getLogger(__name__)

# TTL for presence entries (2 minutes)
PRESENCE_TTL = 120


def _get_presence_key(resource_type: str, resource_id: str) -> str:
    """Generate Redis key for presence tracking."""
    return f"editor_presence:{resource_type}:{resource_id}"


def _get_user_field(user_id: int, tab_id: str) -> str:
    """Generate hash field name for a user+tab."""
    return f"{user_id}:{tab_id}"


def register_editor_presence(
    resource_type: str,
    resource_id: str,
    user_id: int,
    username: str,
    tab_id: str
) -> Dict:
    """
    Register a user's presence as editing a resource.
    
    Args:
        resource_type: 'project' or 'process'
        resource_id: ID of the resource
        user_id: User's ID
        username: User's display name
        tab_id: Unique tab identifier
    
    Returns:
        Dict with registration status
    """
    key = _get_presence_key(resource_type, resource_id)
    field = _get_user_field(user_id, tab_id)
    
    presence_data = {
        "user_id": user_id,
        "username": username,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }
    
    # Store in Redis hash
    redis_instance.hset(key, field, json.dumps(presence_data))
    
    # Set TTL on the hash key
    redis_instance.expire(key, PRESENCE_TTL)
    
    return {"success": True, "user_id": user_id, "tab_id": tab_id}


def unregister_editor_presence(
    resource_type: str,
    resource_id: str,
    user_id: int,
    tab_id: str
) -> Dict:
    """
    Unregister a user's presence from a resource.
    
    Args:
        resource_type: 'project' or 'process'
        resource_id: ID of the resource
        user_id: User's ID
        tab_id: Unique tab identifier
    
    Returns:
        Dict with unregistration status
    """
    key = _get_presence_key(resource_type, resource_id)
    field = _get_user_field(user_id, tab_id)
    
    # Remove from hash
    deleted = redis_instance.hdel(key, field)
    
    # If hash is empty, delete the key
    if redis_instance.hlen(key) == 0:
        redis_instance.delete(key)
    logger.info("unregister_editor_presence: resource=%s:%s user=%s tab=%s deleted=%s", resource_type, resource_id, user_id, tab_id, bool(deleted))
    
    return {"success": bool(deleted), "user_id": user_id, "tab_id": tab_id}


def get_active_editors(
    resource_type: str,
    resource_id: str,
    exclude_user_id: Optional[int] = None,
    exclude_tab_id: Optional[str] = None
) -> List[Dict]:
    """
    Get list of users currently editing a resource.
    
    Args:
        resource_type: 'project' or 'process'
        resource_id: ID of the resource
        exclude_user_id: Optional user ID to exclude (typically current user)
        exclude_tab_id: Optional tab ID to exclude
    
    Returns:
        List of editor dictionaries with username, user_id, started_at
    """
    key = _get_presence_key(resource_type, resource_id)
    
    # Get all entries from hash
    all_entries = redis_instance.hgetall(key)
    
    editors = []
    for field, value in all_entries.items():
        field_str = field.decode('utf-8') if isinstance(field, bytes) else field
        value_str = value.decode('utf-8') if isinstance(value, bytes) else value
        
        # Parse field to get user_id and tab_id
        parts = field_str.split(':')
        if len(parts) != 2:
            continue
        
        entry_user_id = int(parts[0])
        entry_tab_id = parts[1]
        
        # Skip if this is the excluded user+tab
        if exclude_user_id and exclude_tab_id:
            if entry_user_id == exclude_user_id and entry_tab_id == exclude_tab_id:
                continue
        
        # Parse presence data
        try:
            presence_data = json.loads(value_str)
            editors.append({
                "user_id": presence_data["user_id"],
                "username": presence_data["username"],
                "started_at": presence_data["started_at"],
                "last_heartbeat": presence_data.get("last_heartbeat"),
                "tab_id": entry_tab_id
            })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return editors


def heartbeat_presence(
    resource_type: str,
    resource_id: str,
    user_id: int,
    tab_id: str
) -> Dict:
    """
    Update heartbeat timestamp and extend TTL for a presence entry.
    
    Args:
        resource_type: 'project' or 'process'
        resource_id: ID of the resource
        user_id: User's ID
        tab_id: Unique tab identifier
    
    Returns:
        Dict with heartbeat status
    """
    key = _get_presence_key(resource_type, resource_id)
    field = _get_user_field(user_id, tab_id)
    
    # Get existing entry
    existing = redis_instance.hget(key, field)
    
    if not existing:
        return {"success": False, "error": "Presence not found"}
    
    # Parse and update
    existing_str = existing.decode('utf-8') if isinstance(existing, bytes) else existing
    presence_data = json.loads(existing_str)
    presence_data["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    
    # Update in Redis
    redis_instance.hset(key, field, json.dumps(presence_data))
    
    # Extend TTL
    redis_instance.expire(key, PRESENCE_TTL)
    
    return {"success": True, "user_id": user_id, "tab_id": tab_id}


def cleanup_stale_presence(resource_type: str, resource_id: str) -> Dict:
    """
    Cleanup utility (optional) - Redis TTL handles most cleanup automatically.
    This can be called manually if needed.
    
    Args:
        resource_type: 'project' or 'process'
        resource_id: ID of the resource
    
    Returns:
        Dict with cleanup stats
    """
    key = _get_presence_key(resource_type, resource_id)
    
    # Get all entries
    all_entries = redis_instance.hgetall(key)
    
    removed_count = 0
    now = datetime.now(timezone.utc)
    
    for field, value in all_entries.items():
        field_str = field.decode('utf-8') if isinstance(field, bytes) else field
        value_str = value.decode('utf-8') if isinstance(value, bytes) else value
        
        try:
            presence_data = json.loads(value_str)
            last_heartbeat = datetime.fromisoformat(presence_data.get("last_heartbeat", presence_data["started_at"]))
            
            # If no heartbeat in 3 minutes, remove
            if (now - last_heartbeat).total_seconds() > 180:
                redis_instance.hdel(key, field)
                removed_count += 1
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid entry, remove it
            redis_instance.hdel(key, field)
            removed_count += 1
    
    # If hash is empty, delete the key
    if redis_instance.hlen(key) == 0:
        redis_instance.delete(key)
    
    return {"success": True, "removed_count": removed_count}


def cleanup_stale_presence_threshold(resource_type: str, resource_id: str, stale_seconds: int = 40) -> Dict:
    """
    Remove presence entries for a resource whose last_heartbeat is older than stale_seconds.
    This is intended to be used opportunistically when another user attempts to join,
    allowing quick takeover if the previous editor stopped heartbeating (for example
    due to a page reload).

    Returns a dict with removed entries information for broadcasting.
    """
    key = _get_presence_key(resource_type, resource_id)
    all_entries = redis_instance.hgetall(key)
    removed_entries = []
    now = datetime.now(timezone.utc)

    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
    except Exception:
        channel_layer = None

    for field, value in all_entries.items():
        field_str = field.decode('utf-8') if isinstance(field, bytes) else field
        value_str = value.decode('utf-8') if isinstance(value, bytes) else value

        try:
            presence_data = json.loads(value_str)
            last_hb = presence_data.get('last_heartbeat') or presence_data.get('started_at')
            last_dt = datetime.fromisoformat(last_hb)
            age = (now - last_dt).total_seconds()
        except Exception:
            # If parsing fails, treat as stale
            age = float('inf')

        if age > stale_seconds:
            # Remove it
            try:
                redis_instance.hdel(key, field)
            except Exception:
                continue

            # Record removed entry
            try:
                parts = field_str.split(':', 1)
                entry_user_id = int(parts[0]) if parts[0].isdigit() else None
                entry_tab_id = parts[1] if len(parts) > 1 else None
            except Exception:
                entry_user_id = None
                entry_tab_id = None

            removed_entry = {
                'user_id': entry_user_id,
                'tab_id': entry_tab_id,
                'username': presence_data.get('username') if isinstance(presence_data, dict) else None,
            }
            removed_entries.append(removed_entry)

            logger.info("cleanup_stale_presence_threshold: removed stale presence resource=%s user=%s tab=%s age=%s", key, removed_entry['user_id'], removed_entry['tab_id'], age)

            # Broadcast editor_left for this removed entry
            if channel_layer:
                try:
                    group_name = f"presence_{resource_type}_{resource_id}"
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'editor_left',
                            'user_id': removed_entry['user_id'],
                            'username': removed_entry['username'],
                            'resource_type': resource_type,
                            'resource_id': resource_id,
                            'tab_id': removed_entry['tab_id'],
                        }
                    )
                except Exception:
                    pass

    # If hash empty, delete key
    try:
        if redis_instance.hlen(key) == 0:
            redis_instance.delete(key)
    except Exception:
        pass

    return {"success": True, "removed": removed_entries}


def unregister_user_presence_all(user_id: int) -> Dict:
    """
    Remove all presence entries for a given user across all resources.

    Args:
        user_id: ID of the user to remove

    Returns:
        Dict with number of removed entries
    """
    pattern = "editor_presence:*"
    removed = 0

    # Lazy import channels to avoid hard dependency unless used
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
    except Exception:
        channel_layer = None

    # Iterate over matching keys
    for raw_key in redis_instance.scan_iter(match=pattern):
        key = raw_key.decode('utf-8') if isinstance(raw_key, bytes) else raw_key

        # parse resource_type and resource_id from key: editor_presence:<resource_type>:<resource_id>
        try:
            _, resource_type, resource_id = key.split(':', 2)
        except Exception:
            resource_type = None
            resource_id = None

        # hkeys may be bytes
        try:
            fields = redis_instance.hkeys(key)
        except Exception:
            continue

        for field in fields:
            field_str = field.decode('utf-8') if isinstance(field, bytes) else field
            if field_str.startswith(f"{user_id}:"):
                # attempt to read value for broadcasting
                try:
                    val = redis_instance.hget(key, field)
                    val_str = val.decode('utf-8') if isinstance(val, bytes) else val
                    presence_data = json.loads(val_str)
                    username = presence_data.get('username')
                    tab_id = field_str.split(':', 1)[1]
                except Exception:
                    username = None
                    tab_id = field_str.split(':', 1)[1] if ':' in field_str else None

                # Delete the field
                try:
                    redis_instance.hdel(key, field)
                    removed += 1
                except Exception:
                    continue

                logger.info("unregister_user_presence_all: removed resource=%s user=%s tab=%s", key, user_id, tab_id)
                # Broadcast editor_left event so other clients update immediately
                if channel_layer and resource_type and resource_id:
                    try:
                        group_name = f"presence_{resource_type}_{resource_id}"
                        async_to_sync(channel_layer.group_send)(
                            group_name,
                            {
                                'type': 'editor_left',
                                'user_id': user_id,
                                'username': username,
                                'resource_type': resource_type,
                                'resource_id': resource_id,
                                'tab_id': tab_id,
                            }
                        )
                    except Exception:
                        # best-effort, do not fail cleanup on broadcast error
                        pass

        # If hash is empty, delete the key
        try:
            if redis_instance.hlen(key) == 0:
                redis_instance.delete(key)
        except Exception:
            pass

    return {"success": True, "removed_count": removed}
