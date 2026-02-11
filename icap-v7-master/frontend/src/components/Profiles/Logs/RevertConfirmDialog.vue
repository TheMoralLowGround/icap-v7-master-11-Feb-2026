<template>
  <b-modal
    :visible="visible"
    :title="title"
    size="md"
    centered
    no-close-on-backdrop
    :ok-title="okTitle"
    :cancel-title="cancelTitle"
    :ok-variant="okVariant"
    cancel-variant="outline-primary"
    button-size="sm"
    :ok-disabled="!hasValidSelection"
    @ok="handleConfirm"
    @cancel="handleCancel"
    @hidden="handleCancel"
  >
    <div class="mt-3">
      <p class="font-weight-bold mb-2">
        Are you sure to revert <span class="text-primary">{{ changeType }}</span> change ?
      </p>
      <!-- <div>
        <b-form-radio
          v-model="selectedVersion"
          name="version-radios"
          value="old"
          class="mb-1"
        >
          Old version (before changes)
        </b-form-radio>
        <b-form-radio
          v-model="selectedVersion"
          name="version-radios"
          value="new"
        >
          New version (after changes)
        </b-form-radio>
      </div> -->
      <b-alert
        variant="danger"
        :show="!loading && loadingError ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ loadingError }}
          </p>
        </div>
      </b-alert>
    </div>
  </b-modal>
</template>

<script>
import {
  BModal,
  BAlert,
  // BFormRadio,
} from 'bootstrap-vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BAlert,
    // BFormRadio,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: 'Confirm Action',
    },
    id: {
      type: [Number, String],
      default: null,
    },
    okTitle: {
      type: String,
      default: 'Revert',
    },
    cancelTitle: {
      type: String,
      default: 'Cancel',
    },
    okVariant: {
      type: String,
      default: 'primary',
    },
    icon: {
      type: String,
      default: '',
    },
    iconClass: {
      type: String,
      default: 'text-warning',
    },
    changeType: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: 'confirm',
    },
  },
  data() {
    return {
      selectedVersion: 'old',
      loading: false,
      loadingError: null,
    }
  },
  computed: {
    hasValidSelection() {
      return !!this.selectedVersion
    },
  },
  methods: {
    async handleConfirm(bvModalEvt) {
      // Prevent modal from closing
      bvModalEvt.preventDefault()

      if (!this.hasValidSelection) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Warning',
            text: 'Please select a version to revert',
            icon: 'AlertTriangleIcon',
            variant: 'warning',
          },
        })
        return
      }

      this.loading = true
      try {
        const response = await axios.post(`/changelogs/${this.id}/revert/`)
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Success',
            text: `Successfully reverted to ${this.selectedVersion} version`,
            icon: 'CheckCircleIcon',
            variant: 'success',
          },
        })

        this.$emit('confirm', {
          version: this.selectedVersion,
          response: response.data,
        })

        // Close the modal
        this.$nextTick(() => {
          this.$emit('close')
        })
      } catch (error) {
        this.loadingError = error.response?.data?.message || 'Error reverting version'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error',
            text: this.loadingError,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      } finally {
        this.loading = false
      }
    },
    handleCancel() {
      this.selectedVersion = 'old'
      this.loading = false
      this.loadingError = null
      this.$emit('cancel')
      this.$emit('close')
    },
  },
}
</script>
