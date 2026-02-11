<template>
  <div>
  <b-modal
    :visible="modelValue"
    :title="`${form.label} - ${processName}`"
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
        <b-col md="12">
          <b-form-group label="Key Label (Read-only)">
            <b-form-input
              :value="form.label"
              disabled
              placeholder="Key Label"
            />
          </b-form-group>
        </b-col>
        <b-col md="12">
          <b-form-group label="Key Value (Read-only)">
            <b-form-input
              :value="form.keyValue"
              disabled
              placeholder="Key Value"
            />
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group
            label="DocClass (Select one or multiple)"
            label-for="docclass-select"
          >
            <v-select
              v-model="docClassSelected"
              :options="availableDocOption"
              :reduce="option => option.doc_type"
              label="doc_type"
              placeholder="Select or type document class..."
              multiple
              :close-on-select="false"
            />
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group>
            <template #label>
              <div class="d-flex justify-content-between align-items-center">
                <span>Field Description</span>
                <feather-icon
                  v-if="projectKey"
                  v-b-tooltip.hover
                  icon="InfoIcon"
                  size="22"
                  class="cursor-pointer text-info"
                  title="View Project's Field/Rule Descriptions"
                  @click="showProjectDescriptions = true"
                />
              </div>
            </template>
            <b-form-textarea
              v-model="form.process_prompt.Field_Description"
              placeholder="The description of the field. If empty, field name will be used as default."
              rows="3"
            />
          </b-form-group>
        </b-col>

        <b-col md="12">
          <b-form-group label="Rules Description">
            <b-form-textarea
              v-model="form.process_prompt.Rules_Description"
              placeholder="Enter Rules Description"
              rows="3"
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

  <!-- Project Descriptions Dialog -->
  <b-modal
    v-model="showProjectDescriptions"
    :title="`Project Field & Rules Descriptions for ${form.keyValue}`"
    ok-only
    ok-title="Close"
    centered
    size="lg"
  >
    <div v-if="projectKey">
      <b-form-group label="Project Field Description">
        <b-form-textarea
          :value="projectFieldDescription"
          disabled
          rows="4"
          class="bg-light"
        />
      </b-form-group>
      <b-form-group label="Project Rules Description">
        <b-form-textarea
          :value="projectRulesDescription"
          disabled
          rows="4"
          class="bg-light"
        />
      </b-form-group>
    </div>
    <div v-else>
      <p class="text-muted">No project key information available.</p>
    </div>
  </b-modal>
  </div>
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
  BFormTextarea,
  VBTooltip,
} from 'bootstrap-vue'
// import { cloneDeep } from 'lodash'
import vSelect from 'vue-select'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BFormGroup,
    BForm,
    BAlert,
    BFormInput,
    BRow,
    BCol,
    BButton,
    BSpinner,
    BFormTextarea,
    vSelect,
  },
  props: {
    modelValue: Boolean,
    profileKeyItem: {
      type: Object,
      default: () => ({}),
    },
    projectKeyItems: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      defaultFormData: {
        label: '',
        keyValue: '',
        type: '',
        required: false,
        addToProcess: false,
        documents: [],
        process_prompt: {
          DocClass: '',
          Field_Description: '',
          Rules_Description: '',
        },
      },
      formData: {
        label: '',
        keyValue: '',
        type: '',
        required: false,
        addToProcess: false,
        documents: [],
        process_prompt: {
          DocClass: '',
          Field_Description: '',
          Rules_Description: '',
        },
      },
      errorMessage: null,
      submitting: false,
      showValidation: false,
      showProjectDescriptions: false,
    }
  },
  computed: {
    processName() {
      return this.$store.state.profile?.selecedProcessName || ''
    },
    projectKey() {
      // Find the matching project key by keyValue
      if (!this.form.keyValue || !this.projectKeyItems || !this.projectKeyItems.length) return null
      return this.projectKeyItems.find(pk => pk.keyValue === this.form.keyValue)
    },
    projectFieldDescription() {
      if (!this.projectKey) return 'No field description defined for this key'
      const prompt = this.projectKey.project_prompt
      if (prompt && prompt.Field_Description) return prompt.Field_Description
      if (this.projectKey.Field_Description) return this.projectKey.Field_Description
      return 'No field description defined for this key'
    },
    projectRulesDescription() {
      if (!this.projectKey) return 'No rules description defined for this key'
      const prompt = this.projectKey.project_prompt
      if (prompt && prompt.Rules_Description) return prompt.Rules_Description
      if (this.projectKey.Rules_Description) return this.projectKey.Rules_Description
      return 'No rules description defined for this key'
    },
    docTypes() {
      // Get profile documents instead of project documents
      return this.$store.state.profile.documents || []
    },
    transLatedDocs() {
      // Get profile documents instead of project documents
      return this.$store.state.profile.translated_documents || []
    },
    availableDocOption() {
      const documents = this.docTypes || []
      const translatedDocuments = this.transLatedDocs || []

      // Get list of doc_types that have been translated (original doc_types to exclude)
      const translatedDocTypes = translatedDocuments.map(td => td.doc_type)

      // Filter documents where category is 'Processing' and extract doc_type
      // Exclude doc_types that have been translated to another type
      return documents
        .filter(doc => doc.category === 'Processing' && doc.doc_type)
        .filter(doc => !translatedDocTypes.includes(doc.doc_type)) // Exclude translated doc_types
        .map(doc => ({ doc_type: doc.doc_type }))
        .filter((value, index, self) => self.findIndex(v => v.doc_type === value.doc_type) === index) // Remove duplicates
    },

    form: {
      get() {
        return this.formData
      },
      set(value) {
        this.formData = { ...this.formData, ...value }
      },
    },
    isFormValid() {
      return true
    },
    docClassSelected: {
      get() {
        const docClass = this.form.process_prompt?.DocClass || ''
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
        if (!this.form.process_prompt) {
          this.form.process_prompt = {}
        }
        if (Array.isArray(value)) {
          // Trim each value to remove leading/trailing whitespace
          const trimmedValues = value.map(item => (typeof item === 'string' ? item.trim() : item)).filter(item => item)
          this.form.process_prompt.DocClass = trimmedValues.join(', ')
        } else {
          this.form.process_prompt.DocClass = (typeof value === 'string' ? value.trim() : value) || ''
        }
      },
    },
  },
  watch: {
    profileKeyItem: {
      handler(newVal) {
        if (newVal && Object.keys(newVal).length > 0) {
          // ALWAYS migrate to process_prompt structure
          // Read from process_prompt if available, otherwise migrate from top-level fields
          const processPrompt = {
            DocClass: (newVal.process_prompt?.DocClass || newVal.DocClass || ''),
            Field_Description: (newVal.process_prompt?.Field_Description || newVal.Field_Description || ''),
            Rules_Description: (newVal.process_prompt?.Rules_Description || newVal.Rules_Description || ''),
          }

          this.formData = {
            label: newVal.label || '',
            keyValue: newVal.keyValue || '',
            type: newVal.type || '',
            required: newVal.required ?? false,
            addToProcess: newVal.addToProcess ?? false,
            documents: newVal.documents || [],
            process_prompt: processPrompt,
            precedence: newVal.precedence || [],
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

      // Send back ALL fields to preserve the complete object for the REST API
      const formData = {
        label: this.form.label,
        keyValue: this.form.keyValue,
        type: this.form.type,
        required: this.form.required,
        addToProcess: this.form.addToProcess,
        documents: this.form.documents,
        process_prompt: {
          DocClass: this.form.process_prompt?.DocClass || '',
          Field_Description: this.form.process_prompt?.Field_Description || '',
          Rules_Description: this.form.process_prompt?.Rules_Description || '',
        },
        precedence: this.form.precedence || [],
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
      this.showProjectDescriptions = false
    },
    close() {
      this.resetForm()
      this.$emit('update:modelValue', false)
      this.$emit('modal-closed')
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style scoped>
::v-deep .modal-header {
  align-items: flex-start;
}

::v-deep .modal-header .modal-title {
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
  flex: 1;
}

::v-deep .modal-header .close {
  flex-shrink: 0;
  margin-left: 0.5rem;
}
</style>
