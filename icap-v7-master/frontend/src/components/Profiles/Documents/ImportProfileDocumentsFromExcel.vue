<template>
  <b-modal
    :visible="modelValue"
    title="Import Process Documents"
    size="md"
    centered
    no-close-on-backdrop
    @hide="close"
  >
    <b-form @submit.prevent="handleImport">
      <b-row>
        <b-col md="12">
          <b-form-group label="Select File">
            <b-form-file
              ref="fileInput"
              v-model="file"
              accept=".xlsx,.xls"
              placeholder="Choose an Excel file..."
              @change="onFileChange"
            />
          </b-form-group>
        </b-col>
      </b-row>

      <b-alert
        variant="danger"
        :show="errorMessage !== null"
        class="mt-3"
      >
        <div class="alert-body">
          <p class="mb-0">
            {{ errorMessage }}
          </p>
        </div>
      </b-alert>

      <b-alert
        variant="danger"
        :show="validationErrors.length > 0"
        class="mt-3"
      >
        <div class="alert-body">
          <p class="mb-1">
            <strong>Validation Errors Found:</strong>
          </p>
          <div class="validation-errors-container">
            <div
              v-for="(error, index) in validationErrors"
              :key="index"
              class="mb-1"
            >
              <small>Row {{ error.row }}: {{ error.message }}</small>
            </div>
          </div>
          <p class="mb-0 mt-2">
            <strong>Please fix these errors in your file and try again.</strong>
          </p>
        </div>
      </b-alert>

      <b-alert
        variant="warning"
        :show="file !== null && validationErrors.length === 0 && errorMessage === null"
        class="mt-1"
      >
        <div class="alert-body">
          <p class="mb-0">
            <strong>Warning:</strong>
            Importing will replace all existing process documents with the data from the file.
          </p>
        </div>
      </b-alert>
    </b-form>

    <template #modal-footer="{ cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        variant="primary"
        :disabled="file === null || importing || validationErrors.length > 0"
        @click="handleImport"
      >
        Import & Replace
        <b-spinner
          v-if="importing"
          small
          label="Importing..."
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import axios from 'axios'
import {
  BAlert,
  BButton,
  BCol,
  BForm,
  BFormFile,
  BFormGroup,
  BRow,
  BSpinner,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BAlert,
    BButton,
    BCol,
    BForm,
    BFormFile,
    BFormGroup,
    BRow,
    BSpinner,
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    profileId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      file: null,
      errorMessage: null,
      importing: false,
      validationErrors: [],
    }
  },
  watch: {
    modelValue(newVal) {
      if (!newVal) {
        this.resetDialog()
      }
    },
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files[0]
      if (!file) {
        this.file = null
        this.errorMessage = null
        this.validationErrors = []
        return
      }

      this.errorMessage = null
      this.validationErrors = []
      const fileName = file.name.toLowerCase()

      if (!(fileName.endsWith('.xlsx') || fileName.endsWith('.xls'))) {
        this.errorMessage = 'Unsupported file format. Please upload an Excel file (.xlsx or .xls).'
        this.file = null
      }
    },
    async handleImport() {
      if (!this.file) {
        this.errorMessage = 'Please select a file to import'
        return
      }

      this.importing = true
      this.errorMessage = null
      this.validationErrors = []

      const formData = new FormData()
      formData.append('file', this.file)

      try {
        const response = await axios.post(
          `/dashboard/profiles/${this.profileId}/import_documents/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        )

        // Show success message
        this.$toast({
          component: ToastificationContent,
          props: {
            title: response.data.detail || 'Documents imported successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        // Emit import event with success
        this.$emit('import-success')

        // Close modal after short delay
        setTimeout(() => {
          this.$emit('update:modelValue', false)
        }, 500)
      } catch (error) {
        // Handle different error scenarios
        if (error.response) {
          // Server responded with an error status
          const errorData = error.response.data

          // Check if there are validation errors
          if (errorData && errorData.validation_errors && errorData.validation_errors.length > 0) {
            this.validationErrors = errorData.validation_errors
            // Don't set errorMessage or show toast - the validation errors alert is enough
          } else {
            // Extract error message from various possible response formats
            let errorMsg = 'Failed to import documents'

            if (errorData) {
              if (errorData.detail) {
                errorMsg = errorData.detail
              } else if (errorData.error) {
                errorMsg = errorData.error
              } else if (errorData.message) {
                errorMsg = errorData.message
              } else if (typeof errorData === 'string') {
                errorMsg = errorData
              }
            }

            this.errorMessage = errorMsg
            this.$toast({
              component: ToastificationContent,
              props: {
                title: 'Import failed',
                text: this.errorMessage,
                icon: 'XIcon',
                variant: 'danger',
              },
            })
          }
        } else if (error.request) {
          // Request was made but no response received
          this.errorMessage = 'Network error. Please check your connection and try again.'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Network Error',
              text: this.errorMessage,
              icon: 'XIcon',
              variant: 'danger',
            },
          })
        } else {
          // Something else happened while setting up the request
          this.errorMessage = error.message || 'An unexpected error occurred'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Error',
              text: this.errorMessage,
              icon: 'XIcon',
              variant: 'danger',
            },
          })
        }
      } finally {
        this.importing = false
      }
    },
    resetDialog() {
      this.file = null
      this.errorMessage = null
      this.importing = false
      this.validationErrors = []
      if (this.$refs.fileInput) {
        this.$refs.fileInput.reset()
      }
    },
    close() {
      this.resetDialog()
      this.$emit('update:modelValue', false)
    },
  },
}
</script>

<style scoped>
.validation-errors-container {
  max-height: 150px;
  overflow-y: auto;
  padding: 0.5rem;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Custom scrollbar styling */
.validation-errors-container::-webkit-scrollbar {
  width: 6px;
}

.validation-errors-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.validation-errors-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.validation-errors-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
