"""
Unified Redis Log Subscriber Service
Subscribes to Redis channel for both AI agent and extraction service messages.
Handles:
1. Database persistence (AiAgentConversation & BatchStatus tables)
2. Real-time WebSocket notifications to frontend via Django Channels

Architecture:
- AI Agent & Extraction services publish messages to Redis channel
- This unified service subscribes and processes all messages
- Direct DB writes to PostgreSQL via Django ORM
- WebSocket broadcasts via Django Channels
- Single container replaces two separate bridge services
"""
import asyncio
from dotenv import load_dotenv
import json
import logging
import redis.asyncio as redis
import os
import django
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

# Configure Django settings before imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from core.models import AiAgentConversation, BatchStatus
from core.serializers import AiAgentConversationSerializer, BatchStatusSerializer
from utils.utils import convert_to_title

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
LOG_UPDATE_CHANNEL = os.getenv("LOG_UPDATE_CHANNEL") or "websocket_log_updates"


class UnifiedRedisLogSubscriber:
    """
    Unified Redis pub/sub subscriber for both AI agent and extraction service messages.
    Handles DB persistence and WebSocket broadcasting for all log types.
    """
    
    def __init__(self):
        self.redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        self.redis_client = None
        self.pubsub = None
        self.message_count = {"agent": 0, "extraction": 0}
        
    async def connect_redis(self):
        """Establish Redis connection and subscribe to channel"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(LOG_UPDATE_CHANNEL)
            logger.info(f"✓ Subscribed to Redis channel: {LOG_UPDATE_CHANNEL}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self):
        """Clean up Redis connections"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(LOG_UPDATE_CHANNEL)
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info(f"Disconnected from Redis (processed: {self.message_count['agent']} agent, {self.message_count['extraction']} extraction messages)")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def process_ai_agent_message(self, message_data: dict):
        """
        Process AI agent message:
        1. Transform data (agent name to title case)
        2. Save to AiAgentConversation table
        3. Broadcast to ai_agent_response_{batch_id} WebSocket group
        """
        try:
            transaction_id = message_data.get("transaction_id")
            batch_id = message_data.get("batch_id")
            message_type = message_data.get("message_type")
            agent_name = message_data.get("agent_name", "")
            
            # Transform agent name to title case
            if agent_name:
                message_data["agent_name"] = convert_to_title(agent_name)
            
            # Save to database
            ai_agent_log_data = await self.write_ai_agent_log(
                transaction_id=transaction_id,
                batch_id=batch_id,
                message_type=message_type,
                message=message_data,
            )
            
            # Broadcast to WebSocket group
            await self.send_to_group(
                group_name=f"ai_agent_response_{batch_id}",
                message_type="ai_agent_response",
                data=ai_agent_log_data
            )
            
            self.message_count["agent"] += 1
            logger.info(
                f"[AI Agent] batch={batch_id}, agent={agent_name}, type={message_type}"
            )
            
        except Exception as e:
            logger.error(f"Error processing AI agent message: {e}", exc_info=True)
    
    async def process_extraction_message(self, message_data: dict):
        """
        Process extraction service message:
        1. Build remarks from sub_messages and reasoning
        2. Save to BatchStatus table
        3. Broadcast to batch_status_{batch_id} WebSocket group
        """
        try:
            batch_id = message_data.get("batch_id")
            title = message_data.get("title", "")
            sub_messages_list = message_data.get("sub_messages_list", [])
            reasoning = message_data.get("reasoning")
            is_agent = message_data.get("is_agent", False)
            
            # Determine action and build remarks
            action = "display_subprocess_messages"
            remarks = {
                'sub_messages': sub_messages_list,
                'is_agent': is_agent
            }
            
            if reasoning:
                action = "display_json"
                remarks['reasoning'] = reasoning
            
            # Save to database
            batch_log_data = await self.write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message=title,
                remarks=json.dumps(remarks),
                action=action,
            )
            
            # Broadcast to WebSocket group
            await self.send_to_group(
                group_name=f"batch_status_{batch_id}",
                message_type="batch_status",
                data=batch_log_data
            )
            
            self.message_count["extraction"] += 1
            logger.info(
                f"[Extraction] batch={batch_id}, title={title}, action={action}"
            )
            
        except Exception as e:
            logger.error(f"Error processing extraction message: {e}", exc_info=True)
    
    async def process_message(self, message_data: dict):
        """
        Route message to appropriate handler based on is_agent flag.
        
        Messages with is_agent=True -> AI agent handler
        Messages with is_agent=False or missing -> Extraction handler
        """
        try:
            is_agent = message_data.get("is_agent", False)
            
            if is_agent:
                await self.process_ai_agent_message(message_data)
            else:
                await self.process_extraction_message(message_data)
                
        except Exception as e:
            logger.error(f"Error routing message: {e}", exc_info=True)
    
    @database_sync_to_async
    def write_ai_agent_log(self, transaction_id, batch_id, message_type, message):
        """
        Save AI agent message to AiAgentConversation table.
        Uses Django ORM for direct PostgreSQL writes.
        """
        try:
            ai_agent_message_instance = AiAgentConversation.objects.create(
                transaction_id=transaction_id,
                batch_id=batch_id,
                type=message_type,
                message=message,
            )
            
            serialized_message = AiAgentConversationSerializer(ai_agent_message_instance)
            return serialized_message.data
            
        except Exception as e:
            logger.error(f"Database write error (AI agent): {e}", exc_info=True)
            raise
    
    @database_sync_to_async
    def write_batch_log(self, **kwargs):
        """
        Save extraction status to BatchStatus table.
        Uses Django ORM for direct PostgreSQL writes.
        """
        try:
            batch_status_instance = BatchStatus.objects.create(**kwargs)
            batch_log_data = dict(BatchStatusSerializer(batch_status_instance).data)
            return batch_log_data
        except Exception as e:
            logger.error(f"Database write error (extraction): {e}", exc_info=True)
            raise
    
    async def send_to_group(self, group_name: str, message_type: str, data: dict):
        """
        Broadcast message to WebSocket group via Django Channels.
        Frontend clients subscribed to this group will receive real-time updates.
        """
        try:
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                group_name,
                {
                    "type": message_type,
                    "data": data
                }
            )
            logger.debug(f"Sent to WebSocket group: {group_name}")
        except Exception as e:
            logger.error(f"WebSocket broadcast error for {group_name}: {e}", exc_info=True)
    
    async def listen(self):
        """
        Main listener loop for Redis pub/sub messages.
        Processes all messages from both AI agent and extraction services.
        """
        try:
            logger.info("🎧 Starting unified Redis message listener...")
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse JSON message
                        message_data = json.loads(message["data"])
                        await self.process_message(message_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {message['data'][:100]}..., error: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Listener error: {e}", exc_info=True)
            raise
    
    async def run(self):
        """
        Main run loop with auto-reconnection.
        Ensures service stays running and reconnects on failures.
        Production-ready with exponential backoff and health monitoring.
        """
        max_retry_delay = 60
        retry_delay = 5
        
        while True:
            try:
                success = await self.connect_redis()
                if success:
                    logger.info("✓ Unified Redis Log Subscriber started successfully")
                    retry_delay = 5  # Reset retry delay on successful connection
                    await self.listen()
                else:
                    logger.warning(f"Failed to connect, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                    
            except asyncio.CancelledError:
                logger.info("Service cancelled, shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            finally:
                await self.disconnect()


# Main execution
if __name__ == "__main__":
    subscriber = UnifiedRedisLogSubscriber()
    try:
        asyncio.run(subscriber.run())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
