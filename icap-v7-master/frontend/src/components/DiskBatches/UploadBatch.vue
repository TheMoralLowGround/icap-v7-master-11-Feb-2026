<template>
  <b-modal
    v-model="showModal"
    centered
    :title="`Upload Batch - ${batchId}`"
    @ok="onSubmit"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
      <b-form-group
        label="Mode:"
      >
        <b-form-radio-group
          v-model="mode"
          button-variant="outline-primary"
          :options="[
            { text: 'Training', value: 'training' },
            { text: 'Processing', value: 'processing' },
          ]"
          buttons
        />
      </b-form-group>
    </b-card-text>
    {{ batchId }}

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="submitting"
        @click="ok()"
      >
        Upload
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
  BButton, BModal, BSpinner, BCardText, BFormGroup, BFormRadioGroup,
} from 'bootstrap-vue'
import axios from 'axios'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BModal,
    BSpinner,
    BCardText,
    BFormGroup,
    BFormRadioGroup,
  },
  props: {
    batchId: {
      type: String,
      required: true,
    },
    subPath: {
      type: [String],
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      showModal: true,
      submitting: false,
      mode: 'training',
    }
  },
  methods: {
    onSubmit(event) {
      event.preventDefault()
      this.submitting = true

      axios.post('/pipeline/upload_batch/', null, {
        params: {
          batch_id: this.batchId,
          mode: this.mode,
          sub_path: this.subPath,
        },
      }).then(res => {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
        this.submitting = false
        this.$emit('uploaded')
        this.showModal = false
      }).catch(error => {
        const message = error?.response?.data?.detail || 'Error uploading batch'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
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
