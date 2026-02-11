<template>
  <div>
    <div class="mb-4">
      <h5>
        Base URL
      </h5>
      <code>{{ getBaseUrl }}</code>
      <h5 class="mt-2">
        Start Training Process API
      </h5>

      <div>
        <div class="d-flex align-items-center mb-3">
          <BBadge
            variant="info"
            class="mr-1 px-1"
          >
            POST
          </BBadge>
          <code>/api/pipeline/process_training/</code>
        </div>
        <h5 class="mb-2">
          Body Parameters
        </h5>
        <b-table
          bordered
          small
          responsive
          :items="requestFields"
          :fields="requestFieldsMeta"
          head-row-variant="light"
          thead-class="text-center"
        >
          <!-- Center Required -->
          <template #cell(required)="data">
            <span
              v-if="data.item.required"
            >yes</span>
            <span
              v-else
            >no</span>
          </template>

          <!-- Center Type -->
          <template #cell(type)="data">
            <div class="text-center">
              {{ data.item.type }}
            </div>
          </template>

          <!-- Render HTML in Description -->
          <template #cell(description)="data">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <span v-html="renderDescription(data.item.description)" />
          </template>
        </b-table>
        <h5 class="my-2">
          Example Request (JSON structure)
        </h5>
        <BCard class="bg-black text-light mb-2 position-relative">
          <div class="d-flex justify-content-end mb-2">
            <BButton
              variant="outline-light"
              size="sm"
              @click="exportJson(requestPayload, 'training-request')"
            >
              <feather-icon
                icon="DownloadIcon"
                size="14"
                class="me-1"
              />
              Export
            </BButton>
          </div>
          <div class="json-container">
            <pre class="mb-0"><code>{{ formattedRequestJson }}</code></pre>
          </div>
        </BCard>

        <BButton
          variant="primary"
          size="sm"
          :disabled="loading"
          class="mb-3"
          @click="tryItOut"
        >
          <feather-icon
            icon="PlayIcon"
            size="14"
            class="me-1"
          />
          {{ loading ? 'Sending...' : 'Try with it' }}
        </BButton>

        <!-- Loading State -->
        <div
          v-if="loading"
          class="text-center py-3"
        >
          <BSpinner variant="primary" />
          <p class="mt-2 text-muted">
            Sending request...
          </p>
        </div>

        <!-- Response Section - Only show after API call -->
        <div v-if="hasResponse && !loading">
          <h6 class="mb-2">
            Response
          </h6>
          <div class="d-flex align-items-center mb-2">
            <BBadge
              :variant="getStatusVariant(responseData.status)"
              class="mr-1"
            >
              {{ responseData.status }}
            </BBadge>
            <small class="text-muted">{{ getStatusText(responseData.status) }}</small>
          </div>

          <BCard class="bg-black text-light mb-4 position-relative">
            <div class="d-flex justify-content-end mb-2">
              <BButton
                variant="outline-light"
                size="sm"
                @click="exportJson(responseData.data, 'training-response')"
              >
                <feather-icon
                  icon="DownloadIcon"
                  size="14"
                  class="me-1"
                />
                Export
              </BButton>
            </div>
            <div class="json-container">
              <pre class="mb-0"><code>{{ formattedResponseJson }}</code></pre>
            </div>
          </BCard>
        </div>

        <!-- Error Response -->
        <div v-if="errorResponse && !loading">
          <h6 class="mb-2 text-danger">
            Error Response
          </h6>
          <div class="d-flex align-items-center mb-2">
            <BBadge
              variant="danger"
              class="mr-1"
            >
              {{ errorResponse.status }}
            </BBadge>
            <small class="text-muted">{{ errorResponse.statusText }}</small>
          </div>

          <BCard class="bg-black text-light mb-4">
            <div class="json-container">
              <pre class="mb-0"><code>{{ formattedErrorJson }}</code></pre>
            </div>
          </BCard>
        </div>
      </div>
    </div>

    <!-- Return Codes Section -->
    <div>
      <h5 class="mb-3">
        Return Codes
      </h5>
      <BRow>
        <BCol md="6">
          <div class="d-flex align-items-start mb-2">
            <BBadge
              variant="success"
              class="mr-1"
            >
              200
            </BBadge>
            <div>
              <strong>OK</strong><br>
              <small class="text-muted">Training data accepted</small>
            </div>
          </div>
          <div class="d-flex align-items-start mb-2">
            <BBadge
              variant="warning"
              class="mr-1"
            >
              400
            </BBadge>
            <div>
              <strong>Bad Request</strong><br>
              <small class="text-muted">Invalid data format</small>
            </div>
          </div>
          <div class="d-flex align-items-start mb-2">
            <BBadge
              variant="warning"
              class="mr-1"
            >
              422
            </BBadge>
            <div>
              <strong>Validation Error</strong><br>
              <small class="text-muted">Data quality issues</small>
            </div>
          </div>
        </BCol>
        <BCol md="6">
          <div class="d-flex align-items-start mb-2">
            <BBadge
              variant="danger"
              class="mr-1"
            >
              401
            </BBadge>
            <div>
              <strong>Unauthorized</strong><br>
              <small class="text-muted">Authentication failed</small>
            </div>
          </div>
          <div class="d-flex align-items-start mb-2">
            <BBadge
              variant="warning"
              class="mr-1"
            >
              429
            </BBadge>
            <div>
              <strong>Too Many Requests</strong><br>
              <small class="text-muted">Rate limit exceeded</small>
            </div>
          </div>
          <div class="d-flex align-items-start mb-2">
            <BBadge
              variant="danger"
              class="mr-1"
            >
              500
            </BBadge>
            <div>
              <strong>Internal Server Error</strong><br>
              <small class="text-muted">Server error</small>
            </div>
          </div>
        </BCol>
      </BRow>
    </div>

    <!-- Toast for notifications -->
    <BToast
      id="copy-toast"
      :auto-hide-delay="3000"
      variant="success"
      solid
      toast-class="d-none"
    >
      <template #toast-title>
        <feather-icon
          icon="CheckIcon"
          size="16"
          class="me-1"
        />
        Success
      </template>
      Content copied to clipboard!
    </BToast>
  </div>
</template>

<script>
import {
  BBadge,
  BButton,
  BCard,
  BCol,
  BRow,
  BSpinner,
  BToast,
  BTable,
} from 'bootstrap-vue'
import axios from 'axios'
import getEnv from '@/utils/env'
import sanitizeHtml from '@/utils/security'

export default {
  name: 'TrainingApiConfig',
  components: {
    BBadge,
    BButton,
    BCard,
    BCol,
    BRow,
    BSpinner,
    BToast,
    BTable,
  },
  data() {
    // Get backend URL from environment variable
    // const backendUrl = process.env.VUE_APP_BACKEND_URL

    // Parse the URL to extract base URL and port
    // const urlObject = new URL(backendUrl)
    // const baseUrl = process.env.VUE_APP_BACKEND_URL
    // const apiPort = urlObject.port || (urlObject.protocol === 'https:' ? '443' : '80')

    // Configure Axios with the backend URL
    // axios.defaults.baseURL = backendUrl

    return {
      loading: false,
      hasResponse: false,
      responseData: null,
      errorResponse: null,
      requestPayload: {
        files: '<binary-files>',
        process_id: 'AL-AA4-1234567',
      },
      // apiBaseUrl: baseUrl,
      // apiPort,
      requestFieldsMeta: [
        {
          key: 'field', label: 'Field', thStyle: { width: '20%' }, thClass: 'text-center',
        },
        {
          key: 'type', label: 'Type', thStyle: { width: '20%' }, tdClass: 'text-center', thClass: 'text-center',
        },
        {
          key: 'required', label: 'Required', thStyle: { width: '10%' }, tdClass: 'text-center', thClass: 'text-center',
        },
        { key: 'description', label: 'Description', thClass: 'text-center' },
      ],
      requestFields: [
        {
          field: 'files',
          type: 'binary / array of files',
          required: true,
          description: 'One or more files to upload. This should be sent as binary data.',
        },
        {
          field: 'process_id',
          type: 'string',
          required: true,
          description: `ID of the Process associated with the uploaded files.
    <br><b>Example:</b> "AL-AA4-1234567"`,
        },
      ],
    }
  },
  computed: {
    getBaseUrl() {
      return getEnv('VUE_APP_BACKEND_URL')
    },
    formattedRequestJson() {
      return JSON.stringify(this.requestPayload, null, 2)
    },
    formattedResponseJson() {
      return this.responseData ? JSON.stringify(this.responseData.data, null, 2) : ''
    },
    formattedErrorJson() {
      return this.errorResponse ? JSON.stringify(this.errorResponse.data, null, 2) : ''
    },
  },
  methods: {
    renderDescription(value) {
      return sanitizeHtml(value || '')
    },
    async tryItOut() {
      this.loading = true
      this.hasResponse = false
      this.errorResponse = null

      try {
        // Create FormData
        const formData = new FormData()

        // Step 1: Convert the requestPayload to binary file (keep it as is)
        const payloadBinary = new Blob(
          [JSON.stringify(this.requestPayload, null, 2)],
          { type: 'application/json' },
        )

        // Step 2: Add the binary file to FormData
        formData.append('files', payloadBinary, 'request-payload.json')

        // Step 3: Add all form fields from requestPayload (including files: 'binary-files')
        formData.append('process_id', this.requestPayload.process_id)
        formData.append('files', this.requestPayload.files) // This sends 'binary-files' as string
        formData.append('testing', true)

        const response = await axios.post('/pipeline/process_training/', formData)

        this.responseData = {
          status: response.status,
          data: response.data,
        }
        this.hasResponse = true
      } catch (error) {
        this.errorResponse = {
          status: error.response?.status || 0,
          statusText: error.response?.statusText || 'Network Error',
          data: error.response?.data || {
            error: 'Failed to connect to the server',
            message: error.message,
          },
        }
      } finally {
        this.loading = false
      }
    },

    exportJson(data, filename) {
      const jsonString = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      URL.revokeObjectURL(url)
    },

    getStatusVariant(status) {
      if (status >= 200 && status < 300) return 'success'
      if (status >= 400 && status < 500) return 'warning'
      if (status >= 500) return 'danger'
      return 'info'
    },

    getStatusText(status) {
      const statusTexts = {
        200: 'OK - Training data accepted',
        400: 'Bad Request - Invalid data format',
        401: 'Unauthorized - Authentication failed',
        422: 'Validation Error - Data quality issues',
        429: 'Too Many Requests - Rate limit exceeded',
        500: 'Internal Server Error - Server error',
      }
      return statusTexts[status] || 'Unknown status'
    },
  },
}
</script>

<style scoped>
.alert {
  border-radius: 6px;
}

/* Loading spinner alignment */
.spinner-border-sm {
  margin-right: 0.5rem;
}

/* JSON display styling - ensures readability in dark mode */
.json-container pre {
  background: transparent;
  border: none;
  padding: 1rem;
  overflow-x: auto;
  white-space: pre-wrap;
  font-size: 0.875rem;
  line-height: 1.5;
}

.json-container code {
  color: #f8f9fa; /* Light color for dark backgrounds */
  background: transparent;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
</style>
