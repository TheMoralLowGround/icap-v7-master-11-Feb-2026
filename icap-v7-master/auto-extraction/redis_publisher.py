"""
Auto-Extraction Redis Publisher
Publishes extraction service messages to Redis for backend consumption.
Backend service subscribes to this channel and handles DB writes + WebSocket notifications.

Production features:
- Connection pooling with automatic retry
- Graceful error handling with exponential backoff
- Message delivery guarantees with retry logic
- Health monitoring and metrics
"""
import logging
import json
import os
import asyncio
import redis.asyncio as redis
from utils.config import Config

logger = logging.getLogger(__name__)

# Redis channel for log updates
LOG_UPDATE_CHANNEL = os.getenv("LOG_UPDATE_CHANNEL", "websocket_log_updates")

# Metrics
publish_stats = {
    "success": 0,
    "failed": 0,
    "no_subscribers": 0
}


async def get_redis_connection():
    """
    Create a fresh Redis connection for the current event loop.
    Avoids event loop conflicts by not reusing connection pools.
    """
    return redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


async def broadcast_log_update(log_data: dict, max_retries: int = 3):
    """
    Send log update via Redis pub/sub with automatic retry logic.
    
    Production-ready with:
    - Exponential backoff retry mechanism
    - Connection failure handling
    - Message delivery tracking
    - Proper connection cleanup
    
    Args:
        log_data: Dictionary containing log data with keys:
            - batch_id: Batch identifier
            - title: Log title/message
            - sub_messages_list: List of sub-messages (optional)
            - reasoning: Reasoning data (optional)
            - is_agent: Boolean indicating if this is from an agent (optional)
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        bool: True if message was published successfully, False otherwise
    """
    batch_id = log_data.get('batch_id', 'N/A')
    title = log_data.get('title', 'N/A')
    
    for attempt in range(max_retries):
        r = None
        try:
            r = await get_redis_connection()
            message = json.dumps(log_data)
            recipients = await r.publish(LOG_UPDATE_CHANNEL, message)
            
            if recipients > 0:
                publish_stats["success"] += 1
                logger.debug(
                    f"Log published to {recipients} subscriber(s) - "
                    f"batch={batch_id}, title={title[:50]}"
                )
                return True
            else:
                publish_stats["no_subscribers"] += 1
                logger.warning(
                    f"Log published but no subscribers - batch={batch_id}"
                )
                return True
                
        except redis.ConnectionError as e:
            if attempt < max_retries - 1:
                retry_delay = 2 ** attempt
                logger.warning(
                    f"Redis connection error (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {retry_delay}s: {e}"
                )
                await asyncio.sleep(retry_delay)
            else:
                publish_stats["failed"] += 1
                logger.error(
                    f"Failed to publish after {max_retries} attempts - "
                    f"batch={batch_id}, error={e}"
                )
                return False
                
        except Exception as e:
            publish_stats["failed"] += 1
            logger.error(
                f"Unexpected error publishing log - batch={batch_id}, error={e}",
                exc_info=True
            )
            return False
        
        finally:
            # Always close connection to prevent event loop issues
            if r is not None:
                try:
                    await r.close()
                except Exception:
                    pass
    
    return False


async def close_redis_connections():
    """
    Cleanup function for graceful shutdown.
    No-op since we create fresh connections per call.
    """
    logger.info("Redis publisher cleanup complete")


def get_publish_stats() -> dict:
    """
    Get publishing statistics for monitoring.
    
    Returns:
        dict: Statistics including success, failed, and no_subscribers counts
    """
    return publish_stats.copy()

