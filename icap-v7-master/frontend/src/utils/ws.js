/**
 * Organization: AIDocbuilder Inc.
 * File: utils/ws.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Refined WebSocket connection handling and room subscription logic
 *   - [Your Name]: Added AI agent functionality and enhanced message handling
 *
 * Last Updated By: [Your Name]
 * Last Updated At: [Current Date]
 *
 * Description:
 *   This module provides utility functions for managing WebSocket connections, handling
 *   room subscriptions, and processing incoming messages. It includes functionality to
 *   initialize the connection, manage room joins and leaves, and ensure reliable operation
 *   through pending operation queues when the connection is unhealthy. Now includes
 *   enhanced support for AI agent interactions.
 *
 * Dependencies:
 *   - axios: For fetching WebSocket ticket
 *   - bus: Event bus for emitting events across the application
 *   - getEnv: Utility for accessing environment variables
 *
 * Main Features:
 *   - WebSocket connection management
 *   - Room subscription handling (join/leave)
 *   - Incoming message processing with event emission
 *   - Retry mechanism for pending operations when connection is unhealthy
 *   - Fetch WebSocket ticket from the server for connection initialization
 *   - AI agent message handling and response processing
 *   - Support for sending custom messages through WebSocket
 *
 * Core Components:
 *   - `createConnection`: Initializes the WebSocket connection using a fetched ticket
 *   - `closeConnection`: Closes the active WebSocket connection
 *   - `joinRoom`: Joins a WebSocket room, with subscription count management
 *   - `leaveRoom`: Leaves a WebSocket room, ensuring no active subscriptions remain
 *   - `messageHandler`: Processes incoming WebSocket messages and triggers events
 *   - `isConnectionHealthy`: Verifies if the WebSocket connection is active
 *   - `resolvePendingOperations`: Resolves queued operations once the connection is healthy
 *   - `pendingOperations`: Queue for pending room join/leave operations
 *   - `sendMessage`: Sends messages through the WebSocket connection
 *
 * Notes:
 *   - Operations that depend on the WebSocket connection (e.g., joining/leaving rooms) are queued
 *     when the connection is unhealthy and retried once the connection is re-established.
 *   - Error events are emitted in case of connection issues or ticket fetching failures.
 *   - AI agent responses are automatically handled and emitted through the event bus.
 */
// Importing required modules
import axios from 'axios' // Axios for making HTTP requests
import bus from '@/bus' // Event bus for emitting events across the application
import getEnv from '@/utils/env' // Utility for fetching environment variables
import { getTabId } from '@/utils/presence'

// Constants
const INITIAL_RECONNECT_DELAY = 3000 // Initial delay before retrying connection (ms)
const MAX_RECONNECT_DELAY = 30000 // Maximum delay (30 seconds)
const MAX_RETRIES = 10 // Maximum number of retries before giving up

// Object to track joined rooms and their subscription counts
const joinedRooms = {}

// WebSocket connection instance
let connection = null

// Error handling and reconnection tracking
let hasShownError = false
let retryCount = 0
let reconnectDelay = INITIAL_RECONNECT_DELAY
let reconnectTimeout = null

// Queue to store operations that are pending due to an unhealthy connection
const pendingOperations = []

// Function to check if the WebSocket connection is healthy
// eslint-disable-next-line arrow-body-style
const isConnectionHealthy = () => {
  // WebSocket `readyState` 1 indicates an open connection
  return connection && connection.readyState === 1
}

// Enhanced message handler with AI agent support
const messageHandler = event => {
  const eventData = JSON.parse(event.data)

  // Emit events based on the message type
  switch (eventData.type) {
    case 'batch_status':
      bus.$emit('wsData/batchStatus', eventData.data)
      break
    case 'batch_status_tag':
      bus.$emit('wsData/batchStatusTag', eventData.data)
      break
    case 'email_batch_status_tag':
      bus.$emit('wsData/emailBatchStatusTag', eventData.data)
      break
    case 'template_batch_status_tag':
      bus.$emit('wsData/templateBatchStatusTag', eventData.data)
      break
    case 'timeline':
      bus.$emit('wsData/timelineStatus', eventData.data)
      break
    case 'train_batch_status_tag':
      bus.$emit('wsData/trainBatchStatusTag', eventData.data)
      break
    case 'ai_agent_response':
      bus.$emit('wsData/aiAgentResponse', eventData.data)
      break
    case 'editor_joined':
      bus.$emit('wsData/editorJoined', eventData)
      break
    case 'editor_left':
      bus.$emit('wsData/editorLeft', eventData)
      break
    default:
      break
  }
}

// Function to join a WebSocket room
const joinRoom = roomName => {
  if (!isConnectionHealthy()) {
    // If connection is unhealthy, queue the operation for later
    pendingOperations.push({
      action: 'joinRoom',
      roomName,
    })
    return
  }

  // Add the room to the joinedRooms tracker and send a join request if it's not already joined
  if (joinedRooms[roomName] === undefined) {
    joinedRooms[roomName] = 0
    connection.send(JSON.stringify({ type: 'join_room', room_name: roomName }))
  }
  joinedRooms[roomName] += 1
}

// Function to leave a WebSocket room
const leaveRoom = roomName => {
  if (!isConnectionHealthy()) {
    // If connection is unhealthy, queue the operation for later
    pendingOperations.push({
      action: 'leaveRoom',
      roomName,
    })
    return
  }

  // Decrement the subscription count and leave the room if no subscribers remain
  joinedRooms[roomName] -= 1
  if (joinedRooms[roomName] === 0) {
    connection.send(JSON.stringify({ type: 'leave_room', room_name: roomName }))
    delete joinedRooms[roomName]
  }
}

// Function to send messages through WebSocket (new addition)
const sendMessage = (message, messageType = 'ai_agent_consumer') => {
  if (!isConnectionHealthy()) {
    pendingOperations.push({
      action: 'sendMessage',
      message,
      messageType,
    })

    return
  }

  const payload = {
    type: messageType,
    data: message,
  }

  connection.send(JSON.stringify(payload))
}

// Function to send raw message (for presence and other custom types)
const sendRawMessage = messagePayload => {
  if (!isConnectionHealthy()) {
    pendingOperations.push({
      action: 'sendRawMessage',
      messagePayload,
    })
    return
  }

  try {
    if (messagePayload && (messagePayload.type === 'join_presence_room' || messagePayload.type === 'leave_presence_room')) {
      if (!messagePayload.tab_id) {
        try {
          const tabId = getTabId()
          const payloadWithTab = { ...messagePayload, tab_id: tabId }
          connection.send(JSON.stringify(payloadWithTab))
          return
        } catch (e) {
          // ignore
        }
      }
    }
  } catch (e) {
    // ignore
  }

  connection.send(JSON.stringify(messagePayload))
}

// Enhanced pending operations resolver with sendMessage support
const resolvePendingOperations = () => {
  pendingOperations.forEach(pendingOperation => {
    switch (pendingOperation.action) {
      case 'joinRoom':
        joinRoom(pendingOperation.roomName)
        break
      case 'leaveRoom':
        leaveRoom(pendingOperation.roomName)
        break
      case 'sendMessage':
        sendMessage(pendingOperation.message, pendingOperation.messageType)
        break
      case 'sendRawMessage':
        sendRawMessage(pendingOperation.messagePayload)
        break
      default:
        break
    }
  })
  pendingOperations.length = 0
}

// Function to create and initialize a WebSocket connection
// Create and initialize a WebSocket connection
const createConnection = () => {
  axios.get('/access_control/ws_ticket/')
    .then(response => {
      const wsTicket = response.data.ws_ticket
      const wsUrl = `${getEnv('VUE_APP_WEBSOCKET_URL')}?ws_ticket=${wsTicket}`

      connection = new WebSocket(wsUrl)

      // WebSocket event listeners
      connection.onopen = () => {
        resolvePendingOperations() // Process pending operations
        hasShownError = false // Reset error flag on success
        retryCount = 0 // Reset retry count
        reconnectDelay = INITIAL_RECONNECT_DELAY // Reset delay
      }

      // Event listener for incoming messages
      connection.onmessage = event => {
        messageHandler(event) // Process incoming messages
      }

      // Event listener for when the connection closes
      connection.onclose = event => {
        const isUnexpectedClose = !event.wasClean || event.code !== 1000
        if (isUnexpectedClose && retryCount < MAX_RETRIES) {
          retryCount += 1
          // Clear any existing timeout
          if (reconnectTimeout) clearTimeout(reconnectTimeout)
          // Reconnect with exponential backoff
          reconnectTimeout = setTimeout(() => {
            createConnection()
          }, reconnectDelay)
          // Increase delay for next retry (exponential backoff)
          reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY)
        } else if (retryCount >= MAX_RETRIES) {
          if (!hasShownError) {
            bus.$emit('wsError', 'WebSocket connection failed after multiple attempts')
            hasShownError = true
          }
        }
      }
    })
    .catch(() => {
      if (!hasShownError) {
        bus.$emit('wsError', 'Error fetching WebSocket ticket')
        hasShownError = true
      }

      // Optional retry limit:
      // if (retryCount >= MAX_RETRIES) return
      // retryCount+1

      // Note: We do not auto-retry here to avoid tight loops when auth is invalid.
      // The App component is responsible for calling WS.createConnection() when
      // the user is authenticated.
    })
}

// Function to close the WebSocket connection
const closeConnection = () => {
  // Clear any pending reconnection
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  // Reset retry count to prevent reconnection
  retryCount = MAX_RETRIES
  if (connection) {
    connection.close() // Close the connection
    connection = null
  }
}

// Exporting the enhanced WebSocket utility module
const WS = {
  createConnection, // Initialize a WebSocket connection
  closeConnection, // Close the WebSocket connection
  joinRoom, // Join a specific WebSocket room
  leaveRoom, // Leave a specific WebSocket room
  sendMessage, // New exported function
  sendRawMessage, // Send raw WebSocket messages
}

export default WS
