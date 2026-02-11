<template>
  <b-modal
    v-model="showModal"
    title="Import Template(s)"
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form @submit.prevent="onSubmit">
      <b-form-group
        label="Template(s) json file"
      >
        <b-form-file
          v-model="templateFile"
          accept=".json"
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
        :disabled="submitting || !templateFile"
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
      templateFile: null,
      submitting: false,
      showModal: true,
    }
  },
  computed: {
  },
  methods: {
    onSubmit(event) {
      event.preventDefault()
      this.submitting = true
      this.parseDefinitions()
        .then(parsedTemplate => {
          this.profileDefinitions = parsedTemplate
          this.submitting = false
          axios.post('/dashboard/import_templates/', parsedTemplate, {
          })
            .then(res => {
              this.$toast({
                component: ToastificationContent,
                props: {
                  title: `${res.data.detail}`,
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
        })
        .catch(() => {
          this.submitting = false
        })
    },
    parseDefinitions() {
      // eslint-disable-next-line consistent-return
      return new Promise((resolve, reject) => {
        if (!this.templateFile) {
          return reject(new Error('No file provided'))
        }
        const reader = new FileReader()
        // eslint-disable-next-line consistent-return
        reader.onload = () => resolve(JSON.parse(reader.result))
        reader.onerror = () => reject(reader.error)
        reader.readAsText(this.templateFile)
      })
    },
  },
}
</script>
