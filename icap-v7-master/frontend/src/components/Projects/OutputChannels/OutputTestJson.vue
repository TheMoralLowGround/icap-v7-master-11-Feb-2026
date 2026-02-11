<template>
  <div class="mb-4">
    <!-- Test Data Display -->
    <!-- v-if="isData" -->
    <div v-if="testData || testDataError">
      <h5 class="my-2">
        {{ testDataError ? 'Error Response' : 'Test JSON Data' }} (required keys only)
      </h5>
      <BCard
        :class="testDataError ? 'bg-danger text-white mb-2' : 'bg-black text-light mb-2'"
      >
        <div class="json-container bg-black">
          <pre class="mb-0"><code>{{ formattedTestDataJson }}</code></pre>
        </div>
      </BCard>

      <!-- Try Now Button - Only appears when ALL validation passes -->
      <BButton
        v-if="shouldShowTryButton"
        variant="success"
        size="sm"
        :disabled="emitting"
        class="mb-3"
        @click="tryNow"
      >
        <feather-icon
          v-if="emitting"
          icon="LoaderIcon"
          size="14"
          class="me-1 spinner"
        />
        <feather-icon
          v-else
          icon="PlayIcon"
          size="14"
          class="me-1"
        />
        {{ emitting ? 'Testing Connection...' : 'Try Now' }}
      </BButton>
    </div>

    <!-- Loading State for Test Data -->
    <div
      v-if="loadingTestData"
      class="text-center py-3"
    >
      <BSpinner variant="primary" />
      <p class="mt-2 text-muted">
        Fetching test data...
      </p>
    </div>

    <!-- Response Section - Only show after Try Now is clicked -->
    <div v-if="hasResponse && !emitting">
      <h6 class="mb-2">
        Execution Result
      </h6>
      <div class="d-flex align-items-center mb-2">
        <BBadge
          :variant="responseStatus === 'success' ? 'success' : 'danger'"
          class="mr-1"
        >
          {{ responseStatus.toUpperCase() }}
        </BBadge>
        <small class="text-muted">{{ responseMessage }}</small>
      </div>

      <BCard class="bg-black text-light mb-4">
        <div class="json-container">
          <pre class="mb-0"><code>{{ formattedResponseDataJson }}</code></pre>
        </div>
      </BCard>
    </div>

    <!-- Error Alert -->
    <div
      v-if="testDataError"
      class="alert alert-danger mt-3"
    >
      <strong>Error:</strong> {{ testDataError.message || 'Failed to fetch test data' }}
    </div>
  </div>
</template>

<script>
import {
  BBadge,
  BButton,
  BCard,
  BSpinner,
} from 'bootstrap-vue'
import axios from 'axios'

// Authentication configuration - matches parent form logic
const AUTH_CONFIGS = {
  none: [],
  basic: ['username', 'password'],
  token: ['token'],
  api_key: ['api_key_name', 'api_key_value'],
  oauth2: ['client_id', 'client_secret', 'token_url'],
}

export default {
  name: 'OutputTestJson',
  components: {
    BBadge,
    BButton,
    BCard,
    BSpinner,
  },
  props: {
    initialProjectName: {
      type: String,
      default: '',
    },
    // New prop to receive configuration data from parent
    configurationData: {
      type: Object,
      default: () => ({}),
      validator(value) {
        // Optional validation for required fields
        return typeof value === 'object'
      },
    },
    // New prop to know if parent channel is enabled
    isChannelEnabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      projectName: this.initialProjectName,
      testData: null,
      testDataError: null,
      loadingTestData: false,
      emitting: false,
      hasResponse: false,
      responseStatus: '',
      responseMessage: '',
      responseData: null,
    }
  },
  computed: {
    formattedTestDataJson() {
      const data = this.testData || this.testDataError
      return data ? JSON.stringify(data, null, 2) : ''
    },
    isData() {
      return Object.keys(this.testData).length > 0
    },
    formattedResponseDataJson() {
      return this.responseData ? JSON.stringify(this.responseData, null, 2) : ''
    },

    // Comprehensive validation that matches parent logic
    hasValidConfiguration() {
      const config = this.configurationData

      // Check if config exists and channel is enabled
      if (!config || !this.isChannelEnabled) {
        return false
      }

      // Check basic required fields
      if (!config.endpoint_url?.trim() || !config.auth_type || !config.request_type) {
        return false
      }

      // Check auth-specific required fields using array method
      const requiredFields = AUTH_CONFIGS[config.auth_type] || []
      const hasAllRequiredFields = requiredFields.every(field => config[field]?.trim())

      return hasAllRequiredFields
    },

    // Get validation errors for parent notification
    validationErrors() {
      const config = this.configurationData
      const errors = []

      if (!this.isChannelEnabled) {
        errors.push('Channel is disabled')
        return errors
      }

      if (!config) {
        errors.push('Configuration is missing')
        return errors
      }

      // Check basic fields
      if (!config.endpoint_url?.trim()) {
        errors.push('Endpoint URL is required')
      }

      if (!config.request_type) {
        errors.push('Request Type is required')
      }

      if (!config.auth_type) {
        errors.push('Authentication Type is required')
      }

      // Check auth-specific fields using array method
      const requiredFields = AUTH_CONFIGS[config.auth_type] || []
      const authErrors = requiredFields
        .filter(field => !config[field]?.trim())
        .map(field => {
          const displayName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
          return `${displayName} is required for ${config.auth_type} authentication`
        })

      errors.push(...authErrors)

      return errors
    },

    // Get test data from configuration or fallback to fetched data
    effectiveTestData() {
      return this.configurationData?.test_json || this.testData
    },

    // Simple condition for showing Try Now button
    shouldShowTryButton() {
      return this.testData
             && !this.testDataError
             && this.hasValidConfiguration
             && this.isChannelEnabled
    },
  },
  watch: {
    // Simple watcher for configuration changes
    configurationData: {
      handler(newConfig) {
        if (newConfig?.test_json) {
          this.testData = newConfig.test_json
          this.testDataError = null
        }

        // Emit validation status to parent whenever config changes
        this.emitValidationStatus()
      },
      immediate: true,
      deep: true,
    },

    // Reset execution results when auth type changes
    'configurationData.auth_type': {
      handler(newAuthType, oldAuthType) {
        // Only reset if auth type actually changed (not on initial load)
        if (oldAuthType !== undefined && newAuthType !== oldAuthType) {
          this.clearResponse()
          // Emit validation status when auth type changes
          this.$nextTick(() => {
            this.emitValidationStatus()
          })
        }
      },
    },

    // Emit validation status when channel status changes
    isChannelEnabled: {
      handler() {
        this.$nextTick(() => {
          this.emitValidationStatus()
        })
      },
    },
  },
  mounted() {
    // Only fetch test data if not provided via configuration
    if (!this.configurationData?.test_json) {
      this.fetchTestData()
    }
    // Emit initial validation status
    this.$nextTick(() => {
      this.emitValidationStatus()
    })
  },
  methods: {
    // Emit validation status to parent
    emitValidationStatus() {
      const isValid = this.hasValidConfiguration
      const errors = this.validationErrors

      this.$emit('validation-status', {
        isValid,
        errors,
        hasTestData: !!this.testData,
        canTest: this.shouldShowTryButton,
      })
    },

    async fetchTestData() {
      if (!this.projectName || !this.projectName.trim()) {
        return
      }

      this.loadingTestData = true
      this.testData = null
      this.testDataError = null
      this.hasResponse = false

      try {
        const response = await axios.post('/pipeline/get_test_json/', {
          project: this.projectName.trim(),
        })

        this.testData = response.data.test_json
        this.testDataError = null

        // Emit validation status after test data is loaded
        this.$nextTick(() => {
          this.emitValidationStatus()
        })
      } catch (error) {
        this.testDataError = {
          status: error.response?.status || 0,
          statusText: error.response?.statusText || 'Network Error',
          message: error.response?.data?.error || error.response?.data?.message || 'Failed to fetch test data',
          data: error.response?.data || { error: error.message },
        }
        this.testData = null

        // Emit validation status even on error
        this.$nextTick(() => {
          this.emitValidationStatus()
        })
      } finally {
        this.loadingTestData = false
      }
    },

    async tryNow() {
      // Double-check validation before proceeding
      if (!this.hasValidConfiguration) {
        this.$emit('validation-failed', this.validationErrors)
        return
      }

      this.emitting = true
      this.hasResponse = false

      try {
        // Create flat payload structure - no nested objects
        const payload = {
          // Basic config
          auth_type: this.configurationData.auth_type,
          endpoint_url: this.configurationData.endpoint_url,
          request_type: this.configurationData.request_type,

          // Add auth fields based on type (flat structure)
          ...this.getAuthFields(),

          // Add test_json with actual test data
          test_json: this.effectiveTestData || {},
        }

        // Call the test output connection API
        const response = await axios.post('/pipeline/test_output_connection/', payload)

        // Handle successful response
        this.responseStatus = 'success'
        this.responseMessage = response.data.message || 'Connection test successful!'
        this.responseData = response.data
        this.hasResponse = true

        // Emit success event to parent
        this.$emit('test-success', {
          message: this.responseMessage,
          data: this.responseData,
        })
      } catch (error) {
        // Handle error response
        this.responseStatus = 'error'
        this.responseMessage = error.response?.data?.message || error.message || 'Connection test failed'
        this.responseData = {
          error: this.responseMessage,
          details: error.response?.data || error.message,
          status: error.response?.status || 0,
          statusText: error.response?.statusText || 'Unknown Error',
        }
        this.hasResponse = true

        // Emit error event to parent
        this.$emit('test-error', {
          message: this.responseMessage,
          data: this.responseData,
        })
      } finally {
        this.emitting = false
      }
    },

    // Simple method to get auth fields based on auth type
    getAuthFields() {
      const config = this.configurationData
      const authFields = {}

      switch (config.auth_type) {
        case 'none':
          // No authentication fields needed
          break
        case 'basic':
          if (config.username) authFields.username = config.username
          if (config.password) authFields.password = config.password
          break
        case 'token':
          if (config.token) authFields.token = config.token
          break
        case 'api_key':
          if (config.api_key_name) authFields.api_key_name = config.api_key_name
          if (config.api_key_value) authFields.api_key_value = config.api_key_value
          break
        case 'oauth2':
          if (config.client_id) authFields.client_id = config.client_id
          if (config.client_secret) authFields.client_secret = config.client_secret
          if (config.token_url) authFields.token_url = config.token_url
          break
        default:
          // Return empty object for unknown auth types
          break
      }

      return authFields
    },

    handleError(message) {
      this.responseStatus = 'error'
      this.responseMessage = message
      this.responseData = { error: message }
      this.hasResponse = true
    },

    // Method to refresh test data
    refreshTestData() {
      if (this.projectName && !this.configurationData?.test_json) {
        this.fetchTestData()
      }
    },

    // Method to clear all data
    clearData() {
      this.testData = null
      this.testDataError = null
      this.hasResponse = false
      this.responseData = null
      this.projectName = this.initialProjectName
    },

    // Method to reset response data only
    clearResponse() {
      this.hasResponse = false
      this.responseData = null
      this.responseStatus = ''
      this.responseMessage = ''
    },
  },
}
</script>

<style scoped>
/* JSON display styling - fixed height with scroll */
.json-container {
  max-height: 500px;
  overflow-y: auto;
  border-radius: 4px;
}

.json-container pre {
  background: transparent;
  border: none;
  padding: 1rem;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.875rem;
  line-height: 1.5;
}

.json-container code {
  color: #f8f9fa;
  background: transparent;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* Custom scrollbar for JSON container */
.json-container::-webkit-scrollbar {
  width: 6px;
}

.json-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.json-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.json-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* Spinner animation */
.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Alert styling */
.alert {
  border-radius: 6px;
}

/* Badge spacing */
.mr-1 {
  margin-right: 0.25rem;
}
</style>
