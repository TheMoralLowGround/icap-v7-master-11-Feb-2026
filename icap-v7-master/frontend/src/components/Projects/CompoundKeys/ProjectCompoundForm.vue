<template>
  <b-modal
    :visible="modelValue"
    :title="isEdit ? 'Edit Mode Type' : 'Add Mode Type'"
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
              v-model="form.keyLabel"
              required
              placeholder="Enter Label"
              :state="form.keyLabel && form.keyLabel.trim() ? true : null"
            />
            <small
              v-if="(!form.keyLabel || !form.keyLabel.trim()) && showValidation"
              class="text-danger"
            >Key Label is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Key Value">
            <b-form-input
              v-model="form.keyValue"
              required
              placeholder="Enter Value"
              :state="form.keyValue && form.keyValue.trim() ? true : null"
            />
            <small
              v-if="(!form.keyValue || !form.keyValue.trim()) && showValidation"
              class="text-danger"
            >Key Value is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Type">
            <v-select
              v-model="form.type"
              :options="['key', 'table', 'addressBlock', 'addressBlockPartial', 'lookupCode']"
              required
              placeholder="Select Type"
              :state="form.type ? true : null"
              clearable
            />
            <small
              v-if="!form.type && showValidation"
              class="text-danger"
            >Type is required</small>
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Mod Type">
            <v-select
              v-model="form.modType"
              :options="ModeTypeOptions"
              placeholder="Select Mod Type"
              clearable
            />
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Qualifier">
            <v-select
              v-model="form.qualifier"
              :options="qualifierOptions"
              placeholder="Select Qualifier"
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
import vSelect from 'vue-select'

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
    vSelect,
  },
  props: {
    modelValue: Boolean,
    isEdit: Boolean,
    compoundKeyItem: {
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
        type: '',
        modType: '',
        keyLabel: '',
        keyValue: '',
        qualifier: '',
        compoundKeys: '',
      },
      errorMessage: null,
      submitting: false,
      showValidation: false,
    }
  },
  computed: {
    Qualifiers() {
      return this.$store.getters['project/keyQualifiers'] || []
    },
    CompoundKeys() {
      return this.$store.getters['project/compoundKeys'] || []
    },

    ModeTypes() {
      return this.$store.getters['project/keyModeTypes'] || ['hazardousMaterial', 'Financial Value', 'modType']
    },
    qualifierOptions() {
      return this.Qualifiers.map ? this.Qualifiers.map(e => e.name) : []
    },
    compoundKeyOptions() {
      return this.CompoundKeys.map ? this.CompoundKeys.map(e => e.name) : []
    },
    ModeTypeOptions() {
      return this.ModeTypes.map ? this.ModeTypes.map(e => e.modType) : []
    },

    isFormValid() {
      const keyLabel = (this.form.keyLabel || '').trim()
      const keyValue = (this.form.keyValue || '').trim()
      return keyLabel && keyValue && this.form.type
    },
  },
  watch: {
    compoundKeyItem: {
      handler(newVal) {
        this.form = cloneDeep(newVal || {
          type: '',
          modType: '',
          keyLabel: '',
          keyValue: '',
          qualifier: '',
          compoundKeys: '',
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
      const trimmedKeyLabel = (this.form.keyLabel || '').trim()
      const trimmedKeyValue = (this.form.keyValue || '').trim()
      const trimmedQualifier = typeof this.form.qualifier === 'string' ? this.form.qualifier.trim() : this.form.qualifier
      const trimmedModType = typeof this.form.modType === 'string' ? this.form.modType.trim() : this.form.modType
      const currentType = this.form.type

      // Define type groups
      const tableGroup = ['table']
      // Non-table group: 'key', 'addressBlock', 'addressBlockPartial', 'lookupCode'

      // Helper function to check if types are in the same group
      const areTypesInSameGroup = (type1, type2) => {
        const isType1Table = tableGroup.includes(type1)
        const isType2Table = tableGroup.includes(type2)
        return isType1Table === isType2Table
      }

      // Check for duplicates using optimized reduce pattern
      const duplicateType = this.existingItems.reduce((dup, item, index) => {
        if (dup) return dup // Already found → skip rest (fast exit)
        if (this.isEdit && this.selectedItemIndex === index) return dup

        // Only check for duplicates if types are in the same group
        if (areTypesInSameGroup(item.type, currentType)) {
          if ((item.keyLabel || '').toLowerCase().replace(/\s+/g, '') === trimmedKeyLabel.toLowerCase().replace(/\s+/g, '')) return 'label'
          if ((item.keyValue || '').toLowerCase().replace(/\s+/g, '') === trimmedKeyValue.toLowerCase().replace(/\s+/g, '')) return 'value'
        }

        return null
      }, null)

      if (duplicateType) {
        this.errorMessage = duplicateType === 'label'
          ? `Compound Key with keyLabel "${trimmedKeyLabel}" already exists in the same type group.`
          : `Compound Key with keyValue "${trimmedKeyValue}" already exists in the same type group.`

        this.submitting = false
        return
      }

      // Return the form data to parent component with trimmed values
      const formData = {
        keyLabel: trimmedKeyLabel,
        keyValue: trimmedKeyValue,
        type: this.form.type || '',
        qualifier: trimmedQualifier || '',
        modType: trimmedModType || '',
      }

      // Emit the data to parent
      this.$emit('save', formData)

      // Close modal and reset state
      this.submitting = false
      this.$emit('update:modelValue', false)
      this.submitting = false
      this.resetForm()
    },
    close() {
      this.$emit('update:modelValue', false)
      this.resetForm()
    },
    resetForm() {
      this.form = {
        keyLabel: '',
        keyValue: '',
        type: '',
        qualifier: '',
        modType: '',
      }
      this.showValidation = false
      this.errorMessage = null
    },
  },
}
</script>
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
