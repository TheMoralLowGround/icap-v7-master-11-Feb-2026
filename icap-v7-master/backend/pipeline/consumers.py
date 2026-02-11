"""
Organization: AIDocbuilder Inc.
File: pipeline/consumers.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Feature improvement

Last Updated By: Nayem
Last Updated At: 2024-07-04

Description:
    This script handles Websocket connections status updates, 
    processes incoming messages and interacts with the cache.

Dependencies:
    - json
    - parse_qs from urllib.parse
    - AsyncWebsocketConsumer from channels.generic.websocket
    - cache from django.core.cache

Main Features:
    - Websocket connections status.
    - Process incoming messages.
"""
import datetime
import json
import re
from urllib.parse import parse_qs
import uuid
from core.models import AiAgentConversation, Batch
import websockets
import asyncio
from dotenv import load_dotenv
import os

from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.core.cache import cache
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

from utils.presence_utils import unregister_editor_presence


load_dotenv()

AI_AGENT_HOST = os.getenv("AI_AGENT_HOST")
AI_AGENT_PORT = os.getenv("AI_AGENT_PORT")

AI_AGENT_URI = f"ws://{AI_AGENT_HOST}:{AI_AGENT_PORT}"


class StatusConsumer(AsyncWebsocketConsumer):
    ai_agent_handlers = {}

    @classmethod
    async def initialize_ai_agent(cls, channel_layer, session_id):
        """
        Initialize the AI agent handler for a specific session
        
        Args:
            channel_layer: The channel layer to use
            session_id: Unique identifier for the session
        
        Returns:
            Initialized AIAgentConsumer for the session
        """
        # Check if handler already exists for this session
        if session_id in cls.ai_agent_handlers:
            return cls.ai_agent_handlers[session_id]
        
        # Create a new agent consumer for this session
        agent = AIAgentConsumer(channel_layer)
        
        # Connect the agent
        await agent.connect()
        
        # Store the initialized agent
        cls.ai_agent_handlers[session_id] = agent
        
        return agent

    async def connect(self):
        """Only allow connection if valid ws_ticket is passed in query parameters"""
        query_string = self.scope["query_string"].decode("utf-8")
        query_params = dict(parse_qs(query_string))
        ws_ticket = query_params.get("ws_ticket")[0]

        # initialize per-connection presence rooms tracking
        self.presence_rooms = {}

        if cache.delete(ws_ticket):
            await self.accept()

    async def disconnect(self, close_code):
        # On disconnect, attempt to unregister any presence entries associated
        # with this websocket connection and broadcast editor_left events.
        try:
            user = self.scope.get('user')
            if not user or getattr(user, 'is_anonymous', True):
                return

            rooms = list(self.presence_rooms.items()) if hasattr(self, 'presence_rooms') else []
            for room_name, info in rooms:
                try:
                    resource_type = info.get('resource_type')
                    resource_id = info.get('resource_id')
                    tab_id = info.get('tab_id')

                    # unregister presence (sync function) via sync_to_async
                    await sync_to_async(unregister_editor_presence)(
                        resource_type=resource_type,
                        resource_id=str(resource_id),
                        user_id=user.id,
                        tab_id=tab_id,
                    )

                    # broadcast editor_left so other clients update immediately
                    await self.channel_layer.group_send(
                        room_name,
                        {
                            "type": "editor_left",
                            "user_id": user.id,
                            "username": getattr(user, 'username', ''),
                            "resource_type": resource_type,
                            "resource_id": str(resource_id),
                            "tab_id": tab_id,
                        },
                    )
                except Exception:
                    continue
        except Exception:
            pass

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)

        if data["type"] == "join_room":
            await self.channel_layer.group_add(data["room_name"], self.channel_name)

        elif data["type"] == "leave_room":
            await self.channel_layer.group_discard(data["room_name"], self.channel_name)

        elif data["type"] == "join_presence_room":
            # Join presence room for editor notifications
            resource_type = data.get("resource_type")
            resource_id = data.get("resource_id")
            tab_id = data.get("tab_id")
            if resource_type and resource_id:
                room_name = f"presence_{resource_type}_{resource_id}"
                await self.channel_layer.group_add(room_name, self.channel_name)
                try:
                    if tab_id:
                        # track this room and associated tab_id so we can cleanup on disconnect
                        self.presence_rooms[room_name] = {
                            'resource_type': resource_type,
                            'resource_id': resource_id,
                            'tab_id': tab_id,
                        }
                except Exception:
                    pass

        elif data["type"] == "leave_presence_room":
            # Leave presence room
            resource_type = data.get("resource_type")
            resource_id = data.get("resource_id")
            tab_id = data.get("tab_id")
            if resource_type and resource_id:
                room_name = f"presence_{resource_type}_{resource_id}"
                await self.channel_layer.group_discard(room_name, self.channel_name)
                try:
                    if room_name in self.presence_rooms:
                        del self.presence_rooms[room_name]
                except Exception:
                    pass

        elif data["type"] == "ai_agent_consumer":
            # Extract session_id, default to None if not provided
            message = data.get("data", {})
            batch_id = message.get("batch_id")
            close = message.get("close")

            session_id = await self.get_session_id(batch_id)

            # Close the connection if 'close' is true
            if not session_id and close:
                return
            
            if session_id and close:
                ai_agent = self.ai_agent_handlers.get(session_id)

                if ai_agent:
                    await ai_agent.disconnect()
                return

            # Initialize AI agent if not exists
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Initialize or get existing AI agent for this session
            ai_agent = await self.__class__.initialize_ai_agent(
                self.channel_layer, 
                session_id
            )
            
            # Forward message to the specific AI agent
            await ai_agent.forward_message_to_agent({
                "type": "forward_message_to_agent",
                "session_id": session_id,
                "message": data.get("data", {}),
            })

    async def batch_status(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "batch_status",
                }
            )
        )

    async def batch_status_tag(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "batch_status_tag",
                }
            )
        )

    async def email_batch_status_tag(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "email_batch_status_tag",
                }
            )
        )
    
    async def train_batch_status_tag(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "train_batch_status_tag",
                }
            )
        )
    
    async def test_models_status(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "test_models_status",
                }
            )
        )

    async def chunk_data_status(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "chunk_data_status",
                }
            )
        )
    async def timeline(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "timeline",
                }
            )
        )

    async def timeline_tag(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "timeline_tag",
                }
            )
        )

    async def ai_agent_response(self, event):
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "data": data,
                    "type": "ai_agent_response",
                }
            )
        )

    async def editor_joined(self, event):
        """Handle editor joined presence event"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "editor_joined",
                    "data": {
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "resource_type": event["resource_type"],
                        "resource_id": event["resource_id"],
                        "tab_id": event["tab_id"]
                    }
                }
            )
        )

    async def editor_left(self, event):
        """Handle editor left presence event"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "editor_left",
                    "data": {
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "resource_type": event["resource_type"],
                        "resource_id": event["resource_id"],
                        "tab_id": event["tab_id"]
                    }
                }
            )
        )

    @database_sync_to_async
    def get_session_id(self, batch_id):
        """Get session_id from AiAgentConversation in a database-safe way"""
        cutoff_time = timezone.now() - datetime.timedelta(seconds=540)

        try:
            # Only get conversations newer than the cutoff time
            latest_conversation = AiAgentConversation.objects.filter(
                batch_id=batch_id,
                type='agent',
                event_time__gt=cutoff_time
            ).order_by('-event_time').first()
            
            if latest_conversation is None:
                return None
            
            message = latest_conversation.message

            return message.get("session_id")
        except Exception as e:
            return None

class AIAgentConsumer(AsyncWebsocketConsumer):
    """Consumer that connects to the AI Agent WebSocket server"""
    def __init__(self, channel_layer=None):
        self.channel_layer = channel_layer
        # Other initialization
    
    async def connect(self):
        # Connect to AI Agent WebSocket server
        try:
            self.agent_socket = await websockets.connect(AI_AGENT_URI)
            
            # Start background task to listen for AI Agent responses
            self.listener_task = asyncio.create_task(self.listen_for_agent_responses())
            
            # Accept the connection
            await self.accept()
            
        except Exception as e:
            # Don't accept the connection if we can't connect to AI Agent
            return
    
    async def disconnect(self):
        """Clean up connections"""
        # Cancel the listener task
        if hasattr(self, 'listener_task') and not self.listener_task.done():
            self.listener_task.cancel()
            
        # Close connection to AI Agent
        if hasattr(self, 'agent_socket'):
            await self.agent_socket.close()
        
    async def forward_message_to_agent(self, event):
        """Handle WebSocket message from frontend"""
        try:
            message = event["message"]
            session_id = event["session_id"]
            batch_id = message.get("batch_id")
            user_input = message.get("user_input")
            new_conversation_messages = message.get("new_conversation_messages", [])

            # Get batch data using database_sync_to_async
            ra_json = await self.get_batch_ra_json(batch_id)

            if len(new_conversation_messages):
                for item in new_conversation_messages:
                    message_type = item.get("type", "user")
                    new_conversation_message = item.get("message", "user")
                    new_conversation_message.update({
                        "session_id": session_id,
                    })
                    await self.save_conversation_to_db(batch_id, message_type, new_conversation_message)
            
            # Prepare message for AI Agent
            agent_message = {
                'user_input': user_input,
                'batch_id': batch_id,
                "session_id": session_id,
            }

            # Save request to database
            await self.save_conversation_to_db(batch_id, "user", agent_message)

            # Include ra_json to agent message
            agent_message["ra_json"] = ra_json
            
            # Send to AI Agent
            if hasattr(self, 'agent_socket'):
                await self.agent_socket.send(json.dumps(agent_message))
            else:
                pass
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def listen_for_agent_responses(self):
        """Listen for responses from AI Agent"""
        while True:
            try:
                # Wait for response (doesn't block other operations)
                response = await self.agent_socket.recv()
                
                try:
                    # Parse response
                    response_data = json.loads(response)

                    description = response_data.get("chat", {}).get("description", None)

                    if description:
                        description = self.format_text_for_html(description)
                        response_data["chat"]["description"] = description

                    # Extract request_id (batch_id)
                    batch_id = response_data.get('batch_id')
                        
                    
                    # Save response to database
                    await self.save_conversation_to_db(batch_id, "agent", response_data)

                    # Forward message to StatusConsumer
                    await self.channel_layer.group_send(
                        f'ai_agent_response_{batch_id}',  # Group that StatusConsumer is listening to
                        {
                            'type': 'ai_agent_response',
                            'data': response_data, 
                        }
                    )
                except json.JSONDecodeError:
                    pass
                
            except websockets.exceptions.ConnectionClosed:
                try:
                    # Try to reconnect
                    self.agent_socket = await websockets.connect(AI_AGENT_URI)
                except Exception as e:
                    await asyncio.sleep(5)  # Wait before retrying
                    
            except Exception as e:
                await asyncio.sleep(1)

    @database_sync_to_async
    def get_batch_ra_json(self, batch_id):
        """Get ra_json from Batch in a database-safe way"""
        try:
            batch = Batch.objects.filter(id=batch_id).first()
            if batch:
                return batch.ra_json
            return {}
        except Exception as e:
            return {}
    
    @database_sync_to_async
    def get_session_id(self, batch_id):
        """Get session_id from AiAgentConversation in a database-safe way"""
        cutoff_time = timezone.now() - datetime.timedelta(seconds=540)

        try:
            # Only get conversations newer than the cutoff time
            latest_conversation = AiAgentConversation.objects.filter(
                batch_id=batch_id,
                type='agent',
                event_time__gt=cutoff_time
            ).order_by('-event_time').first()
            
            if latest_conversation is None:
                return None
            
            message = latest_conversation.message

            return message.get("session_id")
        except Exception as e:
            return None
        
    @database_sync_to_async
    def save_conversation_to_db(self, batch_id, message_type, message):
        """Save request to database"""
        try:
            AiAgentConversation.objects.create(
                batch_id=batch_id,
                type=message_type,  # Renamed parameter used here
                message=message,
            )
        except Exception as e:
            pass
    
    def format_text_for_html(self, text):
        """
        Format text for HTML display by replacing newlines with <br> tags
        and spaces with &nbsp;
        """
        if not text:
            return ""
        
        # Check if text needs formatting (contains newlines or multiple spaces)
        needs_formatting = '\n' in text or re.search(r' {2,}', text)
        
        if not needs_formatting:
            return text
        
        # Replace newlines with <br> tags
        formatted_text = text.replace("\n", "<br>")
        
        # Replace spaces with non-breaking spaces
        formatted_text = formatted_text.replace(" ", "&nbsp;")
        
        return formatted_text