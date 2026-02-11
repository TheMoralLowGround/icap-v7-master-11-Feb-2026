<template>
  <b-modal
    v-model="showModal"
    size="md"
    title="Upload Document"
    centered
    no-close-on-backdrop
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form @submit.prevent="onSubmit">
      <div
        v-if="loading"
        class="text-center my-1"
      >
        <b-spinner
          variant="primary"
          label="Spinner"
        />
      </div>

      <b-alert
        variant="danger"
        :show="loadingError !== null ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ loadingError }}
          </p>
        </div>
      </b-alert>
      <div v-if="!loading && !loadingError">
        <div class="mb-1">
          Template: {{ template.template_name }}
        </div>
        <b-form-group
          label="Upload Document (.xlsx and .xls only)"
        >
          <b-form-file
            v-model="uploadedFiles"
            :accept="['.xlsx', '.xls']"
            multiple
          />
        </b-form-group>
      </div>
      <b-alert
        :show="submitResult.display"
        :variant="submitResult.error ? 'danger': 'success'"
      >
        <div class="alert-body">
          <p>
            {{ submitResult.message }}
          </p>
          <p v-if="submitResult.createdBatches.length > 0">
            Created Batches: {{ submitResult.createdBatches.join(", ") }}
          </p>
        </div>
      </b-alert>
    </b-form>
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
        :disabled="submitting || !uploadedFiles.length"
        @click="onSubmit"
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
  BModal, BForm, BButton, BSpinner, BFormGroup, BFormFile, BAlert,
} from 'bootstrap-vue'
import axios from 'axios'
// import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BForm,
    BButton,
    BSpinner,
    BFormGroup,
    BFormFile,
    BAlert,
  },
  props: {
    template: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      submitting: false,
      loading: false,
      loadingError: null,
      uploadedFiles: [],
      submitResult: {
        display: false,
        error: false,
        message: null,
        createdBatches: [],
      },
    }
  },
  methods: {
    onSubmit() {
      this.submitting = true
      const formData = new FormData()
      formData.append('upload_type', 'excel')
      this.uploadedFiles.forEach(uploadedFile => {
        formData.append('excel_file', uploadedFile)
      })
      formData.append('template_name', this.template.template_name)
      // const message = 'document upload successfully'

      axios.post('/dashboard/template_upload_document/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
        .then(res => {
          this.submitResult = {
            display: true,
            error: false,
            message: res.data.detail,
            createdBatches: res.data.created_batches,
          }
          this.submitting = false
          this.uploadedFiles = []
        })
        .catch(error => {
          this.submitResult = {
            display: true,
            error: true,
            message: error?.response?.data?.detail || 'Error submitting training documents',
            createdBatches: error?.response?.data?.created_batches || [],
          }
          this.submitting = false
        })
    },
  },
}
</script>
