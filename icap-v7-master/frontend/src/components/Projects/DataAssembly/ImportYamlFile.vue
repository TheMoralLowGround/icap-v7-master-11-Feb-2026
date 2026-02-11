<template>
  <div>
    <b-modal
      v-model="showImportModal"
      title="Import YAML Configuration"
      centered
      size="md"
      :no-close-on-backdrop="loading"
      :no-close-on-esc="loading"
      @ok.prevent="submitImport"
    >
      <b-form>
        <div class="mb-4">
          <label class="form-label fw-bold">Upload YAML File</label>
          <b-form-file
            v-model="yamlFile"
            accept=".yaml,.yml"
            placeholder="Choose a YAML file..."
            class="mb-1"
            @input="handleFileUpload"
          />
          <small class="text-muted">Supported formats: .yaml, .yml</small>

          <!-- Replace Data Checkbox -->
          <div class="mt-1">
            <b-form-checkbox
              v-model="replaceData"
            >
              Replace existing Keys
            </b-form-checkbox>
          </div>

          <!-- Success Message -->
          <b-alert
            v-if="successMessage"
            variant="success"
            show
            class="mt-2 p-1"
          >
            {{ successMessage }}
          </b-alert>

          <!-- Error Message -->
          <b-alert
            v-if="errorMessage"
            variant="danger"
            show
            class="mt-2 p-1"
          >
            {{ errorMessage }}
          </b-alert>
        </div>
      </b-form>

      <template #modal-footer="{ ok, cancel }">
        <b-button
          variant="secondary"
          :disabled="loading"
          @click="cancel()"
        >
          Cancel
        </b-button>
        <b-button
          variant="primary"
          :disabled="loading || !yamlFile || errorMessage"
          @click="ok()"
        >
          Upload
          <b-spinner
            v-if="loading"
            small
          />
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios'
import {
  BAlert,
  BForm,
  BFormFile,
  BFormCheckbox,
  BModal,
  BSpinner,
  BButton,
} from 'bootstrap-vue'

export default {
  name: 'YamlUploadComponent',
  components: {
    BSpinner,
    BModal,
    BForm,
    BFormFile,
    BFormCheckbox,
    BAlert,
    BButton,
  },
  props: {
    value: {
      type: Boolean,
      required: true,
    },
    projectId: {
      type: [Number, String],
      default: undefined,
    },
  },
  data() {
    return {
      loading: false,
      yamlFile: null,
      replaceData: false,
      errorMessage: null,
      successMessage: null,
    }
  },
  computed: {
    showImportModal: {
      get() {
        return this.value
      },
      set(val) {
        this.$emit('input', val)
        if (!val) this.resetForm()
      },
    },
    projectIdValue() {
      return this.projectId || this.$route?.params?.id
    },
  },
  methods: {
    handleFileUpload(file) {
      if (!file) {
        this.errorMessage = 'No file selected.'
        this.successMessage = null
        return
      }

      const fileName = file.name.toLowerCase()
      if (!fileName.endsWith('.yaml') && !fileName.endsWith('.yml')) {
        this.errorMessage = 'Please select a valid YAML file (.yaml or .yml)'
        this.successMessage = null
        return
      }

      this.errorMessage = null
      this.successMessage = null
    },

    submitImport() {
      if (!this.yamlFile) {
        this.errorMessage = 'Please select a YAML file first.'
        this.successMessage = null
        return
      }

      this.loading = true
      this.errorMessage = null
      this.successMessage = null

      const formData = new FormData()
      formData.append('file', this.yamlFile)
      formData.append('replace_data', this.replaceData)

      const apiUrl = `/dashboard/upload_yaml_file/${this.projectIdValue}`

      axios.post(apiUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
        .then(res => {
          this.successMessage = 'YAML file uploaded successfully!'
          this.$emit('imported', res.data)
        })
        .catch(err => {
          const errorMsg = err?.response?.data?.detail || 'Import failed. Please try again.'
          this.errorMessage = errorMsg
        })
        .finally(() => {
          this.loading = false
        })
    },

    resetForm() {
      this.yamlFile = null
      this.replaceData = false
      this.errorMessage = null
      this.successMessage = null
    },
  },
}
</script>

<style scoped>
.form-label {
  margin-bottom: 0.5rem;
}
</style>
