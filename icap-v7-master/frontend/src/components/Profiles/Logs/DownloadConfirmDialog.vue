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
    :ok-disabled="loading"
    @ok="handleConfirm"
    @cancel="handleCancel"
    @hidden="handleCancel"
  >
    <div class="mt-3">
      <p class="font-weight-bold mb-2">
        <!-- <feather-icon
          v-if="icon"
          :icon="icon"
          :class="iconClass"
          class="mr-1"
        /> -->
        Are you sure you want to download <span class="text-primary">{{ changeType }}</span> changes ?
      </p>
      <b-spinner
        v-if="loading"
        small
        label="Loading"
        class="my-2"
      />
      <b-alert
        variant="danger"
        :show="loadingError ? true : false"
      >
        <div class="alert-body">
          <p>{{ loadingError }}</p>
        </div>
      </b-alert>
    </div>
  </b-modal>
</template>

<script>
import { BModal, BAlert, BSpinner } from 'bootstrap-vue'
// import FeatherIcon from '@core/components/feather-icon/FeatherIcon.vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BAlert,
    BSpinner,
    // FeatherIcon,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: 'Download Version',
    },
    id: {
      type: [Number, String],
      default: null,
    },
    okTitle: {
      type: String,
      default: 'Download',
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
      default: 'download',
    },
  },
  data() {
    return {
      loading: false,
      loadingError: null,
    }
  },
  methods: {
    async handleConfirm(bvModalEvt) {
      bvModalEvt.preventDefault()

      // if (!this.id) {
      //   this.loadingError = 'Invalid changelog ID'
      //   this.$toast({
      //     component: ToastificationContent,
      //     props: {
      //       title: 'Error',
      //       text: this.loadingError,
      //       icon: 'AlertTriangleIcon',
      //       variant: 'danger',
      //     },
      //   })
      //   return
      // }

      this.loading = true
      try {
        const response = await axios.post(`/changelogs/${this.id}/download/`)

        // Create JSON file from response data
        const jsonString = JSON.stringify(response.data, null, 2)
        const blob = new Blob([jsonString], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `changelog-${this.id}.json`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Success',
            text: 'Version downloaded successfully',
            icon: 'CheckCircleIcon',
            variant: 'success',
          },
        })

        this.$emit('confirm', {
          response: response.data,
        })

        this.$nextTick(() => {
          this.$emit('close')
        })
      } catch (error) {
        this.loadingError = error.response?.data?.message || 'Error downloading version'
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
      this.loading = false
      this.loadingError = null
      this.$emit('cancel')
      this.$emit('close')
    },
  },
}
</script>
