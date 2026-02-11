<template>
  <b-modal
    :visible="modelValue"
    :title="isEdit ? 'Edit Key' : 'Add Key'"
    no-close-on-backdrop
    @hide="close"
  >
    <b-form @submit.prevent="onSubmitForm">
      <b-row>
        <b-col md="12">
          <b-form-group label="Mapped Key Label">
            <b-form-input
              v-model="form.mappedKey"
              required
              placeholder="Mapped Key Label"
              :state="form.mappedKey && form.mappedKey.trim() ? true : null"
            />
            <small
              v-if="(!form.mappedKey || !form.mappedKey.trim()) && showValidation"
              class="text-danger"
            >Mapped Key Label is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Key Label">
            <v-select
              v-model="form.keyLabel"
              :options="keyItemsOptions"
              placeholder="Select Key Label"
              clearable
              @input="form.qualifierValue = ''"
            />
          </b-form-group>
        </b-col>

        <b-col
          v-if="keyQualifierNames.includes(form.keyLabel)"
          md="12"
        >
          <b-form-group label="Key Qualifier Value">
            <v-select
              v-model="form.qualifierValue"
              :options="keyQualifierOptions"
              :reduce="option => option.value"
              placeholder="Select Key Qualifier Value"
              clearable
            />
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
        :disabled="submitting"
        type="submit"
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
import vSelect from 'vue-select'

export default {
  components: {
    BFormGroup,
    BForm,
    BAlert,
    BFormInput,
    vSelect,
    BRow,
    BCol,
    BButton,
    BSpinner,
  },
  props: {
    modelValue: Boolean,
    isEdit: Boolean,
    mappedKeyItem: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      form: {
        mappedKey: '',
        keyLabel: '',
        qualifierValue: '',
      },
      errorMessage: null,
      submitting: false,
      showValidation: false,
    }
  },
  computed: {
    KeyItems() {
      return this.$store.getters['project/keyItems'] || []
    },
    keyItemsOptions() {
      return this.KeyItems.map ? this.KeyItems.map(e => e.keyLabel) : []
    },
    keyQualifiers() {
      return this.$store.getters['project/keyQualifiers']
    },
    keyQualifierNames() {
      return this.keyQualifiers.map(qualifier => qualifier.name)
    },
    keyQualifierOptions() {
      const keyQualifier = this.keyQualifiers.find(qualifier => qualifier.name === this.form.keyLabel) || {}
      return keyQualifier?.options || []
    },
    isFormValid() {
      const mappedKey = (this.form.mappedKey || '').trim()
      if (this.keyQualifierNames.includes(this.form.keyLabel)) {
        return mappedKey && this.form.keyLabel && this.form.qualifierValue
      }

      return mappedKey && this.form.keyLabel
    },
  },
  watch: {
    mappedKeyItem: {
      handler(newVal) {
        this.form = cloneDeep(newVal || {
          mappedKey: '',
          keyLabel: '',
          qualifierValue: '',
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

      // Return the form data to parent component
      const formData = cloneDeep(this.form)

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
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
