<template>
  <BRow class="no-gutters">
    <!-- Main Form Section -->
    <BCol :md="islogs ? 6 : 12">
      <div class="p-3">
        <validation-observer ref="emailForm">
          <BForm @submit.prevent="handleSubmit">
            <!-- Channel Status Toggle -->
            <BFormGroup class="mb-4">
              <div class="d-flex justify-content-between">
                <div class="d-flex align-items-center">
                  <label class="form-label mx-2">Email Channel Status</label>
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

            <div
              :class="channelEnabled ? '' : 'disabled'"
              :style="!channelEnabled ? 'opacity: 0.6; pointer-events: none;' : ''"
            >
              <!-- Authentication Method Selection -->
              <BFormGroup
                label="Authentication Method"
                label-for="auth-method"
              >
                <BFormRadioGroup
                  id="auth-method"
                  v-model="localAuthMethod"
                  :options="authOptions"
                  :disabled="!channelEnabled"
                  class="mb-3"
                  @input="onAuthMethodChange"
                />
              </BFormGroup>

              <!-- Basic Auth Fields -->
              <div v-if="localAuthMethod === 'BasicAuth'">
                <BRow>
                  <BCol :md="islogs ? '12' : '8'">
                    <validation-provider
                      #default="{ errors }"
                      name="Email Address"
                      vid="email"
                      mode="eager"
                      :rules="channelEnabled ? 'required' : ''"
                    >
                      <BFormGroup
                        label="Email Address"
                        label-for="email"
                        :state="errors.length > 0 ? false : null"
                      >
                        <BFormInput
                          id="email"
                          v-model="localBasicForm.email"
                          type="email"
                          placeholder="user@example.com"
                          :state="errors.length > 0 ? false : null"
                          :disabled="!channelEnabled"
                          @input="onFieldChange"
                        />
                        <small class="text-danger">{{ errors[0] }}</small>
                      </BFormGroup>
                    </validation-provider>
                  </BCol>
                  <BCol :md="islogs ? '12' : '4'">
                    <validation-provider
                      #default="{ errors }"
                      name="port"
                      vid="port"
                      mode="eager"
                      :rules="channelEnabled ? 'required' : ''"
                    >
                      <BFormGroup
                        label="Port"
                        label-for="port"
                        :state="errors.length > 0 ? false : null"
                      >
                        <BFormInput
                          id="port"
                          v-model="localBasicForm.port"
                          type="number"
                          placeholder="Enter port"
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
                  <BCol :md="islogs ? '12' : '6'">
                    <validation-provider
                      #default="{ errors }"
                      name="IMAP Server"
                      vid="server"
                      mode="eager"
                      :rules="channelEnabled ? 'required' : ''"
                    >
                      <BFormGroup
                        label="IMAP Server"
                        label-for="server"
                        :state="errors.length > 0 ? false : null"
                      >
                        <BFormInput
                          id="server"
                          v-model="localBasicForm.server"
                          placeholder="Enter server"
                          :state="errors.length > 0 ? false : null"
                          :disabled="!channelEnabled"
                          @input="onFieldChange"
                        />
                        <small class="text-danger">{{ errors[0] }}</small>
                      </BFormGroup>
                    </validation-provider>
                  </BCol>
                  <BCol :md="islogs ? '12' : '6'">
                    <validation-provider
                      #default="{ errors }"
                      name="Password"
                      vid="password"
                      mode="eager"
                      :rules="channelEnabled ? 'required' : ''"
                    >
                      <BFormGroup
                        label="Password"
                        label-for="password"
                        :state="errors.length > 0 ? false : null"
                      >
                        <BInputGroup class="input-group-merge">
                          <BFormInput
                            id="input-chanel-password"
                            v-model="localBasicForm.password"
                            :type="passwordFieldType"
                            placeholder="Enter password or app password"
                            :state="errors.length > 0 ? false : null"
                            :disabled="!channelEnabled"
                            @input="onFieldChange"
                          />
                          <BInputGroupAppend is-text>
                            <feather-icon
                              class="cursor-pointer"
                              :class="!channelEnabled ? 'text-muted' : ''"
                              :icon="passwordToggleIcon"
                              :style="!channelEnabled ? 'pointer-events: none;' : ''"
                              @click="channelEnabled && togglePasswordVisibility()"
                            />
                          </BInputGroupAppend>
                        </BInputGroup>
                        <small class="text-danger">{{ errors[0] }}</small>
                      </BFormGroup>
                    </validation-provider>
                  </BCol>
                </BRow>
              </div>

              <!-- OAuth 2.0 Fields -->
              <div v-if="localAuthMethod === 'OAuth'">
                <BRow>
                  <BCol md="12">
                    <validation-provider
                      #default="{ errors }"
                      name="Mailbox IDs"
                      vid="mailbox_ids"
                      mode="eager"
                      :rules="channelEnabled ? 'required' : ''"
                    >
                      <BFormGroup
                        label="Mailbox Email Addresses"
                        label-for="mailbox-tags"
                        :state="errors.length > 0 ? false : null"
                      >
                        <BFormTags
                          v-model="localOauthForm.mailbox_ids"
                          input-id="mailbox-tags"
                          placeholder="Type email and press Enter"
                          :state="errors.length > 0 ? false : null"
                          :input-attrs="{ placeholder: 'user@example.com' }"
                          :tag-validator="validateEmailTag"
                          :disabled="!channelEnabled"
                          separator=", "
                          remove-on-delete
                          @input="onFieldChange"
                        />
                        <small class="text-danger">{{ errors[0] }}</small>
                      </BFormGroup>
                    </validation-provider>
                  </BCol>
                </BRow>

                <BRow>
                  <BCol :md="islogs ? '12' : '4'">
                    <validation-provider
                      #default="{ errors }"
                      name="Tenant ID"
                      vid="tenant_id"
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
                          v-model="localOauthForm.tenant_id"
                          placeholder="Enter Tenant ID"
                          :state="errors.length > 0 ? false : null"
                          :disabled="!channelEnabled"
                          @input="onFieldChange"
                        />
                        <small class="text-danger">{{ errors[0] }}</small>
                      </BFormGroup>
                    </validation-provider>
                  </BCol>
                  <BCol :md="islogs ? '12' : '4'">
                    <validation-provider
                      #default="{ errors }"
                      name="Client ID"
                      vid="client_id"
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
                          v-model="localOauthForm.client_id"
                          placeholder="Enter Client ID"
                          :state="errors.length > 0 ? false : null"
                          :disabled="!channelEnabled"
                          @input="onFieldChange"
                        />
                        <small class="text-danger">{{ errors[0] }}</small>
                      </BFormGroup>
                    </validation-provider>
                  </BCol>

                  <BCol :md="islogs ? '12' : '4'">
                    <validation-provider
                      #default="{ errors }"
                      name="Client Secret"
                      vid="client_secret"
                      mode="eager"
                      :rules="channelEnabled ? 'required' : ''"
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
                        <BInputGroup class="input-group-merge">
                          <BFormInput
                            id="client-secret"
                            v-model="localOauthForm.client_secret"
                            :type="clientSecretFieldType"
                            placeholder="Enter Client Secret"
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
              </div>

              <!-- Error and Success Messages -->
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

            <!-- Action Buttons -->
            <div class="d-flex justify-content-between mt-2">
              <BButton
                variant="outline-secondary"
                @click="$emit('cancel')"
              >
                Cancel
              </BButton>
              <div class="d-flex gap-2">
                <BButton
                  variant="outline-primary"
                  :disabled="submitting || !channelEnabled"
                  @click="testConnection"
                >
                  <span v-if="submitting">Testing...</span>
                  <span v-else>Test Connection</span>
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
          :service="localAuthMethod"
          :project="project.name"
        />
      </div>
    </BCol>
  </BRow>
</template>

<script>
import {
  BAlert,
  BButton,
  BCol,
  BForm,
  BFormCheckbox,
  BFormGroup,
  BFormInput,
  BFormRadioGroup,
  BFormTags,
  BInputGroup,
  BRow,
  BInputGroupAppend,
  VBTooltip,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import { togglePasswordVisibility } from '@core/mixins/ui/forms'
import InputChannelLogs from './InputChannelLogs.vue'

export default {
  name: 'EmailConfig',
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BAlert,
    BButton,
    BCol,
    BForm,
    BFormCheckbox,
    BFormGroup,
    BFormInput,
    BFormRadioGroup,
    BFormTags,
    BRow,
    ValidationProvider,
    ValidationObserver,
    BInputGroupAppend,
    BInputGroup,
    InputChannelLogs,
  },
  mixins: [togglePasswordVisibility],
  data() {
    return {
      authOptions: [
        { text: 'OAuth 2.0', value: 'OAuth' },
        { text: 'Basic Authentication', value: 'BasicAuth' },
      ],
      errorMessage: null,
      successMessage: null,
      submitting: false,
      islogs: false,
      clientSecretFieldType: 'password',

      // Local auth method
      localAuthMethod: 'OAuth',

      // Local form data for BasicAuth
      localBasicForm: {
        email: '',
        server: '',
        port: '',
        password: '',
      },

      // Local form data for OAuth
      localOauthForm: {
        client_id: '',
        tenant_id: '',
        client_secret: '',
        mailbox_ids: [],
      },
    }
  },
  computed: {
    shouldShowClearButton() {
      if (!this.channelEnabled) return false

      // Check BasicAuth fields
      const basicFields = [
        this.localBasicForm.email,
        this.localBasicForm.server,
        this.localBasicForm.port,
        this.localBasicForm.password,
      ]

      // Check OAuth fields
      const oauthFields = [
        this.localOauthForm.client_id,
        this.localOauthForm.tenant_id,
        this.localOauthForm.client_secret,
      ]

      const hasBasicData = basicFields.some(v => typeof v === 'string' && v.trim().length > 0)
      const hasOauthData = oauthFields.some(v => typeof v === 'string' && v.trim().length > 0)
                          || (this.localOauthForm.mailbox_ids && this.localOauthForm.mailbox_ids.length > 0)

      return hasBasicData || hasOauthData
    },

    project() {
      return this.$store.getters['project/project']
    },

    // Store config - only used for reading initial data
    storeConfig() {
      const storeConfig = this.$store.getters['project/getEmailConfig']
      return {
        authMethod: storeConfig.authMethod || 'OAuth',
        // BasicAuth fields
        email: storeConfig.email || '',
        server: storeConfig.server || '',
        port: storeConfig.port || '',
        password: storeConfig.password || '',
        // OAuth fields
        client_id: storeConfig.client_id || '',
        tenant_id: storeConfig.tenant_id || '',
        client_secret: storeConfig.client_secret || '',
        mailbox_ids: storeConfig.mailbox_ids || [],
      }
    },

    channelEnabled: {
      get() {
        return this.$store.getters['project/isEmailEnabled']
      },
      set(value) {
        this.$store.dispatch('project/toggleInputChannel', {
          channelType: 'email',
          enabled: value,
        })
      },
    },

    passwordToggleIcon() {
      return this.passwordFieldType === 'password' ? 'EyeIcon' : 'EyeOffIcon'
    },

    clientSecretToggleIcon() {
      return this.clientSecretFieldType === 'password' ? 'EyeIcon' : 'EyeOffIcon'
    },

    // Tooltip content
    tenantIdTooltip() {
      return `
        <div style="text-align: left;">
          <strong>How to find Tenant ID</strong><br>
          Your Microsoft 365 organization ID: <br/> (Microsoft Entra ID → Overview → Tenant ID)
        </div>
      `
    },

    clientIdTooltip() {
      return `
        <div style="text-align: left;">
          <strong>How to get Client ID</strong><br>
          Your app's Application ID: <br/> (Microsoft Entra ID → App registrations → Your App → Application ID)
        </div>
      `
    },

    clientSecretTooltip() {
      return `
        <div style="text-align: left;">
          <strong>How to create Client Secret</strong><br>
          Secret key for your app: <br /> (Microsoft Entra ID → App registrations → Your App → Certificates & Secrets → New client secret)
        </div>
      `
    },
  },

  watch: {
    channelEnabled: {
      handler() {
        this.errorMessage = null
        this.$refs.emailForm.reset()
      },
    },

    // Watch for changes in store config and update local forms
    storeConfig: {
      handler(newConfig) {
        // Only update if local forms are empty (to avoid overwriting user input)
        if (!this.shouldShowClearButton) {
          this.localAuthMethod = newConfig.authMethod
          this.localBasicForm = {
            email: newConfig.email,
            server: newConfig.server,
            port: newConfig.port,
            password: newConfig.password,
          }
          this.localOauthForm = {
            client_id: newConfig.client_id,
            tenant_id: newConfig.tenant_id,
            client_secret: newConfig.client_secret,
            mailbox_ids: newConfig.mailbox_ids,
          }
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
    validateEmailTag(tag) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(tag.trim())
    },

    onFieldChange() {
      // Clear messages when user types
      this.errorMessage = null
      this.successMessage = null
    },

    onAuthMethodChange() {
      // Clear messages when auth method changes
      this.errorMessage = null
      this.successMessage = null
      // Reset validation
      this.$nextTick(() => {
        this.$refs.emailForm.reset()
      })
    },

    // Clear all local forms
    clearForm() {
      // this.localAuthMethod = 'OAuth'
      this.localBasicForm = {
        email: '',
        server: '',
        port: '',
        password: '',
      }
      this.localOauthForm = {
        client_id: '',
        tenant_id: '',
        client_secret: '',
        mailbox_ids: [],
      }

      // Reset validation
      this.$nextTick(() => {
        this.$refs.emailForm.reset()
      })

      // Clear messages and reset password fields
      this.errorMessage = null
      this.successMessage = null
      this.clientSecretFieldType = 'password'
      this.passwordFieldType = 'password'
    },

    // Enhanced test connection with proper validation
    async testConnection() {
      // Clear previous messages
      this.errorMessage = null
      this.successMessage = null

      const success = await this.$refs.emailForm.validate()
      if (!success) {
        this.errorMessage = 'Please fix the validation errors above before testing the connection.'
        return
      }

      try {
        let res
        if (this.localAuthMethod === 'BasicAuth') {
          res = await this.$store.dispatch('project/testImapConfig', {
            payload: this.localBasicForm,
          })
        } else {
          res = await this.$store.dispatch('project/testGraphConfig', {
            inputType: 'email',
            payload: this.localOauthForm,
          })
        }

        this.successMessage = res.message || 'Connection test successful!'
      } catch (error) {
        this.errorMessage = error.response?.data?.error || 'Connection test failed. Please check your configuration.'
      }
    },

    toggleChannelStatus(enabled) {
      this.$store.dispatch('project/toggleInputChannel', {
        channelType: 'email',
        enabled,
      })
    },

    toggleClientSecretVisibility() {
      this.clientSecretFieldType = this.clientSecretFieldType === 'password' ? 'text' : 'password'
    },

    showLogs() {
      this.islogs = !this.islogs
    },

    async handleSubmit() {
      try {
        // Only validate if channel is enabled
        if (this.channelEnabled) {
          const success = await this.$refs.emailForm.validate()
          if (!success) return
        }

        this.submitting = true

        // Prepare config based on auth method
        let config = { authMethod: this.localAuthMethod }

        if (this.localAuthMethod === 'BasicAuth') {
          config = {
            ...config,
            ...this.localBasicForm,
          }
        } else {
          config = {
            ...config,
            ...this.localOauthForm,
          }
        }

        // Save to store
        await this.$store.dispatch('project/saveEmailConfig', config)

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Email Configuration Saved',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        this.$emit('save', config)
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
