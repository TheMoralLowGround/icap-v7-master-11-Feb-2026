<template>
  <b-modal
    :visible="visible"
    title="Delete Dictionary"
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
        Are you sure you want to delete the dictionary <strong>{{ dictionaryName }}</strong>?
      </p>
      <p class="text-danger mb-0">
        <small>This action cannot be undone. All data in this dictionary will be permanently deleted.</small>
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
        <span>Deleting dictionary...</span>
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
import axios from 'axios'

export default {
  name: 'DeleteDictionaryDialog',
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
    dictionaryName: {
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
      if (!this.dictionaryName) return

      this.loading = true
      this.errorMessage = ''

      try {
        const payload = {
          dictionary_name: this.dictionaryName,
          process_name: this.currentProcessName,
        }

        // API call to delete dictionary
        await axios.post('/dashboard/delete_lookup_table/', payload)

        // Emit success event
        this.$emit('dictionary-deleted', {
          name: this.dictionaryName,
        })

        // Show success toast
        this.$toast({
          component: () => import('@core/components/toastification/ToastificationContent.vue'),
          props: {
            title: 'Dictionary deleted successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        // Close modal
        this.handleClose()
      } catch (error) {
        this.errorMessage = error.response?.data?.message
          || error.response?.data?.error
          || 'Failed to delete dictionary. Please try again.'
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
