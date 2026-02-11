<template>
  <div>
    <!-- Modal for adding mapped key -->
    <b-modal
      v-model="dialog"
      :title="title"
      ok-title="Save"
      cancel-variant="outline-secondary"
      :ok-disabled="!isFormValid || loading"
      no-close-on-backdrop
      no-close-on-esc
      centered
      @ok.prevent="addMappedKeyToProject"
      @hidden="handleModalCancel"
    >
      <div class="d-flex flex-column mb-1">
        <b-form-group
          label="Mapped Key Label"
          label-for="mapped-key-input"
        >
          <b-form-input
            id="mapped-key-input"
            v-model="form.mappedKey"
            placeholder="Enter Label"
            readonly
            :state="form.mappedKey ? true : null"
          />
          <b-form-invalid-feedback :state="form.mappedKey ? true : null">
            Mapped Key Label is required
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          label="Key Value"
          label-for="key-value-select"
          class="mt-1"
        >
          <v-select
            id="key-value-select"
            v-model="form.keyLabel"
            :options="projectKeyOptions"
            placeholder="Select Key Label"
            :state="form.keyLabel ? true : null"
            :disabled="loading"
            @input="onKeyValueInput"
          />
          <b-form-invalid-feedback :state="form.keyLabel ? true : null">
            Key Value is required
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          v-if="keyQualifierNames.includes(form.keyLabel)"
          label="Key Qualifier Value"
          label-for="key-qualifier-value-select"
          class="mt-1"
        >
          <v-select
            id="key-qualifier-value-select"
            v-model="form.keyQualifierValue"
            :options="keyQualifierOptions"
            :reduce="option => option.value"
            placeholder="Select Key Qualifier Value"
            :state="form.keyQualifierValue ? true : null"
            :disabled="loading"
            @input="clearErrorOnInput"
          />
          <b-form-invalid-feedback :state="form.keyQualifierValue ? true : null">
            Key Qualifier Value is required
          </b-form-invalid-feedback>
        </b-form-group>
      </div>
      <div
        v-if="formError"
        class="text-danger mb-2"
      >
        {{ formError }}
      </div>
      <template #modal-ok>
        <b-spinner
          v-if="loading"
          small
          class="mr-2"
        />
        <span>{{ loading ? 'Saving...' : 'Save' }}</span>
      </template>
    </b-modal>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'
import vSelect from 'vue-select'
import {
  BModal, BFormGroup, BFormInvalidFeedback, BFormInput, BSpinner,
} from 'bootstrap-vue'
// import normalizeCase from '../utils/normalizeCase'

export default {
  name: 'AddKeysToProfile',
  components: {
    BModal,
    BFormGroup,
    BFormInvalidFeedback,
    BFormInput,
    vSelect,
    BSpinner,
  },
  props: {
    batchId: {
      type: String,
      default: '',
    },
    documentId: {
      type: String,
      default: '',
    },
    label: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: 'Add Mapped Key To Project',
    },
    type: {
      type: String,
      default: 'key',
    },
    addType: {
      type: String,
      default: 'key',
    },
    isTableKey: {
      type: Boolean,
      default: false,
    },
    reverse: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialog: false,
      loading: false,
      form: {
        mappedKey: this.label,
        keyLabel: '',
        keyQualifierValue: '',
        batchId: '',
        documentId: '',
      },
      formError: '',
    }
  },
  computed: {
    ...mapState({
      projectAllKeys: state => state.batch.projectAllKeys,
    }),
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
    projectKeyOptions() {
      if (!Array.isArray(this.projectAllKeys)) return []

      let options
      if (this.mainMode === 'keySettings' || this.reverse) {
        options = this.projectAllKeys.filter(item => item.type !== 'table').map(item => item.label)
      } else if (this.mainMode === 'tableSettings') {
        options = this.projectAllKeys.filter(item => item.type === 'table' || item.type === 'lookupCode').map(item => item.label)
      } else {
        options = this.projectAllKeys.map(item => item.label)
      }

      return options.sort((a, b) => a.localeCompare(b))
    },
    isFormValid() {
      if (this.keyQualifierNames.includes(this.form.keyLabel)) {
        return this.form.mappedKey && this.form.keyLabel && this.form.keyQualifierValue
      }

      return this.form.mappedKey && this.form.keyLabel
    },
    KeyItems() {
      return this.$store.getters['project/keyItems'] || []
    },
    profileDetails() {
      return this.$store.getters['batch/profileDetails'] || {}
    },
    items() {
      return this.$store.getters['project/mappedKeys']
    },
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    project() {
      return this.$store.getters['project/project']
    },
  },
  watch: {
    label: {
      immediate: true,
      handler(newVal) {
        this.form.mappedKey = newVal
      },
    },
  },
  methods: {
    onKeyValueInput() {
      this.form.keyQualifierValue = ''
      this.clearErrorOnInput()
    },
    clearErrorOnInput() {
      if (this.formError) this.formError = ''
    },
    handleModalCancel() {
      // Reset form when modal is canceled
      this.form.keyLabel = ''
      this.form.keyQualifierValue = ''
      this.formError = ''
    },
    async addToProfile() {
      const newKey = {
        profile_id: this.profileDetails?.id,
        key_label: this.label,
        key_type: this.addType,
        is_table_key: this.isTableKey,
        document_id: this.documentId,
        batch_id: this.batchId,
      }

      // Check if profile_id is missing
      if (!newKey.profile_id) {
        this.$bvToast.toast('Process not found.', {
          title: 'Error',
          variant: 'danger',
          solid: true,
        })
        return
      }

      try {
        if (this.label) {
          const response = await axios.post('/add_key_to_profile/', { ...newKey })

          if (response.status === 200 || response.status === 201) {
            const message = response?.data?.detail.replace('profile', 'process') ?? 'Key Added to Process'
            this.$bvToast.toast(message, {
              title: 'Success',
              variant: 'success',
              solid: true,
            })
          }
        }
      } catch (error) {
        if (error.response?.status === 406) {
          this.dialog = true
          this.formError = error?.response?.data?.detail || 'Key already exist'
        } else {
          let message = error?.response?.data?.detail
          if (message.includes('profile')) {
            message = message.replace('profile', 'process')
          }

          if (message.includes('already exist')) {
            this.$bvToast.toast(message, {
              title: 'Info',
              variant: 'info',
              solid: true,
            })
          }
          this.formError = error?.response?.data?.detail || 'Failed to update process'
        }
      }
    },
    async addMappedKeyToProject() {
      if (!this.isFormValid) {
        this.formError = 'Both Mapped Key Label and Key Value are required.'
        return
      }

      this.loading = true
      this.formError = ''

      try {
        const item = this.form

        // Dispatch actions in parallel for better performance
        await Promise.all([
          axios.post('/add_mapped_key_to_project/', {
            profile_id: this.profileDetails?.id,
            // key_label: normalizeCase(item.keyLabel),
            // mapped_key: normalizeCase(item.mappedKey),
            key_label: item.keyLabel,
            mapped_key: item.mappedKey,
            key_qualifier_value: item.keyQualifierValue,
            key_type: this.addType,
            is_table_key: this.isTableKey,
            document_id: this.documentId,
            batch_id: this.batchId,
          }),

          this.$store.dispatch('project/fetchProjectDetail', this.project.id),
        ])

        this.$bvToast.toast('Mapped Key Added to Project and key added to Process', {
          title: 'Success',
          variant: 'success',
          solid: true,
        })

        // Close dialog first, form will be reset in handleModalCancel
        this.dialog = false
      } catch (error) {
        this.formError = error?.response?.data?.detail || 'Failed to update process'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';

.compact-dropdown {
  ::v-deep .dropdown-toggle {
    padding: 0 !important;
    margin: 0 !important;
    min-width: auto !important;
    line-height: 1 !important;
  }
}

.text-danger {
  min-height: 20px;
}
</style>
