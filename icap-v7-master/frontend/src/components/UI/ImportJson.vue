<template>
  <b-modal
    v-model="showModal"
    :title="`Import ${title}`"
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form @submit.prevent="onSubmit">
      <b-form-group
        :label="`${title} JSON File`"
      >
        <b-form-file
          v-model="file"
          accept=".json"
          :disabled="loadingFile"
          @input="loadFile"
        />
      </b-form-group>
      <b-form-checkbox
        v-if="!isOverwriteEnabled"
        v-model="ignoreFields"
      >
        Ignore Mismatched Fields
      </b-form-checkbox>

      <div
        v-if="loadingFile"
        class="text-center"
      >
        <b-spinner
          variant="primary"
          label="Spinner"
        />
      </div>

      <b-alert
        variant="danger"
        :show="fileLoadError !== null ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ fileLoadError }}
          </p>
        </div>
      </b-alert>
      <b-form-group
        v-if="isOverwriteEnabled"
      >
        <b-form-checkbox
          v-model="overwrite"
        >
          Overwrite
        </b-form-checkbox>
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
  BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormFile, BFormCheckbox,
} from 'bootstrap-vue'
import axios from 'axios'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BAlert,
    BModal,
    BFormFile,
    BFormCheckbox,
  },
  props: {
    title: {
      type: String,
      required: true,
    },
    url: {
      type: String,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    project: {
      type: String,
      required: false,
      default: () => null,
    },
  },
  data() {
    return {
      file: null,
      parsedData: null,
      loadingFile: false,
      fileLoadError: null,
      submitting: false,
      showModal: true,
      overwrite: false,
      ignoreFields: false,
    }
  },
  computed: {
    enableSubmit() {
      // return Array.isArray(this.parsedData) ? this.parsedData.length > 0 : this.parsedData
      return this.parsedData
    },
    isOverwriteEnabled() {
      return ['application_settings'].includes(this.field)
    },
  },
  methods: {
    async loadFile() {
      if (!this.file) {
        this.parsedData = null
        this.fileLoadError = null
        return
      }

      this.loadingFile = true

      this.parseDefinitionSettings()
        .then(parsedData => {
          this.parsedData = parsedData
          this.fileLoadError = null
          this.loadingFile = false
        })
        .catch(error => {
          this.parsedData = null
          this.fileLoadError = error.message
          this.loadingFile = false
        })
    },
    parseDefinitionSettings() {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = event => {
          const data = event.target.result
          try {
            const parsedData = JSON.parse(data)
            resolve(parsedData)
          } catch (error) {
            reject(error)
          }
        }
        reader.readAsText(this.file)
      })
    },
    onSubmit(event) {
      event.preventDefault()
      this.submitting = true

      const payload = {}
      delete this.parsedData[0]?.definitions

      payload[this.field] = this.parsedData

      if (this.project) {
        payload.project = this.project
      }

      if (this.isOverwriteEnabled) {
        payload.overwrite = this.overwrite
      } else {
        payload.ignore_fields = this.ignoreFields
      }

      axios.post(this.url, payload)
        .then(res => {
          let message = res.data.detail
          if (message.includes('Profiles')) {
            message = 'Processes Imported'
          }
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.submitting = false
          this.$emit('imported')
          this.showModal = null
        })
        .catch(error => {
          let msg = error?.response?.data?.detail
          if (msg.includes('Profile')) {
            msg = msg.replace('Profile', 'Process')
          }
          this.fileLoadError = msg
          this.submitting = false
        })
    },
  },
}
</script>
