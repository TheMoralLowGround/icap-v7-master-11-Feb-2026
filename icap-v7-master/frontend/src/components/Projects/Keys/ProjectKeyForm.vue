<template>
  <b-modal
    :visible="modelValue"
    :title="isEdit ? 'Edit Key' : 'Add Key'"
    ok-title="Save"
    cancel-title="Cancel"
    no-close-on-backdrop
    centered
    size="lg"
    @hide="close"
    @ok="onSubmitForm"
  >
    <b-form @submit.prevent="onSubmitForm">
      <b-row>
        <!-- <b-row> -->
        <b-col md="6">
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

        <b-col md="6">
          <b-form-group label="Key Value">
            <b-form-input
              v-model="form.keyValue"
              required
              placeholder="Enter Value (no spaces allowed)"
              :state="form.keyValue && form.keyValue.trim() ? true : null"
              @input="sanitizeKeyValue"
            />
            <small
              v-if="(!form.keyValue || !form.keyValue.trim()) && showValidation"
              class="text-danger"
            >Key Value is required</small>
          </b-form-group>
        </b-col>
        <!-- </b-row> -->

        <!-- <b-row> -->
        <b-col md="6">
          <b-form-group label="Type">
            <v-select
              v-model="form.type"
              :options="['key', 'table', 'addressBlock', 'addressBlockPartial', 'lookupCode', 'compound']"
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

        <b-col md="6">
          <b-form-group label="Qualifier">
            <v-select
              v-model="form.qualifier"
              :options="qualifierOptions"
              placeholder="Select Qualifier"
              clearable
            />
          </b-form-group>
        </b-col>
        <!-- </b-row> -->
        <b-col md="12">
          <b-form-group
            label="DocClass (Select one or multiple)"
            label-for="docclass-select"
          >
            <v-select
              v-model="docClassSelected"
              :options="docTypes"
              :reduce="option => option.docType"
              label="docType"
              placeholder="Select or type document class..."
              multiple
              :close-on-select="false"
            />
          </b-form-group>
        </b-col>
        <b-col md="12">
          <b-form-group label="Field Description">
            <b-form-textarea
              v-model="form.project_prompt.Field_Description"
              placeholder="The description of the field. If empty, field name will be used as default."
              rows="3"
            />
          </b-form-group>
        </b-col>
        <b-col md="12">
          <b-form-group label="Rules Description">
            <b-form-textarea
              v-model="form.project_prompt.Rules_Description"
              placeholder="Enter Rules Description"
              rows="3"
            />

          </b-form-group>
        </b-col>

        <b-col md="12">
          <div class="d-flex justify-content-between align-items-center">
            <label class="col-form-label mb-0">Required</label>
            <b-form-checkbox
              v-model="form.required"
              switch
              class="mb-0"
              @change="(newVal) => newVal ? form.addToProcess = newVal : null"
            />
          </div>
        </b-col>

        <b-col md="12">
          <div class="d-flex justify-content-between align-items-center">
            <label class="col-form-label mb-0">Add to Process</label>
            <b-form-checkbox
              v-model="form.addToProcess"
              switch
              :disabled="form.addToProcess && form.required"
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
  BFormTextarea,
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
    BFormCheckbox,
    BFormTextarea,
    vSelect,
  },
  props: {
    modelValue: Boolean,
    isEdit: Boolean,
    projectKeyItem: {
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
        type: '',
        modType: '',
        keyLabel: '',
        keyValue: '',
        qualifier: '',
        compoundKeys: '',
        project_prompt: {
          DocClass: '',
          Field_Description: '',
          Rules_Description: '',
        },
        required: false,
        addToProcess: false,
        itemIndex: null,
      },
      formData: {},
      errorMessage: null,
      submitting: false,
      showValidation: false,
    }
  },
  computed: {
    docTypes() {
      return this.$store.getters['project/docTypes'] || []
    },
    form: {
      get() {
        return this.formData
      },
      set(value) {
        this.formData = { ...this.formData, ...value }
      },
    },
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
    docClassSelected: {
      get() {
        const docClass = this.form.project_prompt?.DocClass || ''
        if (!docClass) return []
        if (typeof docClass === 'string') {
          // Split comma-separated string into array, trim whitespace
          return docClass.split(',').map(item => item.trim()).filter(item => item)
        }
        if (Array.isArray(docClass)) {
          return docClass
        }
        return []
      },
      set(value) {
        // Convert array to comma-separated string for backend storage
        if (!this.form.project_prompt) {
          this.form.project_prompt = {}
        }
        if (Array.isArray(value)) {
          // Trim each value to remove leading/trailing whitespace
          const trimmedValues = value.map(item => (typeof item === 'string' ? item.trim() : item)).filter(item => item)
          this.form.project_prompt.DocClass = trimmedValues.join(', ')
        } else {
          this.form.project_prompt.DocClass = (typeof value === 'string' ? value.trim() : value) || ''
        }
      },
    },
  },
  watch: {
    projectKeyItem: {
      handler(newVal) {
        if (newVal && Object.keys(newVal).length > 0) {
          // Only use values from project_prompt object
          const projectPrompt = newVal.project_prompt || {}

          this.form = {
            ...cloneDeep(newVal),
            project_prompt: {
              DocClass: projectPrompt.DocClass !== undefined ? projectPrompt.DocClass : '',
              Field_Description: projectPrompt.Field_Description !== undefined ? projectPrompt.Field_Description : '',
              Rules_Description: projectPrompt.Rules_Description !== undefined ? projectPrompt.Rules_Description : '',
            },
          }
        } else {
          this.form = {
            type: '',
            modType: '',
            keyLabel: '',
            keyValue: '',
            qualifier: '',
            compoundKeys: '',
            project_prompt: {
              DocClass: '',
              Field_Description: '',
              Rules_Description: '',
            },
            itemIndex: null,
          }
        }
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
    sanitizeKeyValue(value) {
      // Remove all spaces from the keyValue
      this.form.keyValue = value.replace(/\s+/g, '')
    },
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
      const trimmedKeyValue = (this.form.keyValue || '').trim()
      const trimmedKeyLabel = (this.form.keyLabel || '').trim()
      const trimmedQualifier = typeof this.form.qualifier === 'string' ? this.form.qualifier.trim() : this.form.qualifier
      const currentIndex = this.form.index
      const currentType = this.form.type

      // Define type groups
      const tableGroup = ['table']
      // Non-table group: 'key', 'addressBlock', 'addressBlockPartial', 'lookupCode', 'compound'

      // Helper function to check if types are in the same group
      const areTypesInSameGroup = (type1, type2) => {
        const isType1Table = tableGroup.includes(type1)
        const isType2Table = tableGroup.includes(type2)
        return isType1Table === isType2Table
      }

      const duplicateType = this.existingItems.reduce((dup, item, index) => {
        if (dup) return dup // Already found → skip rest (fast exit)
        if (this.isEdit && currentIndex === index) return dup

        // Only check for duplicates if types are in the same group (case-insensitive)
        if (areTypesInSameGroup(item.type, currentType)) {
          if ((item.keyValue || '').toLowerCase() === trimmedKeyValue.toLowerCase()) return 'value'
          if ((item.keyLabel || '').toLowerCase() === trimmedKeyLabel.toLowerCase()) return 'label'
        }

        return null
      }, null)
      if (duplicateType) {
        this.errorMessage = duplicateType === 'value'
          ? `Key with keyValue "${trimmedKeyValue}" already exists in the same type group.`
          : `Key with keyLabel "${trimmedKeyLabel}" already exists in the same type group.`

        this.submitting = false
        return
      }

      // Return the form data to parent component with trimmed values
      const formData = {
        ...this.form,
        type: this.form.type || '',
        keyLabel: trimmedKeyLabel,
        keyValue: trimmedKeyValue,
        modType: this.form.modType || '',
        qualifier: trimmedQualifier || '',
        compoundKeys: this.form.compoundKeys || '',
        project_prompt: {
          // Save actual values, even if they are empty strings
          DocClass: this.form.project_prompt?.DocClass ?? '',
          Field_Description: this.form.project_prompt?.Field_Description ?? '',
          Rules_Description: this.form.project_prompt?.Rules_Description ?? '',
        },
        required: this.form.required || false,
        addToProcess: this.form.addToProcess || false,
      }

      // Emit the data to parent
      this.$emit('save', formData)

      // Close modal and reset state
      this.submitting = false
      this.$emit('update:modelValue', false)
    },
    resetForm() {
      this.formData = cloneDeep(this.defaultFormData)
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
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
