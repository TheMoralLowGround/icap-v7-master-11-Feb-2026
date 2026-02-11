<template>
  <b-modal
    v-model="showModal"
    title="Upload Email Batch"
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form @submit.prevent="onSubmit">
      <b-form-group
        label="Email File (.eml or .msg):"
      >
        <b-form-file
          v-model="emailFile"
          accept=".eml,.msg"
        />
      </b-form-group>
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
        :disabled="submitting || !enableSubmit"
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
  BFormGroup, BButton, BForm, BSpinner, BModal, BFormFile,
} from 'bootstrap-vue'
import axios from 'axios'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BModal,
    BFormFile,
  },
  data() {
    return {
      emailFile: null,
      submitting: false,
      showModal: true,
    }
  },
  computed: {
    enableSubmit() {
      return this.emailFile
    },
  },
  methods: {
    onSubmit(event) {
      event.preventDefault()
      this.submitting = true

      const formData = new FormData()
      formData.append('email_file', this.emailFile)

      axios.post('/pipeline/upload_email_batch/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: `${res.data.detail}\nEmail Batch Id: ${res.data.batch_id}`,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.submitting = false
          this.$emit('uploaded')
          this.showModal = false
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error uploading email batch',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.submitting = false
        })
    },
  },
}
</script>
