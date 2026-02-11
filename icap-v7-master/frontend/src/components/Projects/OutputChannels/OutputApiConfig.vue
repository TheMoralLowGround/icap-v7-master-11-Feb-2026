<template>
  <div class="p-3">
    <validation-observer ref="outputApiForm">
      <BForm @submit.prevent="handleSubmit">
        <!-- Channel Status Toggle -->
        <BFormGroup class="mb-4">
          <div class="d-flex justify-content-between">
            <div class="d-flex align-items-center">
              <label class="form-label mx-2">Output API Channel Status</label>
              <BFormCheckbox
                v-model="channelEnabled"
                switch
                @change="onChannelToggle"
              >
                {{ channelEnabled ? 'Enabled' : 'Disabled' }}
              </BFormCheckbox>
            </div>
            <div class="d-flex gap-2">
              <BButton
                v-if="shouldShowClearButton"
                variant="outline-danger"
                @click="clearForm"
              >
                Clear Form
              </BButton>
            </div>
          </div>
        </BFormGroup>
        <hr class="mb-4">
        <div :style="!channelEnabled ? 'opacity: 0.6; pointer-events: none;' : ''">
          <BRow>
            <BCol md="4">
              <validation-provider
                #default="{ errors }"
                name="Method Type"
                vid="request_type"
                mode="eager"
                :rules="getFieldRules('request_type')"
              >
                <BFormGroup
                  label="Request Type"
                  label-for="request_type"
                  :state="getFieldState(errors)"
                >
                  <v-select
                    id="request_type"
                    v-model="form.request_type"
                    :options="['GET', 'POST', 'PUT', 'PATCH']"
                    :disabled="!channelEnabled"
                    :state="getFieldState(errors)"
                    clearable
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </BFormGroup>
              </validation-provider>
            </BCol>
            <BCol md="8">
              <validation-provider
                #default="{ errors }"
                name="Endpoint URL"
                vid="endpoint_url"
                mode="eager"
                :rules="getFieldRules('endpoint_url')"
              >
                <BFormGroup
                  label="API Endpoint URL"
                  label-for="endpoint-url"
                  :state="getFieldState(errors)"
                >
                  <BFormInput
                    id="endpoint-url"
                    v-model="form.endpoint_url"
                    type="text"
                    placeholder="https://api.example.com/endpoint"
                    :state="getFieldState(errors)"
                    :disabled="!channelEnabled"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </BFormGroup>
              </validation-provider>
            </BCol>
          </BRow>
          <!-- Endpoint URL -->

          <!-- Authentication Type Selection -->
          <validation-provider
            #default="{ errors }"
            name="Authentication Type"
            vid="auth_type"
            mode="eager"
            :rules="getFieldRules('auth_type')"
          >
            <BFormGroup
              label="Authentication Type"
              label-for="auth-type"
              :state="getFieldState(errors)"
            >
              <BFormRadioGroup
                id="auth-type"
                v-model="form.auth_type"
                :options="authOptions"
                :disabled="!channelEnabled"
                class="mb-2"
                :state="getFieldState(errors)"
                @change="onAuthTypeChange"
              />
              <small class="text-danger">{{ errors[0] }}</small>
            </BFormGroup>
          </validation-provider>

          <!-- Basic Authentication Fields -->
          <div v-if="form.auth_type === 'basic'">
            <BasicAuthForm
              v-if="form.auth_type === 'basic'"
              :form-data="form"
              :disabled="!channelEnabled"
              :validation-rules="getFieldRules"
              @update-field="updateFormField"
            />
          </div>

          <!-- Token Authentication Fields -->
          <div v-if="form.auth_type === 'token'">
            <h5 class="mb-1">
              Token Authentication
            </h5>
            <validation-provider
              #default="{ errors }"
              name="Token"
              vid="token"
              mode="eager"
              :rules="getFieldRules('token')"
            >
              <BFormGroup
                label="Token (Bearer)"
                label-for="token"
                :state="getFieldState(errors)"
              >
                <!-- <BInputGroup> -->
                <BFormInput
                  id="token"
                  v-model="form.token"
                  :type="fieldTypes.token"
                  placeholder="Enter your authentication token"
                  :state="getFieldState(errors)"
                  :disabled="!channelEnabled"
                />
                <!-- <BInputGroupAppend>
                    <BButton
                      variant="outline-secondary"
                      :icon="getToggleIcon('token')"
                      @click="toggleFieldVisibility('token')"
                    >
                      <feather-icon :icon="getToggleIcon('token')" size="16" />
                    </BButton>
                  </BInputGroupAppend> -->
                <!-- </BInputGroup> -->
                <small class="text-danger">{{ errors[0] }}</small>
              </BFormGroup>
            </validation-provider>
          </div>

          <!-- API Key Authentication Fields -->
          <div v-if="form.auth_type === 'api_key'">
            <ApiKeyAuthForm
              v-if="form.auth_type === 'api_key'"
              :form-data="form"
              :disabled="!channelEnabled"
              :validation-rules="getFieldRules"
              @update-field="updateFormField"
            />
          </div>

          <!-- OAuth2 Authentication Fields -->
          <div v-if="form.auth_type === 'oauth2'">
            <OAuth2AuthForm
              v-if="form.auth_type === 'oauth2'"
              :form-data="form"
              :disabled="!channelEnabled"
              :validation-rules="getFieldRules"
              @update-field="updateFormField"
            />
          </div>

          <BAlert
            variant="danger"
            :show="errorMessage !== null"
            class="my-3"
          >
            <div class="alert-body">
              <p class="mb-0">
                {{ errorMessage }}
              </p>
            </div>
          </BAlert>

          <BAlert
            variant="success"
            :show="successMessage !== null"
            class="my-3"
          >
            <div class="alert-body">
              <p class="mb-0">
                {{ successMessage }}
              </p>
            </div>
          </BAlert>
          <!-- <TestConnectionOutput  v-if="isConnectionShow" :test-result="conectionResponse" /> -->
        </div>

        <!-- Updated OutputTestJson component with proper configuration binding -->
        <OutputTestJson
          v-if="outputType == 'json'"
          :initial-project-name="project.name"
          :configuration-data="configurationForTesting"
          :is-channel-enabled="channelEnabled"
        />

        <div class="d-flex justify-content-between mt-3">
          <BButton
            variant="outline-secondary"
            @click="$emit('cancel')"
          >
            Cancel
          </BButton>
          <div class="d-flex gap-2">
            <BButton
              variant="primary"
              type="submit"
              :disabled="submitting"
            >
              <span v-if="submitting">{{ isUpdateMode ? 'Updating...' : 'Saving...' }}</span>
              <span v-else>{{ isUpdateMode ? 'Update Configuration' : 'Save Configuration' }}</span>
            </BButton>
          </div>
        </div>
      </BForm>
    </validation-observer>
    <DeleteOutputConfig
      v-if="isReset"
      :project-name="project.name"
      :output-type="outputType"
    />
  </div>
</template>

<script>
import {
  BButton,
  BCol,
  BForm,
  BFormCheckbox,
  BFormGroup,
  BFormInput,
  BFormRadioGroup,
  // BInputGroup,
  // BInputGroupAppend,
  BRow,
  BAlert,
  // BCard,
  // BBadge,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import { togglePasswordVisibility } from '@core/mixins/ui/forms'
import vSelect from 'vue-select'
// eslint-disable-next-line no-unused-vars
import { required, url } from '@validations'
import BasicAuthForm from './BasicAuthForm.vue'
import ApiKeyAuthForm from './ApiKeyAuthForm.vue'
import OAuth2AuthForm from './OAuth2AuthForm.vue'
// import TestConnectionOutput from './TestConnectionOutput.vue'
import OutputTestJson from './OutputTestJson.vue'
import DeleteOutputConfig from './DeleteOutputConfig.vue'
// Simple config for auth fields - no components, just data
const AUTH_CONFIGS = {
  none: [],
  basic: ['username', 'password'],
  token: ['token'],
  api_key: ['api_key_name', 'api_key_value'],
  oauth2: ['client_id', 'client_secret', 'token_url', 'scope', 'grant_type', 'username', 'password'],
}

// All possible auth fields for complete payload
const ALL_AUTH_FIELDS = ['username', 'password', 'api_key_name', 'api_key_value', 'client_id', 'client_secret', 'token', 'token_url', 'scope', 'grant_type']

export default {
  name: 'OutputApiConfig',
  components: {
    BButton,
    BCol,
    BForm,
    BFormCheckbox,
    BFormGroup,
    BFormInput,
    BFormRadioGroup,
    // BInputGroup,
    // BInputGroupAppend,
    BRow,
    ValidationProvider,
    ValidationObserver,
    BAlert,
    vSelect,
    BasicAuthForm,
    ApiKeyAuthForm,
    OAuth2AuthForm,
    // TestConnectionOutput,
    OutputTestJson,
    // BBadge,
    DeleteOutputConfig,
  },
  mixins: [togglePasswordVisibility],
  props: {
    outputType: {
      type: String,
      required: true,
    },
    initialData: {
      type: Object,
      default: () => ({}),
    },
    channelId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      submitting: false,
      errorMessage: null,
      successMessage: null,
      channelEnabled: false,
      isConfigSaved: false,
      isReset: false,
      configId: null, // Track if this is an update or create
      conectionResponse: {},

      // Consolidated field types for password visibility
      fieldTypes: {
        password: 'password',
        token: 'password',
        token_url: 'password',
        api_key_value: 'password',
        client_secret: 'password',
      },

      authOptions: [
        { value: 'none', text: 'No Authentication' },
        { value: 'basic', text: 'Basic Authentication' },
        { value: 'token', text: 'Token Authentication' },
        { value: 'api_key', text: 'API Key' },
        { value: 'oauth2', text: 'OAuth2' },
      ],

      form: {
        endpoint_url: '',
        request_type: 'POST',
        auth_type: 'none',
        username: '',
        password: '',
        token: '', // Added token field
        api_key_name: '',
        api_key_value: '',
        client_id: '',
        client_secret: '',
        token_url: '',
        scope: '',
        grant_type: 'client_credentials',
        // Add test_json to form data
        test_json: null,
        output_type: this.outputType,
      },
    }
  },

  computed: {
    isConnectionShow() {
      return Object.keys(this.conectionResponse).length > 0
    },

    project() {
      return this.$store.getters['project/project']
    },

    shouldShowClearButton() {
      if (!this.channelEnabled) return false

      const checkFields = ['endpoint_url', 'username', 'password', 'token', 'api_key_name', 'api_key_value', 'client_id', 'client_secret', 'token_url']
      return checkFields.some(field => this.form[field]?.trim())
    },

    // Check if this is update mode (has ID)
    isUpdateMode() {
      return this.configId !== null
    },

    // Computed property to create proper configuration object for OutputTestJson
    configurationForTesting() {
      // Don't provide config if channel is disabled or basic required fields are missing
      if (!this.channelEnabled || !this.form.endpoint_url || !this.form.request_type || !this.form.auth_type) {
        return null
      }

      // Base configuration object
      const config = {
        endpoint_url: this.form.endpoint_url,
        request_type: this.form.request_type,
        auth_type: this.form.auth_type,
        // Include test_json if available, otherwise null
        test_json: this.form.test_json,
      }

      // Add authentication-specific fields based on auth_type
      if (this.form.auth_type === 'basic' && this.form.username && this.form.password) {
        config.username = this.form.username
        config.password = this.form.password
      }

      if (this.form.auth_type === 'token' && this.form.token) {
        config.token = this.form.token
      }

      if (this.form.auth_type === 'api_key' && this.form.api_key_name && this.form.api_key_value) {
        config.api_key_name = this.form.api_key_name
        config.api_key_value = this.form.api_key_value
      }

      if (this.form.auth_type === 'oauth2' && this.form.client_id && this.form.client_secret && this.form.token_url) {
        config.client_id = this.form.client_id
        config.client_secret = this.form.client_secret
        config.token_url = this.form.token_url
        if (this.form.scope) {
          config.scope = this.form.scope
        }
        if (this.form.grant_type) {
          config.grant_type = this.form.grant_type
        }
        if (this.form.grant_type === 'password') {
          config.username = this.form.username || ''
          config.password = this.form.password || ''
        }
      }

      return config
    },
  },

  watch: {
    'form.auth_type': {
      handler() {
        this.conectionResponse = {}
      },
      immediate: true,
    },
    initialData: {
      handler(newData) {
        if (newData && Object.keys(newData).length > 0) {
          this.form = { ...this.form, ...newData }
          this.channelEnabled = newData.is_active || false
          this.configId = newData.id || null
        }
      },
      deep: true,
      immediate: true,
    },
  },

  async mounted() {
    await this.fetchOutputApi()
  },

  methods: {
    updateFormField(fieldName, value) {
      this.form[fieldName] = value
    },

    // Helper methods to reduce code duplication
    getFieldState(errors) {
      return errors.length > 0 ? false : null
    },

    getFieldRules(fieldName) {
      if (!this.channelEnabled) return ''

      if (['endpoint_url', 'auth_type', 'request_type'].includes(fieldName)) {
        return 'required'
      }

      // Check if field is required for current auth type
      const requiredFields = AUTH_CONFIGS[this.form.auth_type] || []
      return requiredFields.includes(fieldName) ? 'required' : ''
    },

    getToggleIcon(fieldType) {
      return this.fieldTypes[fieldType] === 'password' ? 'EyeIcon' : 'EyeOffIcon'
    },

    // Consolidated toggle method instead of 4 separate methods
    toggleFieldVisibility(fieldName) {
      if (this.fieldTypes[fieldName]) {
        this.fieldTypes[fieldName] = this.fieldTypes[fieldName] === 'password' ? 'text' : 'password'
      }
    },

    onChannelToggle(enabled) {
      this.channelEnabled = enabled
      this.$refs.outputApiForm.reset()
      this.errorMessage = null
      this.successMessage = null
    },

    onAuthTypeChange() {
      this.clearAuthFields()
      this.$refs.outputApiForm.reset()
      this.errorMessage = null
      this.successMessage = null
    },

    clearAuthFields() {
      ALL_AUTH_FIELDS.forEach(field => {
        this.form[field] = ''
      })
    },

    clearForm() {
      this.form = {
        endpoint_url: '',
        request_type: 'POST',
        auth_type: 'none',
        username: '',
        password: '',
        token: '',
        api_key_name: '',
        api_key_value: '',
        client_id: '',
        client_secret: '',
        token_url: '',
        test_json: null,
        output_type: this.outputType,
      }

      // Reset field types
      Object.keys(this.fieldTypes).forEach(field => {
        this.fieldTypes[field] = 'password'
      })

      this.$nextTick(() => {
        this.$refs.outputApiForm.reset()
      })
    },

    async fetchOutputApi() {
      try {
        const params = { output_id: this.channelId }
        const response = await this.$store.dispatch('project/fetchOutputApiConfig', { params })
        if (response && response.data && response.data.length > 0) {
          this.form = { ...this.form, ...response.data[0] }
          this.channelEnabled = response?.data[0]?.is_active || false
          this.configId = response?.data[0]?.id || null // Set the ID for update mode
          this.isConfigSaved = true
        }
      } catch (error) {
        if (error.response?.status === 500) {
          this.isReset = true
        }
        // Silent fail on initial load
      }
    },

    // Simplified validation using the config
    getMissingFields() {
      const missing = []

      if (!this.form.endpoint_url?.trim()) {
        missing.push('Endpoint URL')
      }

      const requiredFields = AUTH_CONFIGS[this.form.auth_type] || []
      requiredFields.forEach(field => {
        if (!this.form[field]?.trim()) {
          const displayName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
          missing.push(displayName)
        }
      })

      return missing
    },

    // Modified submission data to include ALL auth fields
    getSubmissionData() {
      const baseData = {
        project: this.project.id,
        is_active: this.channelEnabled,
        endpoint_url: this.form.endpoint_url,
        auth_type: this.form.auth_type,
        request_type: this.form.request_type,
        output_type: this.outputType,
        output_id: this.channelId,
      }

      // Add ID if it's an update
      if (this.configId) {
        baseData.id = this.configId
      }

      // Add test_json if available
      if (this.form.test_json) {
        baseData.test_json = this.form.test_json
      }

      // Add ALL auth fields - current auth type fields with values, others with null
      const requiredFields = AUTH_CONFIGS[this.form.auth_type] || []

      ALL_AUTH_FIELDS.forEach(field => {
        if (requiredFields.includes(field) && this.form[field]) {
          // Current auth type field with actual value
          baseData[field] = this.form[field]
        }
      })
      return baseData
    },

    async handleSubmit() {
      try {
        const success = await this.$refs.outputApiForm.validate()
        if (!success) return

        this.submitting = true

        // Choose the appropriate store action based on whether we have an ID
        const actionName = this.isUpdateMode ? 'project/UpdateOutputApiConfig' : 'project/saveOutputApiConfig'

        await this.$store.dispatch(actionName, {
          payload: this.getSubmissionData(),
        })

        this.isConfigSaved = true
        await this.fetchOutputApi() // Refresh to get updated data including ID

        const successMessage = this.isUpdateMode ? 'Output API Configuration Updated' : 'Output API Configuration Saved'

        this.$toast({
          component: ToastificationContent,
          props: {
            title: successMessage,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        this.$emit('save', {
          ...this.form,
          is_active: this.channelEnabled,
          id: this.configId,
        })
      } catch (error) {
        const msg = error.response?.data?.error || error.response?.data?.project[0]
        const errMessage = msg || `Failed to ${this.isUpdateMode ? 'update' : 'save'}`
        this.errorMessage = errMessage
        this.$toast({
          component: ToastificationContent,
          props: {
            title: errMessage,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
