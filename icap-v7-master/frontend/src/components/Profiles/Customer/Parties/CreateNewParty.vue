<template>
  <b-modal
    :visible="visible"
    title="Create New Party"
    no-close-on-backdrop
    size="md"
    centered
    ok-title="Create"
    cancel-title="Cancel"
    :ok-disabled="!isFormValid"
    @ok="handleOk"
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
          v-model="formData.selectedParty"
          :options="lists"
          :reduce="option => option.keyValue"
          label="label"
          placeholder="Select entity to create party..."
          :clearable="false"
        />
        <b-alert
          v-else
          variant="info"
          show
          class="p-1"
        >
          No parties available.
        </b-alert>
      </b-form-group>

      <!-- Force Checkbox -->
      <!-- <b-form-group
        v-if="resolutionMessage"
        class="mb-3"
      >
        <b-form-checkbox
          v-model="formData.force"
          :value="true"
          :unchecked-value="false"
        >
          Force create without all defaults
        </b-form-checkbox>
      </b-form-group> -->

      <!-- Resolution Alert -->
      <!-- <b-alert
        v-if="resolutionMessage"
        variant="warning"
        show
        class="mb-2 p-1"
      >
        {{ resolutionMessage }}
      </b-alert> -->

      <!-- Error Alert -->
      <b-alert
        v-if="errorMessage"
        variant="danger"
        show
        class="p-1"
        @dismissed="errorMessage = ''"
      >
        <span>{{ errorMessage }}</span>
      </b-alert>

      <!-- Loading State -->
      <div
        v-if="loading"
        class="text-center my-2"
      >
        <b-spinner class="mr-2" />
        <span>Creating party...</span>
      </div>
    </b-form>
  </b-modal>
</template>

<script>
import {
  BModal,
  BForm,
  BFormGroup,
  // BFormCheckbox,
  // BFormInput,
  BAlert,
  BSpinner,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

export default {
  name: 'CreateNewParty',
  components: {
    BModal,
    BForm,
    BFormGroup,
    // BFormCheckbox,
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
    existingParties: {
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
        selectedParty: null,
        // force: false,
      },
      loading: false,
      errorMessage: '',
      resolutionMessage: '',
    }
  },
  computed: {
    isFormValid() {
      return (
        this.formData.selectedParty
        && this.formData.selectedParty.trim() !== ''
        && !this.loading
      )
    },
    currentProcessName() {
      return this.$store.getters['profile/currentProcessName']
    },
    // Get all available columns for the selected party
    availableColumnsForParty() {
      if (!this.formData.selectedParty) return []

      const partyNameLower = this.formData.selectedParty.toLowerCase()
      const allKeys = this.$store.state.profile.keys || []

      // Filter keys that match the party name and are addressBlockPartial type
      const matchingKeys = allKeys.filter(item => {
        if (!item || !item.keyValue) return false

        const keyValueLower = item.keyValue.toLowerCase()
        return (
          item.type === 'addressBlockPartial'
          && keyValueLower.startsWith(partyNameLower)
        )
      })

      // Transform to the required column schema format
      return matchingKeys.map(item => ({
        key: item.keyValue,
        label: item.keyValue,
        sortable: true,
        ismandatory: false,
        isFixed: false,
        customSearch: true,
      }))
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
    handleOk(bvModalEvent) {
      // Prevent modal from closing automatically
      bvModalEvent.preventDefault()
      // Call the create handler
      this.handleCreate()
    },

    async handleCreate() {
      if (!this.isFormValid) return

      this.loading = true
      this.errorMessage = ''

      try {
        // Create party table with available columns based on addressBlockPartial keys
        // Send table name in UPPERCASE
        const payload = {
          name: this.formData.selectedParty.toUpperCase(),
          description: null,
          columns: this.availableColumnsForParty, // Send all available columns for the party
        }

        // Add force flag if it's enabled
        // if (this.formData.force) {
        //   payload.force = true
        // }

        await this.$store.dispatch('profile/createPartyTable', payload)

        // Emit success event
        this.$emit('party-created', {
          name: this.formData.selectedParty,
        })

        // Show success toast
        this.$bvToast.toast('Party created successfully', {
          title: 'Success',
          variant: 'success',
          solid: true,
        })

        // Close modal ONLY on success
        this.handleClose()
      } catch (error) {
        // Check if error response contains a resolution field
        const errorDetail = error.response?.data?.detail

        const errorMsg = errorDetail?.message
          || errorDetail
          || error.response?.data?.error
          || error.message
          || 'Failed to create party. Please try again.'

        // If errorDetail is an object and has a resolution field
        // if (errorDetail && typeof errorDetail === 'object' && errorDetail.resolution) {
        //   // Store the resolution message to show in the warning alert
        //   this.resolutionMessage = errorDetail.resolution

        //   // Use the error message
        //   errorMsg = errorDetail.message || 'An error occurred while creating the party.'
        // } else {
        //   // Clear resolution message if there's no resolution in the error
        //   this.resolutionMessage = ''
        // }

        this.errorMessage = errorMsg

        // Show error toast notification
        this.$bvToast.toast(errorMsg, {
          title: 'Error',
          variant: 'danger',
          solid: true,
          autoHideDelay: 5000,
        })

        // DO NOT close modal on error - keep it open
      } finally {
        this.loading = false
      }
    },

    handleClose() {
      this.$emit('close')
    },

    resetForm() {
      this.formData = {
        selectedParty: null,
        // force: false,
      }
      this.errorMessage = ''
      this.resolutionMessage = ''
      this.loading = false
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';
</style>
