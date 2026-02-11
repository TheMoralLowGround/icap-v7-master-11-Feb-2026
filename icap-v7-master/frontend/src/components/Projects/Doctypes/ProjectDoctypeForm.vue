<template>
  <b-modal
    :visible="modelValue"
    :title="isEdit ? 'Edit Document' : 'Add Document'"
    no-close-on-backdrop
    centered
    @hide="close"
  >
    <b-form @submit.prevent="onSubmitForm">
      <b-row>
        <b-col md="12">
          <b-form-group label="Document Label">
            <b-form-input
              v-model="form.docType"
              required
              placeholder="Enter Label"
              :state="form.docType && form.docType.trim() ? true : null"
            />
            <small
              v-if="(!form.docType || !form.docType.trim()) && showValidation"
              class="text-danger"
            >Document Type is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Document Code">
            <b-form-input
              v-model="form.docCode"
              required
              placeholder="Enter Code"
              :state="form.docCode && form.docCode.trim() ? true : null"
            />
            <small
              v-if="(!form.docCode || !form.docCode.trim()) && showValidation"
              class="text-danger"
            >Document Code is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <div class="d-flex justify-content-between align-items-center">
            <label class="col-form-label mb-0">Add to Process</label>
            <b-form-checkbox
              v-model="form.addToProcess"
              switch
              class="mb-0"
            />
          </div>
        </b-col>
      </b-row>

      <b-alert
        variant="danger"
        :show="errorMessage !== null"
        class="mt-3"
      >
        <div class="alert-body">
          <p>{{ errorMessage }}</p>
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
        :disabled="submitting"
        @click="validateForm"
      >
        Save
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
  BAlert,
  BButton,
  BCol,
  BForm,
  BFormGroup,
  BFormInput,
  BRow,
  BSpinner,
  BFormCheckbox,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'

export default {
  components: {
    BFormGroup,
    BForm,
    BAlert,
    BFormInput,
    BRow,
    BCol,
    BButton,
    BSpinner,
    BFormCheckbox,
  },
  props: {
    modelValue: Boolean,
    isEdit: Boolean,
    doctypesItem: {
      type: Object,
      default: () => ({}),
    },
    existingItems: {
      type: Array,
      default: () => [],
    },
  },

  data() {
    return {
      defaultFormData: {
        docType: '',
        docCode: '',
        addToProcess: false,
      },
      formData: {},
      errorMessage: null,
      submitting: false,
      showValidation: false,
    }
  },
  computed: {
    form: {
      get() {
        return this.formData
      },
      set(value) {
        this.formData = { ...this.formData, ...value }
      },
    },
    isFormValid() {
      const docType = (this.form.docType || '').trim()
      const docCode = (this.form.docCode || '').trim()
      return docType && docCode
    },
  },
  watch: {
    doctypesItem: {
      handler(newVal) {
        this.form = cloneDeep(newVal || {
          docType: '',
          docCode: '',
        })
      },
      immediate: true,
      deep: true,
    },
    modelValue(newVal) {
      if (!newVal) {
        this.errorMessage = null
        this.showValidation = false
      }
    },
  },
  created() {
    this.resetForm()
  },
  methods: {
    validateForm() {
      this.showValidation = true

      if (this.isFormValid) {
        this.onSubmitForm()
      }
    },
    onSubmitForm(event) {
      if (event) {
        event.preventDefault()
      }

      this.submitting = true

      // Trim values before validation
      const trimmedDocType = (this.form.docType || '').trim()
      const trimmedDocCode = (this.form.docCode || '').trim()
      const currentIndex = this.form.index

      // Check for duplicate docType only (docCode can be duplicated)
      const isDuplicate = this.existingItems.some((item, index) => {
        if (this.isEdit && currentIndex === index) return false
        return (item.docType || '').toLowerCase().replace(/\s+/g, '') === trimmedDocType.toLowerCase().replace(/\s+/g, '')
      })

      if (isDuplicate) {
        this.errorMessage = `Document with name "${trimmedDocType}" already exists.`
        this.submitting = false
        return
      }

      // Return the form data to parent component with trimmed values
      const formData = {
        ...this.form,
        docType: trimmedDocType,
        docCode: trimmedDocCode,
        addToProcess: this.form.addToProcess || false,
      }
      // Emit the data to parent
      this.$emit('save', formData)

      // Close modal and reset state
      this.submitting = false
      this.$emit('update:modelValue', false)
    },
    resetForm() {
      this.formData = { ...this.defaultFormData }
      this.errorMessage = null
      this.submitting = false
      this.showValidation = false
    },
    close() {
      this.resetForm()
      this.$emit('update:modelValue', false)
    },
  },
}
</script>
