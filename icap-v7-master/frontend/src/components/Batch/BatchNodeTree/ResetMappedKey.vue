<template>
  <div>
    <!-- Modal for confirming reset mapped key -->
    <b-modal
      v-model="dialog"
      title="Reset Mapped Key"
      ok-title="Reset"
      ok-variant="danger"
      cancel-variant="outline-secondary"
      :ok-disabled="loading"
      no-close-on-backdrop
      no-close-on-esc
      centered
      @ok.prevent="resetMappedKey"
      @hidden="handleModalCancel"
    >
      <div class="mb-1">
        <p>Are you sure you want to reset the mapped key for <strong>{{ label }}</strong>?</p>
        <p class="text-muted">
          This action will remove the mapping from the process.
        </p>
      </div>
      <div
        v-if="formError"
        class="text-danger mb-2 mt-1 p-1"
      >
        {{ formError }}
      </div>
      <template #modal-ok>
        <b-spinner
          v-if="loading"
          small
          class="mr-2"
        />
        <span>{{ loading ? 'Resetting...' : 'Reset' }}</span>
      </template>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios'
import {
  BModal, BSpinner,
} from 'bootstrap-vue'
// import normalizeCase from '../utils/normalizeCase'

export default {
  name: 'ResetMappedKey',
  components: {
    BModal,
    BSpinner,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    documentId: {
      type: String,
      default: '',
    },
    batchId: {
      type: String,
      default: '',
    },
    originalKeyLabel: {
      type: String,
      required: false,
      default: null,
    },
    nestedLabel: {
      type: String,
      required: false,
      default: null,
    },
    isAddressBlockPartial: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      dialog: false,
      loading: false,
      formError: '',
    }
  },
  computed: {
    profileDetails() {
      return this.$store.getters['batch/profileDetails'] || {}
    },
    formattedMappedKey() {
      // Handle address block partial formatting
      if (this.isAddressBlockPartial && this.nestedLabel && this.originalKeyLabel) {
        const parts = this.nestedLabel.split('.')
        if (parts.length > 0) {
          return `${parts[0]} [address] ${this.originalKeyLabel}`
          // return normalizeCase(`${parts[0]} [address] ${this.originalKeyLabel}`)
        }
      }
      // Use originalKeyLabel if available, otherwise use label
      const keyLabelValue = this.originalKeyLabel
      return keyLabelValue
      // return normalizeCase(keyLabelValue)
    },
  },
  methods: {
    handleModalCancel() {
      // Reset error when modal is canceled
      this.formError = ''
    },
    openDialog() {
      this.dialog = true
    },
    async resetMappedKey() {
      this.loading = true
      this.formError = ''

      try {
        const payload = {
          profile_name: this.profileDetails?.name,
          remove_key_value: this.label,
          mapped_key: this.formattedMappedKey,
          batch_id: this.batchId,
          document_id: this.documentId,
        }

        // Check if profile_name is missing
        if (!payload.profile_name) {
          this.$bvToast.toast('Process not found.', {
            title: 'Error',
            variant: 'danger',
            solid: true,
          })
          this.loading = false
          return
        }

        const response = await axios.post('/delete_mapped_key/', payload)

        if (response.status === 200) {
          this.$bvToast.toast('Mapped key reset successfully', {
            title: 'Success',
            variant: 'success',
            solid: true,
          })

          // Emit event to parent component
          this.$emit('reset-success', this.label)

          // Close dialog
          this.dialog = false
        }
      } catch (error) {
        this.formError = error?.response?.data?.detail || 'Failed to reset mapped key'
        this.$bvToast.toast(this.formError, {
          title: 'Error',
          variant: 'danger',
          solid: true,
        })
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
