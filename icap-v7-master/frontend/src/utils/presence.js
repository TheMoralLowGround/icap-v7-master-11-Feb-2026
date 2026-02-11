import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

/**
 * Editor presence API service
 * Handles tracking which users are editing Projects/Processes
 */

// Generate a unique tab ID for this browser tab
let tabId = sessionStorage.getItem('editor_tab_id')
if (!tabId) {
  tabId = uuidv4()
  sessionStorage.setItem('editor_tab_id', tabId)
}

export const getTabId = () => tabId

/**
 * Register presence when joining an editor
 * @param {string} resourceType - 'project' or 'process'
 * @param {string|number} resourceId - ID or name of the resource
 * @returns {Promise<{active_editors: Array}>}
 */
export const joinEditor = async (resourceType, resourceId) => {
  try {
    const response = await axios.post('/dashboard/presence/join/', {
      resource_type: resourceType,
      resource_id: resourceId,
      tab_id: tabId,
    })
    return response.data
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to join editor:', error)
    throw error
  }
}

/**
 * Unregister presence when leaving an editor
 * @param {string} resourceType - 'project' or 'process'
 * @param {string|number} resourceId - ID or name of the resource
 * @returns {Promise<{success: boolean}>}
 */
export const leaveEditor = async (resourceType, resourceId) => {
  try {
    const response = await axios.post('/dashboard/presence/leave/', {
      resource_type: resourceType,
      resource_id: resourceId,
      tab_id: tabId,
    })
    return response.data
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to leave editor:', error)
    throw error
  }
}

/**
 * Synchronously notify server that this tab is leaving the editor.
 * Uses navigator.sendBeacon when available and falls back to fetch with keepalive.
 * This is used for unload/refresh cases where async requests may be canceled.
 */
export const leaveEditorBeacon = (resourceType, resourceId) => {
  const url = '/dashboard/presence/leave/'
  const payload = JSON.stringify({ resource_type: resourceType, resource_id: resourceId, tab_id: tabId })

  // Prefer sendBeacon for reliability on unload
  if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
    try {
      const blob = new Blob([payload], { type: 'application/json' })
      return navigator.sendBeacon(url, blob)
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('Failed to send beacon:')
    }
  }

  try {
    fetch(url, {
      method: 'POST',
      body: payload,
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
    }).catch(() => {})
    return true
  } catch (e) {
    return false
  }
}

/**
 * Send heartbeat to keep presence alive
 * @param {string} resourceType - 'project' or 'process'
 * @param {string|number} resourceId - ID or name of the resource
 * @returns {Promise<{success: boolean}>}
 */
export const heartbeatEditor = async (resourceType, resourceId) => {
  try {
    const response = await axios.post('/dashboard/presence/heartbeat/', {
      resource_type: resourceType,
      resource_id: resourceId,
      tab_id: tabId,
    })
    return response.data
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to send heartbeat:', error)
    // Don't throw on heartbeat failure - just log it
    return { success: false }
  }
}

/**
 * Get current editor status
 * @param {string} resourceType - 'project' or 'process'
 * @param {string|number} resourceId - ID or name of the resource
 * @returns {Promise<{active_editors: Array}>}
 */
export const getEditorStatus = async (resourceType, resourceId) => {
  try {
    const response = await axios.get('/dashboard/presence/status/', {
      params: {
        resource_type: resourceType,
        resource_id: resourceId,
      },
    })
    return response.data
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to get editor status:', error)
    throw error
  }
}

/**
 * Force-remove a presence entry for a reloaded tab (called by new tab instance)
 */
export const cleanupReloadedPresence = async (resourceType, resourceId) => {
  try {
    const response = await axios.post('/dashboard/presence/cleanup_reloaded/', {
      resource_type: resourceType,
      resource_id: resourceId,
      tab_id: tabId,
    })
    return response.data
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to cleanup reloaded presence:', error)
    return { success: false }
  }
}

/**
 * Presence manager class to handle lifecycle of editor presence
 */
export class PresenceManager {
  constructor(resourceType, resourceId) {
    this.resourceType = resourceType
    this.resourceId = resourceId
    this.heartbeatInterval = null
    this.isActive = false
    this.autoJoinedOnReload = false
    this.autoTakeInterval = null
  }

  /**
   * Start presence tracking
   */
  async start() {
    if (this.isActive) return null

    const reloadFlagKey = `editor_reloading_${tabId}`
    const hadReloadFlag = (() => {
      try {
        return sessionStorage.getItem(reloadFlagKey) === '1'
      } catch (e) {
        return false
      }
    })()

    try {
      if (hadReloadFlag) {
        // Clear the flag and ensure previous presence is removed
        try {
          sessionStorage.removeItem(reloadFlagKey)
        } catch (e) {
          // eslint-disable-next-line no-console
          console.error('Failed to remove reload flag from sessionStorage:', e)
        }

        try {
          leaveEditorBeacon(this.resourceType, this.resourceId)
        } catch (e) {
          // ignore
        }

        try {
          await cleanupReloadedPresence(this.resourceType, this.resourceId)
        } catch (e) {
          // ignore
        }
      }

      const result = await joinEditor(this.resourceType, this.resourceId)
      this.isActive = true

      // Start heartbeat every 30 seconds
      this.heartbeatInterval = setInterval(() => {
        heartbeatEditor(this.resourceType, this.resourceId)
      }, 30000)

      // Add unload handler to ensure presence is removed on page refresh/close
      this.unloadHandler = () => {
        try {
          // Mark that this tab is reloading so the new page won't auto-join
          try {
            sessionStorage.setItem(`editor_reloading_${tabId}`, '1')
          } catch (e) {
            // ignore
          }
          leaveEditorBeacon(this.resourceType, this.resourceId)
        } catch (e) {
          // ignore
        }
      }
      if (typeof window !== 'undefined' && this.unloadHandler) {
        window.addEventListener('beforeunload', this.unloadHandler)
        window.addEventListener('pagehide', this.unloadHandler)
      }

      this.autoJoinedOnReload = true
      return result
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to start presence:', error)
      throw error
    }
  }

  /**
   * Stop presence tracking
   */
  async stop() {
    if (!this.isActive) return

    // Clear heartbeat
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
    // Remove unload handlers
    try {
      if (typeof window !== 'undefined' && this.unloadHandler) {
        window.removeEventListener('beforeunload', this.unloadHandler)
        window.removeEventListener('pagehide', this.unloadHandler)
        this.unloadHandler = null
      }
    } catch (e) {
      // ignore
    }

    try {
      await leaveEditor(this.resourceType, this.resourceId)
      this.isActive = false
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to stop presence:', error)
      // Still mark as inactive even if API call fails
      this.isActive = false
    }

    // clear auto-take interval if any
    try {
      if (this.autoTakeInterval) {
        clearInterval(this.autoTakeInterval)
        this.autoTakeInterval = null
      }
    } catch (e) {
      // ignore
    }
  }

  /**
   * Get current status
   */
  async getStatus() {
    return getEditorStatus(this.resourceType, this.resourceId)
  }
}

export default {
  joinEditor,
  leaveEditor,
  heartbeatEditor,
  getEditorStatus,
  getTabId,
  PresenceManager,
}
