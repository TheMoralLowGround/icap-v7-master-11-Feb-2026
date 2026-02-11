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
      </b-form-group>

      <!-- Description Field -->
      <b-form-group
        label="Description"
        label-for="description-input"
      >
        <b-form-textarea
          id="description-input"
          v-model="formData.description"
          placeholder="Enter description..."
          rows="3"
          max-rows="6"
        />
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
  BFormTextarea,
  BAlert,
  BSpinner,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
// import axios from 'axios'

export default {
  name: 'CreateNewDictionary',
  components: {
    BModal,
    BForm,
    BFormGroup,
    BFormTextarea,
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
        description: '',
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
        // Emit the selected dictionary name and description to parent
        this.$emit('create', {
          name: this.formData.selectedDictionary,
          description: this.formData.description || this.formData.selectedDictionary,
        })
        this.loading = false
      } catch (error) {
        this.errorMessage = error.message || 'Failed to create dictionary'
        this.loading = false
      }
    },

    handleClose() {
      this.$emit('close')
    },

    resetForm() {
      this.formData = {
        selectedDictionary: null,
        description: '',
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
