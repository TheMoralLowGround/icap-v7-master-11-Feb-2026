<template>
  <app-timeline-item
    :variant="apptimeColorVarient"
    :is-agent="getIsAgent(item.remarks) || false"
  >
    <div class="d-flex flex-sm-row flex-column flex-wrap justify-content-between mb-sm-0">
      <h6>{{ item.message }}</h6>
      <small class="text-muted">{{ formattedDate(item.event_time) }}</small>
    </div>
    <div class="d-flex flex-sm-row flex-column flex-wrap justify-content-end mb-sm-0">
      <small
        v-if="timeDifference !== null"
        class="text-muted"
      >
        TD: {{ timeDifference }}
      </small>
    </div>
    <template v-if="item.action === 'download_output_json'">
      <b-button
        variant="primary"
        :disabled="loading"
        size="sm"
        @click="downloadJSON('output', '')"
      >
        Download Output JSON
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
    <template v-if="item.action === 'download_automated_table_model_json'">
      <b-button
        variant="primary"
        :disabled="loading"
        size="sm"
        @click="downloadJSON('automated_table_model', '')"
      >
        Download Automated Table Model JSON
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
    <template v-else-if="item.action === 'download_djson_excel'">
      <b-button
        variant="primary"
        :disabled="loading"
        size="sm"
        @click="downloadExcel()"
      >
        Download DataJson Excel
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
    <template v-else-if="item.action === 'download_definition_fields_json'">
      <b-button
        variant="primary"
        :disabled="loading"
        size="sm"
        @click="downloadJSON('definition_fields', item.remarks ? item.remarks.replace('filename:', ''): '')"
      >
        Download Definition Fields JSON
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
    <template v-else-if="item.action === 'display_subprocess_messages' || item.action === 'display_docbuilder_response'">
      <div>
        <li
          v-for="(logItem, index) of getSubMessagesForDisplay(item.remarks)"
          :key="index"
        >
          <b
            :class="{
              'text-warning': logItem.code !== 200,
              'text-danger': (logItem.message && logItem.message.includes && logItem.message.includes('Fail')) || (item.remarks && item.remarks.includes && item.remarks.includes('fail'))
            }"
          >{{ logItem.module }}</b> -
          <span style="white-space: pre-wrap">{{ logItem.message }}</span>
        </li>
      </div>
    </template>
    <template v-else-if="item.action === 'display_key_values'">
      <div>
        <li
          v-for="(value, key) of JSON.parse(item.remarks)"
          :key="key"
        >
          <b>{{ key }}</b> - {{ value }}
        </li>
      </div>
    </template>
    <template v-else-if="item.action === 'display_table'">
      <div v-if="item.remarks && JSON.parse(item.remarks).length > 0">
        <b-table
          class="table"
          :items="JSON.parse(item.remarks)"
          :columns="JSON.parse(item.remarks)[0].keys"
          :small="true"
          :bordered="true"
        />
      </div>
    </template>
    <template v-else-if="item.action === 'display_json'">
      <div>
        <div v-if="item.sub_message">
          {{ item.sub_message }}
        </div>
        <a
          href="javascript:void(0)"
          @click="toogleDisplayJson"
        >
          {{ jsonLinkText }}
        </a> |
        <a
          href="javascript:void(0)"
          @click="downloadLocalJSON(JSON.parse(item.remarks))"
        >
          Download JSON
        </a>
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </div>
      <div
        v-if="jsonDisplayed"
      >
        <div class="json-pretty-container">
          <vue-json-pretty
            :data="JSON.parse(item.remarks)"
            :show-icon="true"
          />
        </div>
      </div>
    </template>
    <template v-else-if="item.action === 'display_paginated_json'">
      <div>
        <div v-if="item.sub_message">
          {{ item.sub_message }}
        </div>
        <a
          href="javascript:void(0)"
          @click="toogleDisplayJson"
        >
          {{ jsonLinkText }}
        </a> |
        <a
          href="javascript:void(0)"
          @click="downloadLocalJSON(parsedRemarks)"
        >
          Download JSON
        </a>
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </div>
      <div
        v-if="jsonDisplayed"
      >
        <div>
          <vue-json-pretty
            :data="paginatedRemarks"
            :show-icon="true"
            :virtual="true"
          />
          <div class="pagination-container">
            <div class="page-jump-container">
              <label for="page-jump">Go to Page:</label>
              <input
                id="page-jump"
                v-model.number="inputPage"
                type="number"
                min="1"
                :max="totalPages"
                @keyup.enter="jumpToPage"
              >
              <button
                class="go-button"
                @click="jumpToPage"
              >
                Go
              </button>
            </div>
            <b-pagination
              v-model="currentPage"
              :total-rows="parsedRemarks.length"
              :per-page="itemsPerPage"
              aria-controls="remarks-json"
            />
          </div>
        </div>
      </div>
    </template>
    <template v-else-if="item.action === 'display_error'">
      <div>
        <pre class="json-pretty">{{ formattedMessage }}</pre>
        <div v-if="item.sub_message">
          {{ item.sub_message }}
        </div>
        <a
          href="javascript:void(0)"
          @click="toogleDisplayJson"
        >
          {{ jsonLinkText }}
        </a> |
        <a
          href="javascript:void(0)"
          @click="downloadLocalJSON(JSON.parse(item.remarks))"
        >
          Download JSON
        </a>
        <b-spinner
          v-if="loading"
          small
          label="Small Spinner"
        />
      </div>
      <div
        v-if="jsonDisplayed"
      >
        <pre class="json-pretty">{{ formattedTraceback }}</pre>
      </div>
    </template>
    <p v-else-if="item.remarks">
      {{ item.remarks }}
    </p>
  </app-timeline-item>
</template>

<script>
import axios from 'axios'
import AppTimelineItem from '@core/components/app-timeline/AppTimelineItem.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import {
  BSpinner, BButton, BTable, BPagination,
} from 'bootstrap-vue'
import exportFromJSON from 'export-from-json'
import download from 'downloadjs'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

export default {
  components: {
    AppTimelineItem,
    BSpinner,
    BButton,
    BTable,
    VueJsonPretty,
    BPagination,
  },
  props: {
    batchId: { type: String, required: true },
    item: { type: Object, required: true },
    timeDifference: { type: String, default: null },
  },
  data() {
    return {
      loading: false,
      jsonDisplayed: false,
      jsonLinkText: 'View JSON',
      currentPage: 1,
      itemsPerPage: 1,
      inputPage: 1,
      transactionRemarks: [],
    }
  },
  computed: {
    apptimeColorVarient() {
      if (this.item.status === 'failed' || (this.item.remarks && this.item.remarks?.toLowerCase()?.includes('fail'))) {
        return 'danger'
      }
      return ['warning', 'incomplete'].includes(this.item.status) ? 'warning' : 'success'
    },
    formattedTraceback() {
      return JSON.parse(this.item.remarks)?.traceback || ''
    },
    formattedMessage() {
      return JSON.parse(this.item.remarks)?.message || ''
    },
    totalPages() {
      return Math.ceil(this.parsedRemarks.length / this.itemsPerPage)
    },
    parsedRemarks() {
      return this.transactionRemarks.map(remark => (typeof remark === 'object' ? remark : JSON.parse(remark)))
    },
    paginatedRemarks() {
      return this.parsedRemarks.slice((this.currentPage - 1) * this.itemsPerPage, this.currentPage * this.itemsPerPage)
    },
  },
  methods: {
    getIsAgent(remarks) {
      try {
        if (!remarks) return false

        const parsed = JSON.parse(remarks)
        return parsed && typeof parsed === 'object' && parsed.is_agent === true
      } catch (error) {
        return false
      }
    },
    formattedDate(dateString) {
      const date = new Date(dateString)
      return `${date.toLocaleDateString('en-GB')} ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`
    },
    async downloadJSON(fileType, fileName) {
      try {
        this.loading = true
        const { data } = await axios.get('/retrive_json/', { params: { batch_id: this.batchId, file_type: fileType, file_name: fileName } })
        exportFromJSON({ data, fileName: `${fileType}-${this.batchId}`, exportType: 'json' })
      } catch (error) {
        this.showErrorToast(error)
      } finally {
        this.loading = false
      }
    },
    async downloadExcel() {
      try {
        this.loading = true
        const { data, headers } = await axios.get('/download_djson_excel/', { params: { batch_id: this.batchId }, responseType: 'blob' })
        download(data, `djson-${this.batchId}.xlsx`, headers['content-type'])
      } catch (error) {
        this.showErrorToast(error)
      } finally {
        this.loading = false
      }
    },
    async downloadLocalJSON(data) {
      try {
        this.loading = true

        // If the action is 'display_paginated_json', fetch the JSON data first
        if (this.item.action === 'display_paginated_json') {
          await this.getJson()
          // eslint-disable-next-line no-param-reassign
          data = this.parsedRemarks // Update the data with the fetched parsedRemarks
        }

        // Check if data is valid and not empty
        if (data && (Array.isArray(data) ? data.length : Object.keys(data).length)) {
          exportFromJSON({ data, fileName: 'AIDB_JSON', exportType: 'json' })
        } else {
          this.showToast('Data is empty', 'warning')
        }
      } catch (error) {
        this.showErrorToast(error)
      } finally {
        this.loading = false
      }
    },
    toogleDisplayJson() {
      this.jsonDisplayed = !this.jsonDisplayed
      if (this.jsonDisplayed) {
        if (this.item.action === 'display_paginated_json') {
          this.getJson()
        }
        this.jsonLinkText = 'Hide JSON'
      } else {
        this.jsonLinkText = 'View JSON'
      }
    },
    async getJson() {
      try {
        this.loading = true
        const messageMap = [
          ['Shipment-Create API call was partially failed', 'api', 'failed'],
          ['Shipment-Create API call was failed', 'api', 'failed'],
          ['Time Stamp API call was successful', 'timestamp_api', 'success'],
          ['Time Stamp API call was partially successful', 'timestamp_api', 'success'],
          ['Time Stamp API call was failed', 'timestamp_api', 'failed'],
          ['Uploading document to CW1 edoc was successful', 'doc', 'success'],
          ['Uploading document to CW1 edoc was failed', 'doc', 'failed'],
        ]

        let msgType = 'api'
        let msgStatus = 'success'

        const match = messageMap.find(([msg]) => this.item.message.includes(msg))

        if (match) {
          [, msgType, msgStatus] = match
        }

        const isFirstEndpoint = this.item.message.includes('Transaction result(s)') || this.item.message.includes('Calling Shipment-Create API to send payload')
        const params = isFirstEndpoint
          ? { email_batch_id: this.batchId, ...(this.item.message.includes('Calling Shipment-Create API to send payload') && { type: 'payload' }) }
          : { email_batch_id: this.batchId, type: msgType, status: msgStatus }
        const endpoint = isFirstEndpoint ? '/get_assembled_results/' : '/get_api_responses/'
        const { data } = await axios.get(endpoint, { params })
        this.transactionRemarks = [...data]
      } catch (error) {
        this.showErrorToast(error)
      } finally {
        this.loading = false
      }
    },
    jumpToPage() {
      if (this.inputPage < 1 || this.inputPage > this.totalPages) {
        this.showToast(`Page number must be between 1 and ${this.totalPages}`, 'danger')
      } else {
        this.currentPage = this.inputPage
      }
    },
    showToast(title, variant) {
      this.$toast({ component: ToastificationContent, props: { title, icon: 'AlertTriangleIcon', variant } })
    },
    showErrorToast(error) {
      this.showToast(error?.response?.data?.detail || 'Failed to process request', 'danger')
    },
    // NEW METHOD: Only addition to handle the new backend format
    getSubMessagesForDisplay(remarks) {
      try {
        if (!remarks) return []

        const parsed = JSON.parse(remarks)

        // Handle new format for display_subprocess_messages: {sub_messages: [...], is_agent: boolean}
        if (parsed && typeof parsed === 'object' && parsed.sub_messages && Array.isArray(parsed.sub_messages)) {
          return parsed.sub_messages
        }

        // Handle old format: direct array (for backward compatibility)
        if (Array.isArray(parsed)) {
          return parsed
        }

        return []
      } catch (error) {
        // console.error('Error parsing remarks for subprocess messages:', error)
        return []
      }
    },
  },
}
</script>
<style scoped>
.json-pretty {
  background-color: #f0f0f0; /* Light grey background for JSON block */
  padding: 10px;
  border-radius: 5px;
  color: #388e3c;
  font-family: monospace; /* Use monospace for better JSON display */
  white-space: pre-wrap; /* Preserve new lines */
  word-break: keep-all; /* Prevent word breaking */
  overflow-wrap: normal; /* Prevent word wrapping */
  overflow: auto;
  font-size: 14px;
}

/* vue-json-pretty word wrap styles */
::v-deep .vjs-tree {
  overflow-x: hidden !important;
}

::v-deep .vjs-tree-node {
  white-space: pre-wrap !important;
  word-break: break-word !important;
  overflow-wrap: break-word !important;
}

::v-deep .vjs-value {
  white-space: pre-wrap !important;
  word-break: break-word !important;
  overflow-wrap: break-word !important;
}

::v-deep .vjs-key {
  white-space: nowrap !important;
}

.json-pretty::selection {
  background-color: #388e3c;
  color: #fff;
}

.json-pretty span {
  font-weight: bold;
}

.json-pretty .brace {
  color: #d32f2f; /* Color for braces */
}

.json-pretty .key {
  color: #1976d2; /* Color for JSON keys */
}

.json-pretty .string {
  color: #388e3c; /* Color for strings */
}

.json-pretty .number {
  color: #f57c00; /* Color for numbers */
}

.json-pretty .boolean {
  color: #d32f2f; /* Color for booleans */
}

.json-pretty .null {
  color: #757575; /* Color for null values */
}

.json-pretty-container {
  max-height: 400px;
  overflow-y: auto;
}

.pagination-container {
  display: flex;
  /* flex-direction: column; */
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.page-jump-container {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.page-jump-container label {
  margin-right: 8px;
}

.page-jump-container input {
  width: 60px;
  margin-right: 8px;
  text-align: center;
}

.go-button {
  padding: 3px 12px;
  background-color: #7367f0;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.go-button:hover {
  background-color: #5b54c8; /* Darker shade on hover */
}

.go-button:active {
  background-color: #443ea1; /* Even darker shade on click */
}

.go-button:focus {
  outline: none;
  box-shadow: 0 0 4px #7367f0;
}
</style>
