<template>
  <div>
    <!-- Error Alert - Show only when there's an error message -->
    <div v-if="isProjectAvailable && !showLoading">
      <b-alert
        variant="danger"
        show
      >
        <div class="alert-body">
          <p>
            {{ isProjectAvailable }}
          </p>

        </div>
      </b-alert>
    </div>

    <!-- Main Content - wrapped with overlay to prevent destroy/recreate cycle -->
    <b-overlay
      v-else
      :show="showLoading"
      spinner-variant="primary"
      opacity=".4"
      rounded="sm"
    >
      <div>
      <b-row>
        <b-col class="d-flex align-items-center">
          <h2 class="mb-0">
            Project : {{ project.name || '' }}
          </h2>
          <b-button
            variant="outline-secondary"
            class="ml-2"
            @click="$router.back()"
          >
            <feather-icon
              icon="ArrowLeftIcon"
              size="16"
              class="mr-50"
            />
            Back
          </b-button>
        </b-col>
        <b-col

          cols="12"
          md="6"
          class="d-flex align-items-center justify-content-end gap-3 mb-1 mb-md-0"
        >
          <div v-if="!['Data Assembly', 'Input Channel', 'Output Channel'].includes(tabs[currentTab])">
            <div
              v-if="tabs[currentTab] !== 'Project'"
              class="d-flex align-items-center justify-content-end gap-3 mb-1 mb-md-0"
            >
              <b-button
                v-if="tabs[currentTab] ==='Keys'"
                variant="outline-primary"
                @click="emitUploadModel"
              >
                Upload Data Model
              </b-button>
              <ImportExportProject
                :project="project"
                :export-settings-item="toCamelCase(tabs[currentTab])"
                partial-import
              />
              <b-button
                v-if="tabs[currentTab] === 'Doc Types' || tabs[currentTab] === 'Doctypes'"
                variant="outline-primary"
                class="mr-1"
                @click="importDoctypes"
              >
                Import Excel
              </b-button>
              <b-button
                variant="outline-primary"
                @click="addItem"
              >
                Add New
              </b-button>
            </div>
          </div>

          <b-button
            v-if="!['Input Channel', 'Output Channel'].includes(tabs[currentTab])"
            variant="primary"
            :disabled="isButtonDisabled"
            @click="save"
          >
            {{ tabs[currentTab] !== 'Project'? 'Save':'Update Project' }}
            <b-spinner
              v-if="loading || (tabs[currentTab] === 'Project' && projectFormState.submitting)"
              small
              label="Small Spinner"
            />
          </b-button>
        </b-col>
      </b-row>

      <div class="p-2">
        <b-tabs
          v-model="currentTab"
          pills
        >
          <b-tab
            title="Project"
            active
          >
            <b-card>
              <UpdateProjectForm
                :project="project"
                @form-state-changed="onProjectFormStateChanged"
              />
            </b-card>
          </b-tab>
          <b-tab
            title="Keys"
          >
            <b-card><ProjectKeysTable /></b-card>
          </b-tab>
          <!-- <b-tab title="Mapped Keys">
            <b-card><ProjectMappedKeysTable /></b-card>
          </b-tab> -->
          <b-tab title="Key Qualifiers">
            <b-card-text><ProjectKeyQualifier /></b-card-text>
          </b-tab>
          <b-tab title="Compound Keys">
            <b-card-text><ProjectCompoundKeys /> </b-card-text>
          </b-tab>
          <b-tab title="Doc Types">
            <b-card><ProjectDoctypeTable /></b-card>
          </b-tab>
          <b-tab title="Data Assembly">
            <b-card>
              <ProjectDataAssembly />
            </b-card>
          </b-tab>
          <b-tab title="Other Settings">
            <b-card><OtherSettingsIndex /></b-card>
          </b-tab>
          <b-tab title="Input Channel">
            <b-card><InputChannels /></b-card>
          </b-tab>
          <b-tab title="Output Channel">
            <b-card><OutputChannels /> </b-card>
          </b-tab>
          <b-tab title="AI Agents">
            <b-card><AgentsConfig /> </b-card>
          </b-tab>
        </b-tabs>
      </div>
      </div>
    </b-overlay>
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BButton,
  BCard,
  BCardText,
  BCol,
  BRow,
  BSpinner,
  BTab,
  BTabs,
  BOverlay,
  BAlert,
} from 'bootstrap-vue'

import { PresenceManager } from '@/utils/presence'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import WS from '@/utils/ws'
import ProjectCompoundKeys from './CompoundKeys/ProjectCompoundKeys.vue'
import ProjectDataAssembly from './DataAssembly/ProjectDataAssembly.vue'
import ProjectDoctypeTable from './Doctypes/ProjectDoctypeTable.vue'
import ImportExportProject from './ImportExportProject.vue'
import ProjectKeysTable from './Keys/ProjectKeysTable.vue'
// import ProjectMappedKeysTable from './MappedKeys/ProjectMappedKeysTable.vue'
import OtherSettingsIndex from './OtherSettings/OtherSettingsIndex.vue'
import ProjectKeyQualifier from './Qualifier/ProjectKeyQualifier.vue'
import UpdateProjectForm from './UpdateProjectForm.vue'
import InputChannels from './InputChannels/InputChanels.vue'
import OutputChannels from './OutputChannels/OutputChannels.vue'
import AgentsConfig from './Agents/AgentsConfig.vue'

export default {
  components: {
    BButton,
    BRow,
    BCol,
    BTabs,
    BTab,
    BCard,
    BCardText,
    BSpinner,
    ProjectKeysTable,
    // ProjectMappedKeysTable,
    ProjectDoctypeTable,
    ProjectKeyQualifier,
    ProjectCompoundKeys,
    ProjectDataAssembly,
    ImportExportProject,
    OtherSettingsIndex,
    UpdateProjectForm,
    BOverlay,
    BAlert,
    InputChannels,
    OutputChannels,
    AgentsConfig,
  },
  data() {
    return {
      currentTab: 0,
      tabs: ['Project', 'Keys', 'Key Qualifiers', 'Compound Keys', 'Doc Types', 'Data Assembly', 'Other Settings', 'Input Channel', 'Output Channel', 'AI Agents'],
      loading: false,
      projectFormState: {
        hasChanges: false,
        canSubmit: false,
        submitting: false,
      },
      isProjectAvailable: null,
      // Presence tracking
      presenceManager: null,
      activeEditors: [],
      initialActiveEditors: [], // Track who was here when you joined
      presenceToastId: null,
      currentUserId: null, // Store current user's ID
      currentTabId: null, // Store current tab ID
    }
  },
  computed: {
    keyItems() {
      return this.$store.getters['project/keyItems']
    },

    project() {
      return this.$store.getters['project/project']
    },

    showLoading() {
      return this.$store.getters['project/isProjectLoading']
    },

    isButtonDisabled() {
      if (this.tabs[this.currentTab] === 'Project') {
        // For Project tab, disable if no changes, can't submit, or is submitting
        return !this.projectFormState.canSubmit || this.projectFormState.submitting
      }
      // For other tabs, use existing loading state
      return this.loading
    },
  },
  created() {
    this.fetchProject()
  },
  async mounted() {
    // Initialize presence tracking
    await this.initializePresence()

    // Subscribe to WebSocket events via bus
    bus.$on('wsData/editorJoined', this.handleEditorJoined)
    bus.$on('wsData/editorLeft', this.handleEditorLeft)
  },
  async beforeDestroy() {
    // Reset project store to clear stale data
    this.$store.dispatch('project/resetProject')

    // Cleanup presence tracking
    await this.cleanupPresence()

    // Unsubscribe from WebSocket events
    bus.$off('wsData/editorJoined', this.handleEditorJoined)
    bus.$off('wsData/editorLeft', this.handleEditorLeft)
  },
  destroyed() {
    this.isProjectAvailable = null
  },
  methods: {
    emitUploadModel() {
      bus.$emit('project:upload-model')
    },
    addItem() {
      const tab = this.tabs[this.currentTab]
      switch (tab) {
        case 'Keys':
          bus.$emit('project:add-key')
          break
        // case 'Mapped Keys':
        //   bus.$emit('project:add-mapped-key')
        //   break
        case 'Doc Types':
        case 'Doctypes':
          bus.$emit('project:add-doc-type')
          break
        case 'Key Qualifiers':
          bus.$emit('project:add-key-qualifier')
          break
        case 'Compound Keys':
          bus.$emit('project:add-compound-key')
          break
        case 'Other Settings':
          bus.$emit('project:add-other-setting')
          break
        default:
          break
      }
    },

    importDoctypes() {
      bus.$emit('project:import-doctypes')
    },

    save() {
      if (this.tabs[this.currentTab] === 'Project') {
        // Trigger the project form submission via bus
        bus.$emit('project:update-project')
      } else {
        // Handle other tabs
        this.loading = true
        this.$store.dispatch('project/saveProject')
          .then(() => {
            this.$toast.success('Project Settings Updated Successfully')
            this.loading = false
          })
          .catch(err => {
            const errMsg = err.response?.data?.settings?.message || err.response?.data?.settings[0] || err.response?.data?.detail || 'Failed to update Project Settings'
            this.$toast.error(errMsg)
            this.loading = false
          })
      }
    },

    onProjectFormStateChanged(state) {
      this.projectFormState = { ...state }
    },

    toCamelCase(str) {
      if (!str) return ''
      const camel = str
        .replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) => (index === 0 ? word.toLowerCase() : word.toUpperCase()))
        .replace(/\s+/g, '')
      return camel.charAt(0).toLowerCase() + camel.slice(1)
    },

    updateProjectKeys(newItems) {
      if (!Array.isArray(newItems)) return
      this.$store.dispatch('project/updateProjectKeys', newItems)
    },

    async fetchProject() {
      // Reset error state when starting fetch
      this.isProjectAvailable = null

      try {
        await this.$store.dispatch('project/fetchProjectDetail', this.$route.params.id)
      } catch (error) {
        // Set error message
        this.isProjectAvailable = error?.response?.data?.detail || 'Failed to load project'
      }
    },

    // ===== PRESENCE TRACKING METHODS =====

    async initializePresence() {
      const projectId = this.$route.params.id
      if (!projectId) return

      try {
        // Import getTabId
        const { getTabId } = await import('@/utils/presence')
        this.currentTabId = getTabId()

        // Create presence manager
        this.presenceManager = new PresenceManager('project', projectId)

        // Start tracking
        const result = await this.presenceManager.start()

        // Store current user's ID from the response
        if (result.current_user_id) {
          this.currentUserId = result.current_user_id
        }

        // Set initial active editors (who were here when you joined)
        if (result.active_editors && result.active_editors.length > 0) {
          this.activeEditors = result.active_editors
          this.initialActiveEditors = [...result.active_editors] // Copy initial list
          this.showEditorsToast()
        }

        // Join WebSocket presence room
        WS.sendRawMessage({
          type: 'join_presence_room',
          resource_type: 'project',
          resource_id: projectId,
        })
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to initialize presence:', error)
      }
    },

    async cleanupPresence() {
      const projectId = this.$route.params.id

      // Hide toast
      this.hideEditorsToast()

      // Leave WebSocket room
      try {
        WS.sendRawMessage({
          type: 'leave_presence_room',
          resource_type: 'project',
          resource_id: projectId,
        })
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to leave presence room:', error)
      }

      // Stop presence manager
      if (this.presenceManager) {
        await this.presenceManager.stop()
        this.presenceManager = null
      }
    },

    formatEditorNames(editors) {
      if (!editors || editors.length === 0) return ''

      const names = editors.map(e => e.username)

      if (names.length === 1) {
        return names[0]
      } if (names.length === 2) {
        return `${names[0]} and ${names[1]}`
      }
      const lastIndex = names.length - 1
      const firstNames = names.slice(0, lastIndex).join(', ')
      return `${firstNames}, and ${names[lastIndex]}`
    },

    showEditorsToast() {
      if (!this.activeEditors || this.activeEditors.length === 0) {
        this.hideEditorsToast()
        return
      }

      // Sort editors by started_at to find the first one who joined
      const sortedEditors = [...this.activeEditors].sort((a, b) => new Date(a.started_at) - new Date(b.started_at))
      const firstEditorName = sortedEditors[0].username

      // Clear existing toast if any
      this.hideEditorsToast()

      // Show new toast
      this.presenceToastId = this.$toast(
        {
          component: ToastificationContent,
          props: {
            title: 'Concurrent Editing Warning',
            text: `${firstEditorName} is currently editing this Project`,
            icon: 'AlertCircleIcon',
            variant: 'warning',
            hideClose: true,
          },
        },
        {
          timeout: false, // No auto-dismiss
          closeButton: false, // No close button
          closeOnClick: false,
          position: 'top-center',
          hideProgressBar: true,
        },
      )
    },

    hideEditorsToast() {
      if (this.presenceToastId) {
        try {
          this.$toast.dismiss(this.presenceToastId)
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('[Presence] Error dismissing toast:', error)
        }
        this.presenceToastId = null
      } else {
        // Try to clear all toasts as fallback
        try {
          this.$toast.clear()
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('[Presence] Error clearing toasts:', error)
        }
      }
    },

    handleEditorJoined(event) {
      const data = event.data || event
      const projectId = this.$route.params.id

      // Only handle events for this project
      if (data.resource_type !== 'project' || String(data.resource_id) !== String(projectId)) {
        return
      }

      // Ignore if this is the current user's own join event (Fix #1)
      if (data.user_id === this.currentUserId && data.tab_id === this.currentTabId) {
        return
      }
      // Check if this user is already in the list
      const exists = this.activeEditors.some(
        e => e.user_id === data.user_id && e.tab_id === data.tab_id,
      )

      if (!exists) {
        // Add to current list but DON'T show in toast (Fix #2 - they joined after you)
        this.activeEditors.push({
          user_id: data.user_id,
          username: data.username,
          tab_id: data.tab_id,
        })
        // Don't call showEditorsToast() - we don't want to notify about new joiners
      }
    },

    handleEditorLeft(event) {
      const data = event.data || event
      const projectId = this.$route.params.id

      // Only handle events for this project
      if (data.resource_type !== 'project' || String(data.resource_id) !== String(projectId)) {
        return
      }
      // Remove from current list
      this.activeEditors = this.activeEditors.filter(
        e => !(e.user_id === data.user_id && e.tab_id === data.tab_id),
      )

      // Remove from initial list if present
      this.initialActiveEditors = this.initialActiveEditors.filter(
        e => !(e.user_id === data.user_id && e.tab_id === data.tab_id),
      )
      // If no initial editors remain, hide toast immediately
      if (this.initialActiveEditors.length === 0) {
        this.hideEditorsToast()
        return
      }

      // Check if any initial editors are still active
      const stillPresent = this.initialActiveEditors.filter(initial => this.activeEditors.some(current => current.user_id === initial.user_id && current.tab_id === initial.tab_id))

      if (stillPresent.length === 0) {
        this.hideEditorsToast()
      } else {
        // Refresh toast to show updated state (though message is generic)
        this.showEditorsToast()
      }
    },
  },
}
</script>
