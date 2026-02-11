<template>
  <div>
    <div class="d-flex align-items-center justify-content-start gap-3 ">
      <b-button
        variant="outline-primary"
        @click="openImportModal"
      >
        Import
      </b-button>
      <b-button
        variant="outline-primary"
        @click="exportProject(project)"
      >
        Export
        <b-spinner
          v-if="isExporting"
          small
          label="Exporting..."
        />
      </b-button>
    </div>

    <!-- Import Modal -->
    <b-modal
      id="import-modal"
      v-model="showImportModal"
      title="Import Project"
      centered
      :ok-disabled="loading || (showConfirmationCheckbox && !acceptMismatchProject)"
      :ok-title="'Submit'"
      :cancel-disabled="loading"
      @ok.prevent="submitImport"
    >
      <b-form>
        <b-form-file
          ref="fileInput"
          v-model="jsonFile"
          accept=".json"
          placeholder="Choose a JSON file..."
          class="mb-3"
          @change="handleFileUpload"
        />
        <b-form-checkbox
          v-if="!partialImport"
          v-model="form.replace_settings"
          class="mb-3"
        >
          Replace Settings
        </b-form-checkbox>
        <template v-if="showConfirmationCheckbox">
          <small class="text-danger"> Project Mismatched</small>
          <b-form-checkbox
            v-model="acceptMismatchProject"
          >
            Import with different Project
          </b-form-checkbox>
        </template>
      </b-form>

      <b-alert
        v-if="errorMessage"
        variant="danger"
        show
        class="mt-3"
      >
        {{ errorMessage }}
      </b-alert>
      <template #modal-ok>
        <b-spinner
          v-if="loading"
          small
          class="mr-1"
          label="Submitting"
        />
        {{ loading ? 'Submitting...' : 'Submit' }}
      </template>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios'
import {
  BAlert,
  BButton,
  BForm,
  BFormCheckbox,
  BFormFile,
  BModal,
  BSpinner,
} from 'bootstrap-vue'
import exportFromJSON from 'export-from-json'

export default {
  components: {
    BButton,
    BSpinner,
    BModal,
    BForm,
    BFormFile,
    BFormCheckbox,
    BAlert,
  },
  props: {
    exportSettingsItem: {
      type: String,
      default: '',
    },
    importSettingsItem: {
      type: String,
      default: '',
    },
    project: {
      type: Object,
      default: () => ({}),
    },
    partialImport: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      isExporting: false,
      showImportModal: false,
      loading: false,
      jsonFile: null,
      uploadedData: [],
      form: {
        replace_settings: false,
      },
      acceptMismatchProject: false,
      errorMessage: null,
    }
  },
  computed: {
    showConfirmationCheckbox() {
      return this.uploadedData.length ? this.project.name !== this.uploadedData[0].name : false
    },
  },
  methods: {
    openImportModal() {
      this.showImportModal = true
      this.errorMessage = null
      this.loading = false
      this.jsonFile = null
      this.uploadedData = []
      this.form.replace_settings = false
    },

    handleFileUpload(event) {
      let file

      // Check for drag and drop event first
      if (event.dataTransfer && event.dataTransfer.files) {
        [file] = event.dataTransfer.files
      } else if (event.target && event.target.files) {
        [file] = event.target.files
      }

      // Fall back to this.jsonFile if neither exists
      file = file || this.jsonFile

      if (!file) {
        this.errorMessage = 'No file selected.'
        return
      }

      const reader = new FileReader()
      reader.onload = e => {
        try {
          const parsedData = JSON.parse(e.target.result)
          this.uploadedData = parsedData
          this.errorMessage = null
        } catch (err) {
          this.errorMessage = 'Invalid JSON format.'
          // Reset file input so user can select the same file again after fixing it
          this.resetFileInput()
        }
      }
      reader.readAsText(file)
    },

    async fetchProject() {
      await this.$store.dispatch('project/fetchProjectDetail', this.$route.params.id)
    },
    submitImport() {
      if (!this.uploadedData.length) {
        this.errorMessage = 'Please upload a valid JSON file.'
        return
      }
      if (this.uploadedData.length && this.uploadedData[0].name !== this.project.name) {
        this.uploadedData[0].name = this.project.name
      }

      this.loading = true
      const payload = {
        replace_settings: this.form.replace_settings,
        projects: this.uploadedData,
        import_settings_item: this.exportSettingsItem,
      }

      axios.post('/dashboard/admin/projects/import/', payload)
        .then(res => {
          this.$toast.success(res.data.detail || 'Import successful')
          this.resetImportForm()
          this.showImportModal = false
          this.fetchProject()
        })
        .catch(err => {
          this.errorMessage = err?.response?.data?.detail || 'Import failed.'
          // Reset file input so user can select the same file again after fixing it
          this.resetFileInput()
        })
        .finally(() => {
          this.loading = false
        })
    },

    resetFileInput() {
      // Reset the file input value so the same file can be selected again
      this.jsonFile = null
      this.uploadedData = []
      if (this.$refs.fileInput) {
        this.$refs.fileInput.reset()
      }
    },

    resetImportForm() {
      this.jsonFile = null
      this.uploadedData = []
      this.form.replace_settings = false
      this.errorMessage = null
      if (this.$refs.fileInput) {
        this.$refs.fileInput.reset()
      }
    },

    exportProject(project) {
      const fileName = `Project-${project.name}-${this.exportSettingsItem}`
      const payload = {
        ids: [project.id],
        export_all: false,
        export_settings_item: this.exportSettingsItem,
      }
      this.exportProjects(payload, fileName)
    },

    exportProjects(data, fileName) {
      this.isExporting = true
      return axios.post('/dashboard/admin/projects/export/', data)
        .then(res => {
          exportFromJSON({
            data: Array.isArray(res.data) ? res.data : [res.data],
            fileName,
            exportType: 'json',
          })
          this.$toast.success('Project exported successfully')
        })
        .catch(() => {
          this.$toast.error('Failed to export project')
        })
        .finally(() => {
          this.isExporting = false
        })
    },
  },
}
</script>
