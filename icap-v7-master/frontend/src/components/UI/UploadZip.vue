<template>
  <validation-observer
    ref="uploadZipForm"
    mode="eager"
  >
    <b-modal
      v-model="showModal"
      centered
      :title="title"
      @ok="onSubmit"
      @hidden="$emit('modal-closed')"
    >
      <b-card-text>
        <validation-provider
          #default="{ errors }"
          name="File"
          vid="file"
          rules="required"
        >
          <b-form-group
            :label="label"
          >
            <b-form-file
              v-model="zipFile"
              accept=".zip"
              :state="errors.length > 0 ? false:null"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </b-form-group>
        </validation-provider>

        <b-form-group>
          <b-form-checkbox
            v-model="replaceIfExists"
          >
            Replace if already exists
          </b-form-checkbox>
        </b-form-group>
      </b-card-text>
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
  </validation-observer>
</template>

<script>
import {
  BButton, BModal, BSpinner, BAlert, BCardText, BFormGroup, BFormFile, BFormCheckbox,
} from 'bootstrap-vue'
import axios from 'axios'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import { ValidationObserver, ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    BButton,
    BModal,
    BSpinner,
    BAlert,
    BCardText,
    BFormGroup,
    BFormFile,
    BFormCheckbox,
    ValidationObserver,
    ValidationProvider,
  },
  props: {
    title: {
      type: [String],
      required: false,
      default() {
        return 'Upload Zip'
      },
    },
    label: {
      type: [String],
      required: false,
      default() {
        return 'File:'
      },
    },
    apiEndpoint: {
      type: [String],
      required: false,
      default() {
        return '/pipeline/upload_batch_zip/'
      },
    },
    subPath: {
      type: [String],
      required: false,
      default() {
        return null
      },
    },
    replace: {
      type: [Boolean],
      required: false,
      default() {
        return false
      },
    },
  },
  data() {
    return {
      showModal: true,
      submitting: false,
      zipFile: null,
      fileLoadError: null,
      replaceIfExists: false,
    }
  },
  created() {
    this.replaceIfExists = this.replace
  },
  methods: {
    onSubmit(event) {
      event.preventDefault()

      this.$refs.uploadZipForm.validate().then(success => {
        if (!success) {
          return
        }

        this.submitting = true

        const formData = new FormData()
        formData.append('zip_file', this.zipFile)
        formData.append('sub_path', this.subPath || '')
        formData.append('replace_if_exists', this.replaceIfExists)

        axios.post(this.apiEndpoint, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
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
          this.showModal = false
          this.$emit('uploaded')
        }).catch(error => {
          this.fileLoadError = error?.response?.data?.detail || 'Error uploading batch zip'
          this.submitting = false
        })
      })
    },
  },
}
</script>
