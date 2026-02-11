<template>
  <b-modal
    :visible="modelValue"
    :title="isEdit ? 'Edit Key' : 'Add Key'"
    ok-title="Save"
    cancel-title="Cancel"
    centered
    no-close-on-backdrop
    @hide="close"
    @ok="onSubmitForm"
  >
    <b-form @submit.prevent="onSubmitForm">
      <b-row>
        <b-col md="12">
          <b-form-group label="Key Label">
            <b-form-input
              v-model="form.label"
              required
              placeholder="Enter Label"
              :state="form.label && form.label.trim() ? true : null"
            />
            <small
              v-if="(!form.label || !form.label.trim()) && showValidation"
              class="text-danger"
            >Key Label is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Key Value">
            <b-form-input
              v-model="form.value"
              required
              placeholder="Enter Value"
              :state="form.value && form.value.trim() ? true : null"
            />
            <small
              v-if="(!form.value || !form.value.trim()) && showValidation"
              class="text-danger"
            >Key Value is required</small>
          </b-form-group>
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
  },
  props: {
    modelValue: Boolean,
    isEdit: Boolean,
    optionLabel: {
      type: Object,
      default: () => ({}),
    },
    existingItems: {
      type: Array,
      default: () => [],
    },
    selectedItemIndex: {
      type: Number,
      default: -1,
    },
  },
  data() {
    return {
      form: {
        label: '',
        value: '',
      },
      errorMessage: null,
      submitting: false,
      showValidation: false,
    }
  },
  computed: {
    isFormValid() {
      const label = (this.form.label || '').trim()
      const value = (this.form.value || '').trim()
      return label && value
    },
  },
  watch: {
    optionLabel: {
      handler(newVal) {
        this.form = cloneDeep(newVal || {
          label: '',
          value: '',
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
      const trimmedLabel = (this.form.label || '').trim()
      const trimmedValue = (this.form.value || '').trim()

      // Check for duplicates using optimized reduce pattern
      const duplicateType = this.existingItems.reduce((dup, item, index) => {
        if (dup) return dup // Already found → skip rest (fast exit)
        if (this.isEdit && this.selectedItemIndex === index) return dup

        if ((item.label || '').toLowerCase().replace(/\s+/g, '') === trimmedLabel.toLowerCase().replace(/\s+/g, '')) return 'label'
        if ((item.value || '').toLowerCase().replace(/\s+/g, '') === trimmedValue.toLowerCase().replace(/\s+/g, '')) return 'value'

        return null
      }, null)

      if (duplicateType) {
        this.errorMessage = duplicateType === 'label'
          ? `Key Qualifier with label "${trimmedLabel}" already exists.`
          : `Key Qualifier with value "${trimmedValue}" already exists.`

        this.submitting = false
        return
      }

      // Return the form data to parent component with trimmed values
      const formData = {
        label: trimmedLabel,
        value: trimmedValue,
      }

      // Emit the data to parent
      this.$emit('save', formData)

      // Close modal and reset state
      this.submitting = false
      this.$emit('update:modelValue', false)
    },
    close() {
      this.$emit('update:modelValue', false)
    },
  },
}
</script>
