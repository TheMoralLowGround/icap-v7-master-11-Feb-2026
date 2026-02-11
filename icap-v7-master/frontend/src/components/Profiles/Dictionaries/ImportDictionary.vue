<template>
  <b-modal
    v-model="showDialog"
    title="Import Dictionary"
    size="lg"
    centered
    no-close-on-backdrop
    :busy="submitting"
    @ok="submitHandler"
    @hidden="closeDialog"
  >
    <!-- OK button -->
    <template #modal-ok>
      <span>
        {{ submitting ? 'Importing...' : 'Import' }}
        <b-spinner
          v-if="submitting"
          small
        />
      </span>
    </template>

    <!-- File Input -->
    <div class="d-flex align-items-center mb-3">
      <feather-icon
        icon="PaperclipIcon"
        class="cursor-pointer mr-1"
        size="17"
        @click="$refs.fileInput.$el.querySelector('input[type=file]').click()"
      />
      <b-form-file
        ref="fileInput"
        v-model="selectedFile"
        placeholder="Upload Excel file (.xlsx, .xls)"
        accept=".xlsx,.xls"
        :clearable="true"
        class="mr-1"
      />
    </div>

    <!-- Error Message -->
    <b-alert
      v-if="errorMessage"
      variant="danger"
      show
    >
      <div class="alert-body">
        {{ errorMessage }}
      </div>
    </b-alert>
  </b-modal>
</template>

<script>
import axios from 'axios'
import {
  BModal, BFormFile,
  BAlert, BSpinner,
} from 'bootstrap-vue'

export default {
  name: 'ImportDictionary',
  components: {
    BModal,
    BFormFile,
    BAlert,
    BSpinner,
  },
  props: {
    value: { type: Boolean, default: false },
    tableName: { type: String, required: true },
  },
  data() {
    return {
      showDialog: this.value,
      errorMessage: '',
      submitting: false,
      selectedFile: null,
      selectedType: null, // Will be set dynamically based on file extension
    }
  },
  computed: {
    processUid() {
      return this.$store.getters['profile/processUid']
    },
    processKeys() {
      return this.$store.getters['profile/keys']?.map(key => key.keyValue) || []
    },
    profileId() {
      return this.$route.params.id
    },
  },
  watch: {
    // Sync with parent component
    value(newVal) {
      this.showDialog = newVal
    },
    showDialog(newVal) {
      if (!newVal) {
        this.$emit('input', false)
      }
    },
    // Watch for changes to selectedFile and set selectedType based on extension
    selectedFile(newFile) {
      if (newFile) {
        const extension = newFile.name.split('.').pop().toLowerCase()
        if (extension === 'xlsx' || extension === 'xls') {
          this.selectedType = 'excel'
        } else {
          this.errorMessage = 'Unsupported file type. Please upload a .xlsx or .xls file.'
          this.selectedFile = null // Reset file input if invalid
        }
      } else {
        this.selectedType = null
        this.errorMessage = ''
      }
    },
  },
  methods: {
    async submitHandler(bvModalEvt) {
      bvModalEvt.preventDefault()

      if (!this.selectedFile || !this.selectedType) {
        this.errorMessage = 'Please select a valid .xlsx or .xls file.'
        return
      }

      if (!this.processUid) {
        this.errorMessage = 'No process selected'
        return
      }

      this.submitting = true
      this.errorMessage = ''

      const formData = new FormData()
      formData.append('file', this.selectedFile)
      formData.append('process_keys', JSON.stringify(this.processKeys))

      try {
        // POST request with multipart/form-data using axios
        const response = await axios.post(
          '/pipeline/qdrant_vector_db/',
          formData,
          {
            params: {
              endpoint: `dictionaries/processes/${this.processUid}/tables/${this.tableName}/import`,
              request_type: 'POST',
            },
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        )

        this.$bvToast.toast('File imported successfully', {
          title: 'Success',
          variant: 'success',
          solid: true,
        })

        this.$emit('uploaded', response.data)
        this.$emit('import-success')
        this.closeDialog()
      } catch (error) {
        // Handle axios error
        let errorDetail = 'Failed to import file'
        if (error.response?.data) {
          errorDetail = error.response.data.detail || error.response.data.message || errorDetail
        } else {
          errorDetail = error.message || errorDetail
        }
        this.errorMessage = errorDetail
      } finally {
        this.submitting = false
      }
    },
    closeDialog() {
      this.showDialog = false
      this.$emit('modal-closed')
      this.resetForm()
    },
    resetForm() {
      this.selectedFile = null
      this.selectedType = null
      this.errorMessage = ''
    },
  },
}
</script>
