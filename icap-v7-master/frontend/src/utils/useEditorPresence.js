/**
 * Vue composable for editor presence management
 * Provides toast notifications and presence tracking
 */

import { ref, onMounted, onBeforeUnmount } from '@vue/composition-api'
import { PresenceManager, getTabId } from '@/utils/presence'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export function useEditorPresence(resourceType, resourceId, vue) {
  const activeEditors = ref([])
  const initialActiveEditors = ref([]) // Track who was here when you joined
  const presenceManager = ref(null)
  const toastId = ref(null)
  const currentUserId = ref(null) // Store current user's ID
  const currentTabId = getTabId() // Get current tab ID

  /**
   * Hide the editors toast
   */
  const hideEditorsToast = () => {
    if (toastId.value) {
      vue.$toast.dismiss(toastId.value)
      toastId.value = null
    }
  }
  /**
   * Show persistent toast notification
   */
  const showEditorsToast = editors => {
    if (!editors || editors.length === 0) {
      hideEditorsToast()
      return
    }

    const resourceTypeLabel = resourceType === 'project' ? 'Project' : 'Process'

    // Sort editors by started_at to find the first one who joined
    const sortedEditors = [...editors].sort((a, b) => new Date(a.started_at) - new Date(b.started_at))
    const firstEditorName = sortedEditors[0].username

    // Clear existing toast if any
    hideEditorsToast()

    // Show new toast
    toastId.value = vue.$toast(
      {
        component: ToastificationContent,
        props: {
          title: 'Concurrent Editing Warning',
          text: `${firstEditorName} is currently editing this ${resourceTypeLabel}`,
          icon: 'AlertCircleIcon',
          variant: 'warning',
        },
      },
      {
        timeout: false, // No auto-dismiss
        closeButton: false, // No close button
        position: 'top-center',
        hideProgressBar: true,
      },
    )
  }

  /**
   * Update active editors list and toast
   */
  const updateActiveEditors = editors => {
    activeEditors.value = editors
    showEditorsToast(editors)
  }

  /**
   * Handle editor joined event
   */
  const handleEditorJoined = data => {
    // Ignore if this is the current user's own join event
    if (data.user_id === currentUserId.value && data.tab_id === currentTabId) {
      return
    }

    // Check if this user is already in the list
    const exists = activeEditors.value.some(
      e => e.user_id === data.user_id && e.tab_id === data.tab_id,
    )

    if (!exists) {
      // Add to current list but DON'T show in toast
      activeEditors.value.push({
        user_id: data.user_id,
        username: data.username,
        tab_id: data.tab_id,
      })
    }
  }

  /**
   * Handle editor left event
   */
  const handleEditorLeft = data => {
    // Remove from current list
    activeEditors.value = activeEditors.value.filter(
      e => !(e.user_id === data.user_id && e.tab_id === data.tab_id),
    )

    // Remove from initial list if present
    initialActiveEditors.value = initialActiveEditors.value.filter(
      e => !(e.user_id === data.user_id && e.tab_id === data.tab_id),
    )

    // Only show toast for initial editors (who were here when you joined)
    if (initialActiveEditors.value.length === 0) {
      hideEditorsToast()
    } else {
      // Show only initial editors who are still present
      const stillPresent = initialActiveEditors.value.filter(initial => activeEditors.value.some(current => current.user_id === initial.user_id && current.tab_id === initial.tab_id))
      if (stillPresent.length === 0) {
        hideEditorsToast()
      } else {
        showEditorsToast(stillPresent)
      }
    }
  }

  /**
   * Initialize presence tracking
   */
  const initializePresence = async () => {
    try {
      // Create presence manager
      presenceManager.value = new PresenceManager(resourceType, resourceId)

      // Start tracking
      const result = await presenceManager.value.start()

      // Store current user's ID from the response
      if (result.current_user_id) {
        currentUserId.value = result.current_user_id
      }

      // Set initial active editors (who were here when you joined)
      if (result.active_editors && result.active_editors.length > 0) {
        activeEditors.value = result.active_editors
        initialActiveEditors.value = [...result.active_editors] // Copy initial list
        showEditorsToast(activeEditors.value) // Warn about existing editors
      }

      // Subscribe to WebSocket events
      if (vue.$socket) {
        vue.$socket.client.send(JSON.stringify({
          type: 'join_presence_room',
          resource_type: resourceType,
          resource_id: resourceId,
          tab_id: currentTabId,
        }))
      }

      return result
    } catch (error) {
      return null
    }
  }

  /**
   * Cleanup presence tracking
   */
  const cleanupPresence = async () => {
    // Hide toast
    hideEditorsToast()

    // Leave WebSocket room
    if (vue.$socket) {
      try {
        vue.$socket.client.send(JSON.stringify({
          type: 'leave_presence_room',
          resource_type: resourceType,
          resource_id: resourceId,
          tab_id: currentTabId,
        }))
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to leave presence room:', error)
      }
    }

    // Stop presence manager
    if (presenceManager.value) {
      await presenceManager.value.stop()
      presenceManager.value = null
    }
  }

  // Lifecycle hooks
  onMounted(() => {
    initializePresence()
  })

  onBeforeUnmount(() => {
    cleanupPresence()
  })

  return {
    activeEditors,
    initializePresence,
    cleanupPresence,
    handleEditorJoined,
    handleEditorLeft,
    updateActiveEditors,
  }
}

export default useEditorPresence
