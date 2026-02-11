<template>
  <div>
    <!-- Display a status chip if the status exists -->
    <chip
      v-if="status"
      :variant="chipVariant"
    >
      {{ formattedStatus }} <!-- Displays the status text inside the chip -->
    </chip>

    <!-- Display a spinner when the data is being refreshed -->
    <b-spinner
      v-if="refreshing"
      class="mx-50"
      small
    />
  </div>
</template>

<script>
import { BSpinner } from 'bootstrap-vue'
import Chip from '@/components/UI/Chip.vue'

export default {
  components: {
    BSpinner,
    Chip,
  },
  computed: {
    // Computed property to check if data is being refreshed
    refreshing() {
      return this.$store.getters['batch/refreshing'] // Retrieves the refreshing state from the Vuex store
    },
    // Computed property to get the batch status from the Vuex store
    batchStatus() {
      return this.$store.getters['batch/status']
    },
    // Computed property to extract the status value from batchStatus
    status() {
      return this.batchStatus?.status // Returns the status or undefined if batchStatus is null/undefined
    },
    // Computed property to determine the chip's variant based on the status
    chipVariant() {
      if (this.status === 'completed') {
        return 'success' // Green chip for completed status
      }
      if (this.status === 'failed') {
        return 'danger' // Red chip for failed status
      }
      if (['warning', 'awaiting_agent'].includes(this.status)) {
        return 'warning' // Red chip for failed status
      }
      return 'primary' // Default blue chip for other statuses
    },
    formattedStatus() {
      return this.status
        ?.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ') || ''
    },
  },
}
</script>
