<template>
  <b-modal
    v-model="showModal"
    :title="`${mode.charAt(0).toUpperCase() + mode.slice(1)} Definition`"
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <validation-observer
      ref="definitionForm"
    >
      <b-form @submit.prevent="onSubmit">
        <b-row>
          <b-col
            md="12"
          >
            <validation-provider
              #default="{ errors }"
              name="Profile ID"
              vid="profileId"
              mode="eager"
            >
              <b-form-group
                label="Profile ID"
              >
                <b-form-input
                  v-model="profileId"
                  type="text"
                  placeholder="Profile ID"
                  :state="errors.length > 0 ? false:null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>

          <b-col
            md="12"
          >
            <validation-provider
              #default="{ errors }"
              name="Customer"
              vid="vendor"
              mode="eager"
            >
              <b-form-group
                label="Customer"
              >
                <b-form-input
                  v-model="vendor"
                  type="text"
                  placeholder="Customer"
                  :state="errors.length > 0 ? false:null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>

          <b-col
            md="12"
          >
            <validation-provider
              #default="{ errors }"
              name="Type"
              vid="type"
              mode="eager"
            >
              <b-form-group
                label="Type"
                :state="errors.length > 0 ? false:null"
              >
                <v-select
                  v-model="type"
                  transition=""
                  :label="options['options-meta-root-type'].lableKey"
                  :options="options['options-meta-root-type'].items"
                  :reduce="option => option[options['options-meta-root-type'].valueKey]"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>

          <b-col
            md="12"
          >
            <b-form-checkbox
              v-model="cw1"
            >
              Cw1
            </b-form-checkbox>
          </b-col>
        </b-row>

        <b-alert
          variant="danger"
          :show="errorMessage !== null ? true : false"
          class="my-1"
        >
          <div class="alert-body">
            <p>
              {{ errorMessage }}
            </p>
          </div>
        </b-alert>

        <b-row v-if="definitionExists">
          <b-col
            md="12"
          >
            <b-form-checkbox
              v-model="override"
            >
              Overwrite Definition
            </b-form-checkbox>
          </b-col>
        </b-row>
      </b-form>
    </validation-observer>
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        variant="primary"
        type="submit"
        :disabled="submitting"
        @click="ok()"
      >
        Submit
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>

</template>

<script>
import {
  BRow, BCol, BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormInput, BFormCheckbox,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import vSelect from 'vue-select'
import axios from 'axios'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    vSelect,
    BRow,
    BCol,
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    BFormInput,
    BModal,
    BFormCheckbox,
  },
  // props data coming from parent
  props: {
    mode: {
      type: String,
      required: true,
    },
    definition: {
      type: Object,
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      // Stores the profile ID of the definition
      profileId: null,
      // Vendor name for the definition
      vendor: '',
      // Type of the definition
      type: '',
      // Boolean flag indicating whether CW1 is enabled
      cw1: true,
      // Indicates whether a submission is in progress
      submitting: false,
      // Stores error messages for display
      errorMessage: null,
      // Controls the visibility of the modal
      showModal: true,
      // Indicates if the definition already exists
      definitionExists: false,
      // Controls whether to override the existing definition
      override: false,
    }
  },
  computed: {
    // Fetches the options for definition settings from the Vuex store
    options() {
      return this.$store.getters['definitionSettings/options']
    },
  },
  watch: {
    // Watches changes to `definitionExists`
    definitionExists() {
      // If the definition does not exist, reset the `override` flag
      if (!this.definitionExists) {
        this.override = false
      }
    },
  },
  created() {
    // Initializes data properties if a definition is provided
    if (this.definition) {
      this.profileId = this.definition.definition_id
      this.vendor = this.definition.vendor
      this.type = this.definition.type
      this.cw1 = this.definition.cw1
    }
  },
  methods: {
    // Handles form submission
    onSubmit(event) {
      event.preventDefault() // Prevents the default form submission

      // Validates the form before proceeding
      this.$refs.definitionForm.validate().then(success => {
        if (!success) {
          return
        }
        this.submitting = true // Sets the submitting state to true

        // Prepares the data payload for the API request
        const data = {
          definition_id: this.profileId,
          vendor: this.vendor,
          type: this.type,
          cw1: this.cw1,
        }

        let request = null // Holds the Axios request object
        let message = null // Holds the success message

        // Determines the mode of operation (add, edit, or clone) and sets the appropriate request and message
        if (this.mode === 'add') {
          request = axios.post('/definitions/', data)
          message = 'Definition created successfully'
        } else if (this.mode === 'edit') {
          request = axios.patch(`/definitions/${this.definition.id}/`, data)
          message = 'Definition updated successfully'
        } else if (this.mode === 'clone') {
          request = axios.post('/definitions/clone/', {
            reference_id: this.definition.id,
            override: this.override,
            ...data,
          })
          message = 'Definition cloned successfully'
        }

        // Executes the API request
        request
          .then(() => {
            // Shows a success notification
            this.$toast({
              component: ToastificationContent,
              props: {
                title: message,
                icon: 'CheckIcon',
                variant: 'success',
              },
            })
            this.submitting = false // Resets the submitting state
            this.errorMessage = null // Clears any error messages
            this.$emit('saved') // Emits a saved event
            this.showModal = false // Hides the modal
          })
          .catch(error => {
            // Handles server-side errors
            const serverErrors = error?.response?.data
            if (serverErrors) {
              if (serverErrors.non_field_errors) {
                // Displays non-field errors
                // eslint-disable-next-line prefer-destructuring
                this.errorMessage = serverErrors.non_field_errors[0]
              } else {
                this.errorMessage = null
              }
              // Sets field-specific errors in the form
              this.$refs.definitionForm.setErrors({
                profileId: serverErrors.definition_id,
                vendor: serverErrors.vendor,
                type: serverErrors.type,
              })
            } else {
              this.errorMessage = null
              // Shows a generic error notification
              this.$toast({
                component: ToastificationContent,
                props: {
                  title: error?.response?.data?.detail || 'Something went wrong',
                  icon: 'AlertTriangleIcon',
                  variant: 'danger',
                },
              })
            }

            // Updates the `definitionExists` flag based on the error response
            if (serverErrors && serverErrors.definition_exists) {
              this.definitionExists = true
            } else {
              this.definitionExists = false
            }
            this.submitting = false // Resets the submitting state
          })
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
