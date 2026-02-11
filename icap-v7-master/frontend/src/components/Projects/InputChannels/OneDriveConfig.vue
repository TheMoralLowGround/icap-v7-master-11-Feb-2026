<template>
  <BRow class="no-gutters">
    <!-- Main Form Section -->
    <BCol :md="islogs ? 6 : 12">
      <div class="p-3">
        <validation-observer ref="onedriveForm">
          <BForm @submit.prevent="handleSubmit">
            <!-- Channel Status Toggle -->
            <BFormGroup class="mb-4">
              <div class="d-flex justify-content-between">
                <div class="d-flex align-items-center">
                  <label class="form-label mx-2">OneDrive Channel Status</label>
                  <BFormCheckbox
                    v-model="channelEnabled"
                    switch
                    @change="toggleChannelStatus"
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
                  <BButton
                    variant="outline-primary"
                    @click="showLogs"
                  >
                    {{ islogs ? 'Hide logs' : 'Show logs' }}
                  </BButton>
                </div>
              </div>
            </BFormGroup>

            <hr class="mb-4">
            <div :style="!channelEnabled ? 'opacity: 0.6; pointer-events: none;' : ''">

              <BRow>
                <BCol :md="islogs? '12' : '6'">
                  <validation-provider
                    #default="{ errors }"
                    name="Transaction Folder Url"
                    vid="transactionFolderPath"
                    mode="eager"
                    :rules="channelEnabled ? folderUrlValidation : ''"
                  >
                    <BFormGroup
                      label="Transaction Folder Url"
                      label-for="transaction_folder_url"
                      :state="errors.length > 0 ? false : null"
                    >
                      <BFormInput
                        id="transaction_folder_url"
                        v-model="localForm.transaction_folder_url"
                        placeholder="Enter transaction folder url"
                        :state="errors.length > 0 ? false : null"
                        :disabled="!channelEnabled"
                        @input="onFieldChange"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </BFormGroup>
                  </validation-provider>
                </BCol>
                <BCol :md="islogs? '12': '6'">
                  <validation-provider
                    #default="{ errors }"
                    name="Training Folder Path"
                    vid="trainingFolderPath"
                    mode="eager"
                    :rules="channelEnabled ? trainingFolderUrlValidation : ''"
                  >
                    <BFormGroup
                      label="Training Folder Url"
                      label-for="training_folder_url"
                      :state="errors.length > 0 ? false : null"
                    >
                      <BFormInput
                        id="training_folder_url"
                        v-model="localForm.training_folder_url"
                        placeholder="Enter training folder url"
                        :disabled="!channelEnabled"
                        :state="errors.length > 0 ? false : null"
                        @input="onFieldChange"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </BFormGroup>
                  </validation-provider>
                </BCol>
              </BRow>

              <BRow>
                <BCol :md="islogs? '12': '4'">
                  <validation-provider
                    #default="{ errors }"
                    name="Tenant ID"
                    vid="tenantId"
                    mode="eager"
                    :rules="channelEnabled ? 'required' : ''"
                  >
                    <BFormGroup
                      :state="errors.length > 0 ? false : null"
                    >
                      <template #label>
                        <div class="d-flex align-items-center">
                          <span>Tenant ID</span>
                          <feather-icon
                            v-b-tooltip.hover.top.html="tenantIdTooltip"
                            class="cursor-pointer ml-1"
                            icon="InfoIcon"
                            size="14"
                          />
                        </div>
                      </template>
                      <BFormInput
                        id="tenant-id"
                        v-model="localForm.tenant_id"
                        placeholder="Enter tenant id"
                        :state="errors.length > 0 ? false : null"
                        :disabled="!channelEnabled"
                        @input="onFieldChange"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </BFormGroup>
                  </validation-provider>
                </BCol>
                <BCol :md="islogs? '12': '4'">
                  <validation-provider
                    #default="{ errors }"
                    name="Client ID"
                    vid="clientId"
                    mode="eager"
                    :rules="channelEnabled ? 'required' : ''"
                  >
                    <BFormGroup
                      :state="errors.length > 0 ? false : null"
                    >
                      <template #label>
                        <div class="d-flex align-items-center">
                          <span>Client (Application) ID</span>
                          <feather-icon
                            v-b-tooltip.hover.top.html="clientIdTooltip"
                            class="cursor-pointer ml-1"
                            icon="InfoIcon"
                            size="14"
                          />
                        </div>
                      </template>
                      <BFormInput
                        id="client-id"
                        v-model="localForm.client_id"
                        placeholder="Enter client id"
                        :state="errors.length > 0 ? false : null"
                        :disabled="!channelEnabled"
                        @input="onFieldChange"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </BFormGroup>
                  </validation-provider>
                </BCol>
                <BCol :md="islogs? '12': '4'">
                  <validation-provider
                    #default="{ errors }"
                    name="Client Secret"
                    vid="client_secret"
                    mode="eager"
                    :rules="channelEnabled ? 'required' : ''"
                    slim
                  >
                    <BFormGroup
                      :state="errors.length > 0 ? false : null"
                    >
                      <template #label>
                        <div class="d-flex align-items-center">
                          <span>Client Secret</span>
                          <feather-icon
                            v-b-tooltip.hover.top.html="clientSecretTooltip"
                            class="cursor-pointer ml-1"
                            icon="InfoIcon"
                            size="14"
                          />
                        </div>
                      </template>
                      <BInputGroup
                        class="input-group-merge"
                        :state="errors.length > 0 ? false : null"
                      >
                        <BFormInput
                          id="client-secret"
                          v-model="localForm.client_secret"
                          :type="clientSecretFieldType"
                          placeholder="Enter client secret"
                          :state="errors.length > 0 ? false : null"
                          :disabled="!channelEnabled"
                          @input="onFieldChange"
                        />
                        <BInputGroupAppend is-text>
                          <feather-icon
                            class="cursor-pointer"
                            :class="!channelEnabled ? 'text-muted' : ''"
                            :icon="clientSecretToggleIcon"
                            :style="!channelEnabled ? 'pointer-events: none;' : ''"
                            @click="channelEnabled && toggleClientSecretVisibility()"
                          />
                        </BInputGroupAppend>
                      </BInputGroup>
                      <small class="text-danger">{{ errors[0] }}</small>
                    </BFormGroup>
                  </validation-provider>
                </BCol>
              </BRow>

              <BFormGroup
                label="File Extensions to Monitor"
                label-for="file-extensions"
              >
                <BFormCheckboxGroup
                  id="file-extensions"
                  v-model="localForm.extensions"
                  :options="extensionOptions"
                  :disabled="!channelEnabled"
                  class="mb-3"
                />
              </BFormGroup>
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
            </div>
            <div class="d-flex justify-content-between">
              <BButton
                variant="outline-secondary"
                @click="$emit('cancel')"
              >
                Cancel
              </BButton>
              <div class="d-flex gap-2">
                <BButton
                  variant="outline-primary"
                  type="button"
                  class="me-2"
                  :disabled="submitting || !channelEnabled"
                  @click="testConnection"
                >
                  Test Connection
                </BButton>
                <BButton
                  variant="primary"
                  type="submit"
                  :disabled="submitting"
                >
                  <span v-if="submitting">Saving...</span>
                  <span v-else>Save Configuration</span>
                </BButton>
              </div>
            </div>
          </BForm>
        </validation-observer>
      </div>
    </BCol>

    <!-- Logs Panel -->
    <BCol
      v-if="islogs"
      md="6"
      class="border-left"
    >
      <div class="p-2">
        <div class="d-flex justify-content-end mb-2">
          <BButton
            variant="outline-secondary"
            size="sm"
            @click="islogs = false"
          >
            <feather-icon
              icon="XIcon"
              size="14"
            />
          </BButton>
        </div>
        <InputChannelLogs
          service="OneDrive"
          :project="project.name"
        />
      </div>
    </BCol>
  </BRow>
</template>

<script>
import {
  BButton,
  BCol,
  BForm,
  BFormCheckbox,
  BFormCheckboxGroup,
  BFormGroup,
  BFormInput,
  BInputGroup,
  BInputGroupAppend,
  BRow,
  VBTooltip,
  BAlert,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver, extend } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import { togglePasswordVisibility } from '@core/mixins/ui/forms'
// eslint-disable-next-line no-unused-vars
import { required, email } from '@validations'
import InputChannelLogs from './InputChannelLogs.vue'

// Custom validation rule for folder URLs
extend('at_least_one_url', {
  validate(value, { other }) {
    // Check if current field has value OR the other field has value
    return !!(value && value.trim()) || !!(other && other.trim())
  },
  message: 'At least one folder URL (Transaction or Training) must be provided',
  params: ['other'],
})

export default {
  name: 'OneDriveConfig',
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BButton,
    BCol,
    BForm,
    BFormCheckbox,
    BFormCheckboxGroup,
    BFormGroup,
    BFormInput,
    BInputGroup,
    BInputGroupAppend,
    BRow,
    ValidationProvider,
    ValidationObserver,
    BAlert,
    InputChannelLogs,
  },
  mixins: [togglePasswordVisibility],
  data() {
    return {
      extensionOptions: [
        { value: 'pdf', text: 'PDF Files (.pdf)' },
        { value: 'doc', text: 'Word Documents (.doc)' },
        { value: 'docx', text: 'Word Documents (.docx)' },
        { value: 'xls', text: 'Excel Files (.xls)' },
        { value: 'xlsx', text: 'Excel Files (.xlsx)' },
        { value: 'eml', text: 'Email Files (.eml)' },
        { value: 'msg', text: 'Msg Files (.msg)' },
      ],
      submitting: false,
      islogs: false,
      clientSecretFieldType: 'password',
      errorMessage: null,
      successMessage: null,

      // Local form data - this is what the form actually uses
      localForm: {
        transaction_folder_url: '',
        training_folder_url: '',
        extensions: ['pdf', 'doc', 'docx', 'xlsx', 'xls', 'msg', 'eml'],
        client_id: '',
        client_secret: '',
        tenant_id: '',
      },
    }
  },
  computed: {
    shouldShowClearButton() {
      if (!this.channelEnabled) return false

      // Check if local form has any non-empty values
      const fields = [
        this.localForm.transaction_folder_url,
        this.localForm.training_folder_url,
        this.localForm.tenant_id,
        this.localForm.client_id,
        this.localForm.client_secret,
      ]

      return fields.some(v => typeof v === 'string' && v.trim().length > 0)
    },

    project() {
      return this.$store.getters['project/project']
    },

    // Store config - only used for reading initial data
    storeConfig() {
      const storeConfig = this.$store.getters['project/getOneDriveConfig']
      return {
        transaction_folder_url: storeConfig.transaction_folder_url || '',
        training_folder_url: storeConfig.training_folder_url || '',
        extensions: storeConfig.extensions || ['pdf', 'doc', 'docx', 'xlsx', 'xls', 'msg', 'eml'],
        client_id: storeConfig.client_id || '',
        client_secret: storeConfig.client_secret || '',
        tenant_id: storeConfig.tenant_id || '',
      }
    },

    channelEnabled: {
      get() {
        return this.$store.getters['project/isOneDriveEnabled']
      },
      set(value) {
        this.$store.dispatch('project/toggleInputChannel', {
          channelType: 'onedrive',
          enabled: value,
        })
      },
    },

    clientSecretToggleIcon() {
      return this.clientSecretFieldType === 'password' ? 'EyeIcon' : 'EyeOffIcon'
    },

    // Custom validation rule for folder URLs using local form
    folderUrlValidation() {
      return `at_least_one_url:${this.localForm.training_folder_url || ''}`
    },

    trainingFolderUrlValidation() {
      return `at_least_one_url:${this.localForm.transaction_folder_url || ''}`
    },

    // Tooltip content
    tenantIdTooltip() {
      return `
        <div style="text-align: left;">
          <strong>How to find Tenant ID </strong><br>
          Your Microsoft 365 organization ID :  <br/> (Microsoft Entra ID → Overview → Tenant ID)
        </div>
      `
    },

    clientIdTooltip() {
      return `
        <div style="text-align: left;">
          <strong>How to get Client ID</strong><br>
         Your app's Application ID : <br/> (Microsoft Entra ID → App registrations → Your App → Application ID)
        </div>
      `
    },

    clientSecretTooltip() {
      return `
        <div style="text-align: left;">
          <strong>How to create Client Secret</strong><br>
         Secret key for your app : <br /> (Microsoft Entra ID → App registrations → Your App → Certificates & Secrets → New client secret)
        </div>
      `
    },
  },

  watch: {
    channelEnabled: {
      handler() {
        this.errorMessage = null
        this.$refs.onedriveForm.reset()
      },
    },

    // Watch for changes in store config and update local form
    storeConfig: {
      handler(newConfig) {
        // Only update if local form is empty (to avoid overwriting user input)
        if (!this.shouldShowClearButton) {
          this.localForm = { ...newConfig }
        }
      },
      deep: true,
      immediate: true,
    },
  },

  destroyed() {
    this.errorMessage = null
  },

  methods: {
    showLogs() {
      this.islogs = !this.islogs
    },

    onFieldChange() {
      // Clear messages when user types
      this.errorMessage = null
      this.successMessage = null
    },

    // Clear the local form
    clearForm() {
      this.localForm = {
        transaction_folder_url: '',
        training_folder_url: '',
        extensions: ['pdf', 'doc', 'docx', 'xlsx', 'xls', 'msg', 'eml'],
        client_id: '',
        client_secret: '',
        tenant_id: '',
      }

      // Reset validation
      this.$nextTick(() => {
        this.$refs.onedriveForm.reset()
      })

      // Clear messages
      this.errorMessage = null
      this.successMessage = null
      this.clientSecretFieldType = 'password'
    },

    // Enhanced test connection method using local form data
    async testConnection() {
      // Clear previous messages
      this.errorMessage = null
      this.successMessage = null

      // Check required fields from local form
      const isValid = await this.$refs.onedriveForm.validate()

      if (!isValid) {
        this.errorMessage = 'Please fix the validation errors above before testing the connection.'
        return
      }

      try {
        const res = await this.$store.dispatch('project/testGraphConfig', {
          inputType: 'onedrive',
          payload: this.localForm, // Use local form data
        })
        this.successMessage = res.message || 'Connection test successful!'
      } catch (error) {
        this.errorMessage = error.response?.data?.error || 'Connection test failed. Please check your configuration.'
      }
    },

    toggleClientSecretVisibility() {
      this.clientSecretFieldType = this.clientSecretFieldType === 'password' ? 'text' : 'password'
    },

    toggleChannelStatus(enabled) {
      this.$store.dispatch('project/toggleInputChannel', {
        channelType: 'onedrive',
        enabled,
      })
    },

    // Custom validation method for folder URLs using local form
    validateFolderUrls() {
      const hasTransactionUrl = this.localForm.transaction_folder_url && this.localForm.transaction_folder_url.trim()
      const hasTrainingUrl = this.localForm.training_folder_url && this.localForm.training_folder_url.trim()

      return hasTransactionUrl || hasTrainingUrl
    },

    async handleSubmit() {
      try {
        // Only validate folder URLs if channel is enabled
        if (this.channelEnabled && !this.validateFolderUrls()) {
          this.errorMessage = 'At least one folder URL (Transaction or Training) must be provided'
          return
        }

        const success = await this.$refs.onedriveForm.validate()
        if (!success) return

        this.submitting = true

        // Save local form data to store
        await this.$store.dispatch('project/saveOneDriveConfig', this.localForm)

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'OneDrive Configuration Saved',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        this.$emit('save', this.localForm)
      } catch (error) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Save Failed',
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

<style scoped>
.border-left {
  border-left: 1px solid #dee2e6;
}
</style>
