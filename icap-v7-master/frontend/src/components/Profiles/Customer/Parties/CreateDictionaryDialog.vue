<template>
  <b-modal
    :visible="visible"
    title="Create New Dictionary"
    no-close-on-backdrop
    size="md"
    centered
    ok-title="Create"
    cancel-title="Cancel"
    :ok-disabled="!isFormValid"
    @ok="handleCreate"
    @hidden="handleClose"
    @cancel="handleClose"
  >
    <b-form @submit.prevent="handleCreate">
      <!-- Entity Selection -->
      <b-form-group
        label="Select Entity"
        label-for="columns-select"
      >
        <v-select
          v-if="lists.length > 0"
          id="columns-select"
          v-model="formData.selectedDictionary"
          :options="lists"
          :reduce="option => option.keyValue"
          label="label"
          placeholder="Select entity to create dictionary..."
          :clearable="false"
        />
        <b-alert
          v-else
          variant="info"
          show
        >
          All available lists already have dictionaries created. No new dictionaries can be created at this time.
        </b-alert>
        <small
          v-if="formData.selectedDictionary"
          class="text-muted mt-1 d-block"
        >
          Selected: {{ formData.selectedDictionary }}
        </small>
      </b-form-group>

      <!-- Error Alert -->
      <b-alert
        v-if="errorMessage"
        variant="danger"
        show
        @dismissed="errorMessage = ''"
      >
        {{ errorMessage }}
      </b-alert>

      <!-- Loading State -->
      <div
        v-if="loading"
        class="text-center my-2"
      >
        <b-spinner class="mr-2" />
        <span>Creating dictionary...</span>
      </div>
    </b-form>
  </b-modal>
</template>

<script>
import {
  BModal,
  BForm,
  BFormGroup,
  // BFormInput,
  BAlert,
  BSpinner,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import axios from 'axios'

export default {
  name: 'CreateDictionaryDialog',
  components: {
    BModal,
    BForm,
    BFormGroup,
    // BFormInput,
    BAlert,
    BSpinner,
    vSelect,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    existingDictionaries: {
      type: Array,
      default: () => [],
    },
    lists: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      formData: {
        selectedDictionary: null,
      },
      loading: false,
      errorMessage: '',
    }
  },
  computed: {
    isFormValid() {
      return (
        this.formData.selectedDictionary
        && this.formData.selectedDictionary.trim() !== ''
        && !this.loading
      )
    },
    currentProcessName() {
      return this.$store.getters['profile/currentProcessName']
    },
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.resetForm()
      }
    },
  },
  methods: {
    async handleCreate() {
      if (!this.isFormValid) return

      this.loading = true
      this.errorMessage = ''

      try {
        // Get the selected entity to extract its fields
        const selectedEntity = this.lists.find(
          en => en.keyValue === this.formData.selectedDictionary,
        )

        // Build columns array with ID at start, entity fields, and PROCESS_NAME at end
        const columns = ['ID']

        // Add the entity's fields if available
        if (selectedEntity && selectedEntity.keyValue) {
          // Add all the field names from the selected entity
          // The keyValue itself becomes part of the columns
          const entityColumns = selectedEntity.children || selectedEntity.fields || []
          entityColumns.forEach(field => {
            if (field.keyValue || field.name) {
              columns.push(field.keyValue || field.name)
            }
          })
        }

        // Add PROCESS_NAME at the end
        columns.push('PROCESS_NAME')

        const payload = {
          dictionary_name: this.formData.selectedDictionary,
          columns,
        }

        // API call to create dictionary
        await axios.post('/dashboard/create_lookup_table/', payload)

        // Emit success event
        this.$emit('dictionary-created', {
          name: this.formData.selectedDictionary,
          columns,
        })

        // Show success toast
        this.$toast({
          component: () => import('@core/components/toastification/ToastificationContent.vue'),
          props: {
            title: 'Dictionary created successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        // Close modal
        this.handleClose()
      } catch (error) {
        this.errorMessage = error.response?.data?.message
          || error.response?.data?.error
          || 'Failed to create dictionary. Please try again.'
      } finally {
        this.loading = false
      }
    },

    handleClose() {
      this.$emit('close')
    },

    resetForm() {
      this.formData = {
        selectedDictionary: null,
      }
      this.errorMessage = ''
      this.loading = false
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';
</style>
