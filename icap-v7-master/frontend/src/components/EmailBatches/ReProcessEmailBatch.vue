<template>
  <b-modal
    v-model="showModal"
    centered
    title="Re-Process Email Batch"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      <div class="d-flex justify-content-center">
        <b-form-group class="pt-1">
          <b-form-radio-group
            v-model="reprocessType"
            size="small"
            button-variant="outline-primary"
            :options="[
              { text: 'All', value: 'all' },
              { text: 'Extraction', value: 'extraction' },
              { text: 'API', value: 'api' },
              { text: 'Upload Doc', value: 'uploadDoc' },
            ]"
            buttons
            @input="errorMessage = null"
          />
        </b-form-group>
      </div>

      <div
        v-if="reprocessType === 'all'"
        class="d-flex justify-content-between align-items-center"
      >
        <label class="col-form-label mb-0">Force OCR Engine</label>
        <b-form-checkbox
          v-model="forceOcrEngine"
          switch
          class="mb-0"
        />
      </div>

      <div>
        Are you sure you want to re-process the email
        <span
          v-if="ids.length === 1"
          class="text-primary"
        >batch</span>
        <span
          v-else
          class="text-primary"
        >batches</span>?
        <div
          v-for="(id, index) of ids"
          :key="index"
          class="text-primary"
        >
          {{ id }}
        </div>
      </div>
      <b-alert
        variant="danger"
        :show="hasErrors"
        class="my-1"
      >
        <div v-if="typeof errorMessage !== 'string'">
          <h5
            class="alert-body"
            style="margin-bottom: -10px;"
          >
            <strong>Unable to Re-Process the Batches</strong>
          </h5>
          <div
            v-for="(error, errorIndex) in errorMessage"
            :key="errorIndex"
            class="alert-body"
          >
            <p>{{ error.message }}</p>
            <div
              v-for="(id, idIndex) in error.ids"
              :key="idIndex"
              class="text-primary"
            >
              {{ id }}
            </div>
          </div>
        </div>
        <div v-else>
          <strong class="alert-body">{{ errorMessage }}</strong>
        </div>
      </b-alert>

    </b-card-text>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="isProcessing"
        @click="ok()"
      >
        Re-Process
        <b-spinner
          v-if="isProcessing"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import axios from 'axios'
import {
  BModal, BCardText, BButton, BSpinner, BFormRadioGroup, BFormGroup, BAlert, BFormCheckbox,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BAlert,
    BModal,
    BCardText,
    BButton,
    BSpinner,
    BFormRadioGroup,
    BFormGroup,
    BFormCheckbox,
  },
  props: {
    ids: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      isProcessing: false,
      reprocessType: 'all',
      errorMessage: null,
      forceOcrEngine: false,
    }
  },
  computed: {
    hasErrors() {
      return this.errorMessage && this.errorMessage.length > 0
    },
  },
  methods: {
    confirmHandler(event) {
      event.preventDefault()
      this.errorMessage = null

      this.isProcessing = true

      axios.post('/pipeline/re_process_email_batches/', {
        ids: this.ids,
        reprocess_type: this.reprocessType,
        force_ocr_engine: this.forceOcrEngine,
      })
        .then(() => {
          this.$emit('completed')

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Email Batches Queued for re-processing',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.errorMessage = null
          this.showModal = false
        })
        .catch(error => {
          // Check if the status code is 400
          if (error?.response?.status === 400) {
            this.errorMessage = error?.response?.data?.detail || error?.response?.data
          } else {
            this.errorMessage = error?.message
          }

          this.isProcessing = false
        })
    },
  },
}

</script>
