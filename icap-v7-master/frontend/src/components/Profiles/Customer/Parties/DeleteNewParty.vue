<template>
  <b-modal
    :visible="visible"
    title="Delete Party"
    centered
    size="md"
    ok-title="Delete"
    ok-variant="danger"
    cancel-title="Cancel"
    :ok-disabled="loading"
    @ok="handleDelete"
    @hidden="handleClose"
    @cancel="handleClose"
  >
    <div>
      <p class="mb-3">
        Are you sure you want to delete the party <strong>{{ partyName }}</strong>?
      </p>
      <p class="text-danger mb-0">
        <small>This action cannot be undone. All data in this party will be permanently deleted.</small>
      </p>

      <!-- Error Alert -->
      <b-alert
        v-if="errorMessage"
        variant="danger"
        show
        class="mt-3"
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
        <span>Deleting party...</span>
      </div>
    </div>
  </b-modal>
</template>

<script>
import {
  BModal,
  BAlert,
  BSpinner,
} from 'bootstrap-vue'

export default {
  name: 'DeleteNewParty',
  components: {
    BModal,
    BAlert,
    BSpinner,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    partyName: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      loading: false,
      errorMessage: '',
    }
  },
  computed: {
    currentProcessName() {
      return this.$store.getters['profile/currentProcessName']
    },
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.errorMessage = ''
      }
    },
  },
  methods: {
    async handleDelete() {
      if (!this.partyName) return

      this.loading = true
      this.errorMessage = ''

      try {
        // Call store action to delete party table
        await this.$store.dispatch('profile/deletePartyTable', {
          tableName: this.partyName,
        })

        // Emit success event
        this.$emit('party-deleted', {
          name: this.partyName,
        })

        // Show success toast
        this.$bvToast.toast('Party deleted successfully', {
          title: 'Success',
          variant: 'success',
          solid: true,
        })

        // Close modal
        this.handleClose()
      } catch (error) {
        this.errorMessage = error.response?.data?.message
          || error.response?.data?.error
          || error.message
          || 'Failed to delete party. Please try again.'
      } finally {
        this.loading = false
      }
    },

    handleClose() {
      this.$emit('close')
    },
  },
}
</script>

<style lang="scss" scoped>
strong {
  color: inherit;
}
</style>
