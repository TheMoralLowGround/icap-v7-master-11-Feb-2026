<template>
  <div>
    <b-button
      variant="outline-primary"
      size="md"
      :disabled="loading || disabled"
      @click="openModal"
      class="mr-1"
    >
      <b-spinner
        v-if="loading"
        small
        class="mr-1"
      />
      Import All
    </b-button>

    <b-modal
      v-model="showModal"
      title="Import All Parties"
      size="lg"
      centered
      no-close-on-backdrop
      :busy="loading"
      @ok="handleImport"
      @hidden="resetForm"
    >
      <!-- OK button -->
      <template #modal-ok>
        <span>
          {{ loading ? 'Importing...' : 'Import' }}
          <b-spinner
            v-if="loading"
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

      <!-- Info Message -->
      <b-alert
        variant="info"
        show
      >
        <div class="alert-body">
          This will import all parties from the Excel file into the current process.
        </div>
      </b-alert>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios'
import {
  BButton,
  BModal,
  BFormFile,
  BAlert,
  BSpinner,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  name: 'ImportAllParties',
  components: {
    BButton,
    BModal,
    BFormFile,
    BAlert,
    BSpinner,
  },
  props: {
    disabled: { type: Boolean, default: false },
  },
  data() {
    return {
      loading: false,
      showModal: false,
      selectedFile: null,
      errorMessage: '',
    }
  },
  computed: {
    processUid() {
      return this.$store.getters['profile/processUid']
    },
    // processKeys() {
    //   return this.$store.getters['profile/keys']?.map(key => key.keyValue) || []
    // },
    profileId() {
      return this.$route.params.id
    },
  },
  watch: {
    // Watch for changes to selectedFile to validate Excel files only
    selectedFile(newFile) {
      if (newFile) {
        const extension = newFile.name.split('.').pop().toLowerCase()
        if (extension !== 'xlsx' && extension !== 'xls') {
          this.errorMessage = 'Only Excel files are supported. Please upload a .xlsx or .xls file.'
          this.selectedFile = null
        } else {
          this.errorMessage = ''
        }
      }
    },
  },
  methods: {
    openModal() {
      this.showModal = true
    },

    async handleImport(bvModalEvt) {
      bvModalEvt.preventDefault()

      if (!this.selectedFile) {
        this.errorMessage = 'Please select an Excel file (.xlsx or .xls).'
        return
      }

      if (!this.processUid) {
        this.errorMessage = 'No process selected'
        return
      }

      this.loading = true
      this.errorMessage = ''

      const formData = new FormData()
      formData.append('file', this.selectedFile)

      try {
        // POST request with multipart/form-data using axios
        const response = await axios.post(
          '/pipeline/qdrant_vector_db/',
          formData,
          {
            params: {
              endpoint: `parties/processes/${this.processUid}/import`,
              request_type: 'POST',
            },
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        )

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'All parties imported successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        // Check for warnings in response and display them
        // Response could be an array of results (one per table) or a single result
        const results = Array.isArray(response.data) ? response.data : [response.data]
        const allWarnings = []

        results.forEach(result => {
          if (result && result.warnings && result.warnings.length > 0) {
            allWarnings.push(...result.warnings)
          }
        })

        if (allWarnings.length > 0) {
          const warningMessage = allWarnings.join('\n')
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Import Warnings',
              text: warningMessage,
              icon: 'AlertTriangleIcon',
              variant: 'warning',
            },
          })
        }

        this.$emit('import-success', response.data)
        this.showModal = false
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
        this.loading = false
      }
    },

    resetForm() {
      this.selectedFile = null
      this.errorMessage = ''
    },
  },
}
</script>
