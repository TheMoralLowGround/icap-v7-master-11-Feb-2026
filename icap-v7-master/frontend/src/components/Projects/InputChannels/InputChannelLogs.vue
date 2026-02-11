<template>
  <div class="modal-content-container">
    <!-- Error Alert -->
    <b-alert
      v-if="error"
      variant="danger"
      :show="true"
      class="mb-3"
    >
      <div class="alert-body">
        <p>{{ error }}</p>
      </div>
    </b-alert>

    <!-- List displaying data -->
    <div class="list-container">
      <!-- Loading Spinner -->
      <div
        v-if="loading"
        class="text-center m-3 loading-spinner"
      >
        <b-spinner
          variant="primary"
          label="Loading..."
        />
        <p class="mt-2 text-muted">
          Loading logs...
        </p>
      </div>

      <!-- No data available message -->
      <div
        v-if="!loading && data.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>

      <!-- Bootstrap List Group -->
      <b-list-group
        v-if="!loading && data.length > 0"
        flush
      >
        <b-list-group-item
          v-for="item in sortedData"
          :key="item.id"
          class="log-item"
        >
          <!-- First line: Error message or success message -->
          <div class="error-line">
            <div
              v-if="item.status === 'error'"
              class="error-message"
            >
              <span class="error-text">
                {{ item.message }}
              </span>
            </div>
            <div
              v-else
              class="success-message"
            >
              <span class="success-text">
                <feather-icon
                  icon="CheckCircleIcon"
                  size="16"
                  class="mr-1"
                />
                Parsed successfully
              </span>
            </div>
          </div>

          <!-- Second line: Status and Time -->
          <div
            v-if="item.batch_id"
            class="mb-1"
          >
            <strong>Batch ID</strong>: {{ item.batch_id }}
          </div>
          <div class="status-time-line">
            <div class="status-section">
              <span class="status-label">Status:</span>
              <b-badge
                :variant="getStatusVariant(item.status)"
                class="status-badge"
              >
                {{ item.status }}
              </b-badge>
            </div>
            <div class="time-section">
              <small class="text-muted">{{ formattedDate(item.updated_at) }}</small>
            </div>
          </div>
          <div class="mt-1 mb-1">
            {{ item.file_name }}
          </div>

          <!-- Remarks section for error status -->
          <div
            v-if="item.status === 'error' && item.remarks"
            class="remarks-section"
          >
            <h6 class="mt-1">
              Error Details:
            </h6>
            <ul>
              <li v-if="parseRemarks(item.remarks).code">
                <b>Code:</b> {{ parseRemarks(item.remarks).code }}
              </li>
              <li v-if="parseRemarks(item.remarks).innerError && parseRemarks(item.remarks).innerError.code">
                <!-- <b>Inner Error Code:</b> {{ parseRemarks(item.remarks).innerError.code }} -->
              </li>
              <li v-if="parseRemarks(item.remarks).message">
                <b>Message:</b> {{ parseRemarks(item.remarks).message }}
              </li>
            </ul>
            <a
              href="javascript:void(0)"
              @click="toggleJsonDisplay(item.id)"
            >
              {{ jsonDisplayStates[item.id] ? 'Hide JSON' : 'View JSON' }}
            </a> |
            <a
              href="javascript:void(0)"
              @click="downloadJson(item.remarks, item.id)"
            >
              Download JSON
            </a>
            <b-spinner
              v-if="downloadLoading[item.id]"
              small
              label="Small Spinner"
            />
            <div
              v-if="jsonDisplayStates[item.id]"
              class="mt-1"
            >
              <vue-json-pretty
                :data="parseRemarks(item.remarks)"
                :show-icon="true"
                :virtual="true"
                :height="150"
              />
            </div>
          </div>
        </b-list-group-item>
      </b-list-group>
    </div>
  </div>
</template>

<script>
import {
  BSpinner,
  BAlert,
  BListGroup,
  BListGroupItem,
  BBadge,
} from 'bootstrap-vue'
import FeatherIcon from '@core/components/feather-icon/FeatherIcon.vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'
import exportFromJSON from 'export-from-json'

export default {
  components: {
    BSpinner,
    BAlert,
    BListGroup,
    BListGroupItem,
    BBadge,
    FeatherIcon,
    VueJsonPretty,
  },
  props: {
    title: {
      type: String,
      required: false,
      default: 'Channel Logs',
    },
    service: {
      type: String,
      required: true,
    },
    project: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      data: [],
      error: null,
      expandedErrors: {}, // Track which error messages are expanded
      jsonDisplayStates: {}, // Track JSON display state per item
      downloadLoading: {}, // Track download loading state per item
      sortBy: 'updated_at',
      sortDesc: true,
    }
  },
  computed: {
    sortedData() {
      if (!this.sortBy) return this.data

      return [...this.data].sort((a, b) => {
        let aVal = a[this.sortBy]
        let bVal = b[this.sortBy]

        if (aVal === null || aVal === undefined) aVal = ''
        if (bVal === null || bVal === undefined) bVal = ''

        if (this.sortBy === 'created_at' || this.sortBy === 'updated_at') {
          aVal = new Date(aVal).getTime()
          bVal = new Date(bVal).getTime()
        } else {
          aVal = String(aVal).toLowerCase()
          bVal = String(bVal).toLowerCase()
        }

        if (aVal < bVal) return this.sortDesc ? 1 : -1
        if (aVal > bVal) return this.sortDesc ? -1 : 1
        return 0
      })
    },
  },
  async mounted() {
    await this.showLogs()
  },
  methods: {
    async showLogs() {
      this.loading = true
      this.error = null

      try {
        const res = await this.$store.dispatch('project/getInputChannelLogs', {
          service: this.service,
          project: this.project,
        })
        this.data = res.data || []
      } catch (error) {
        this.error = error?.response?.data?.detail || error?.message || 'Failed to load channel logs'
        this.data = []
      } finally {
        this.loading = false
      }
    },
    truncateError(error) {
      if (!error) return ''
      if (error.length <= 100) return error
      return `${error.substring(0, 100)}...`
    },
    toggleError(id) {
      this.$set(this.expandedErrors, id, !this.expandedErrors[id])
    },
    async refresh() {
      await this.showLogs()
    },
    formattedDate(dateString) {
      const date = new Date(dateString)
      return `${date.toLocaleDateString('en-GB')} ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`
    },
    getStatusVariant(status) {
      switch (status?.toLowerCase()) {
        case 'success':
        case 'completed':
          return 'success'
        case 'error':
        case 'failed':
          return 'danger'
        case 'pending':
        case 'processing':
          return 'warning'
        default:
          return 'primary'
      }
    },
    parseRemarks(remarks) {
      if (!remarks) return {}

      try {
        // Convert Python-style dict string to JSON
        const validJson = remarks
          .replace(/'/g, '"')
          .replace(/\\"/g, "'")
        return JSON.parse(validJson) || {}
      } catch (e) {
        return { message: remarks }
      }
    },
    toggleJsonDisplay(id) {
      this.$set(this.jsonDisplayStates, id, !this.jsonDisplayStates[id])
    },
    downloadJson(remarks, id) {
      try {
        this.$set(this.downloadLoading, id, true)
        const parsed = this.parseRemarks(remarks)
        // const parsed = JSON.parse(remarks)
        if (parsed && Object.keys(parsed).length) {
          exportFromJSON({
            data: parsed,
            fileName: `remarks-${id}`,
            exportType: 'json',
          })
        } else {
          this.$bvToast.toast('No valid data to download', {
            title: 'Error',
            variant: 'danger',
            solid: true,
          })
        }
      } catch (error) {
        this.$bvToast.toast('Failed to download JSON', {
          title: 'Error',
          variant: 'danger',
          solid: true,
        })
      } finally {
        this.$set(this.downloadLoading, id, false)
      }
    },
  },
}
</script>

<style scoped>
/* List container - scrollable */
.list-container {
  flex: 1;
  overflow-y: auto;
  max-height: calc(80vh - 180px);
}

/* List item styling */
.log-item {
  border: none !important;
  border-bottom: 1px solid #dee2e6 !important;
}

.log-item:last-child {
  border-bottom: none !important;
}

/* Error/Success line styling */
.error-line {
  margin-bottom: 0.5rem;
}

.error-message {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.error-text {
  color: #dc3545;
  font-weight: 500;
  line-height: 1.4;
  word-break: break-word;
}

.success-message {
  display: flex;
  align-items: center;
}

.success-text {
  color: #28a745;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.error-toggle-button {
  padding: 0 0.25rem;
  font-size: 0.875rem;
  line-height: 1.2;
  text-decoration: underline;
  white-space: nowrap;
}

/* Status and time line styling */
.status-time-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.875rem;
}

.status-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-label {
  color: #6c757d;
  font-weight: 500;
}

.status-badge {
  font-size: 0.75rem;
}

.time-section {
  display: flex;
  align-items: center;
}

/* Remarks section styling */
.remarks-section {
  margin-top: 0.5rem;
}

.remarks-section ul {
  list-style: none;
  padding-left: 0;
}

.remarks-section li {
  margin-bottom: 0.25rem;
}

.remarks-section a {
  font-size: 0.875rem;
  margin-right: 0.5rem;
}

/* JSON pretty display */
.vue-json-pretty {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

/* Loading spinner */
.loading-spinner {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Responsive design */
@media (max-width: 768px) {
  .status-time-line {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .error-message {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
