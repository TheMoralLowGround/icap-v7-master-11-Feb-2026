<template>
  <b-modal
    v-model="showModal"
    centered
    :title="title"
    @hidden="$emit('modal-closed')"
  >
    <div class="text-center">
      <feather-icon
        icon="AlertTriangleIcon"
        size="48"
        class="text-danger mb-2"
      />
      <p class="mb-2">
        {{ message }}
      </p>
    </div>

    <template #modal-footer="{ cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="resetting"
        @click="handleReset"
      >
        <span v-if="resetting">Resetting...</span>
        <span v-else>Reset</span>
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BButton,
  BModal,
} from 'bootstrap-vue'
import axios from 'axios'
import FeatherIcon from '@core/components/feather-icon/FeatherIcon.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  name: 'DeleteOutputConfig',
  components: {
    BButton,
    BModal,
    FeatherIcon,
  },
  props: {
    title: {
      type: String,
      default: 'Configuration Error',
    },
    message: {
      type: String,
      default: 'Secret key not matching. Please reset existing configuration.',
    },
    apiEndpoint: {
      type: String,
      default: '/dashboard/output-channels/',
    },
    projectName: {
      type: String,
      required: true,
    },
    outputType: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      resetting: false,
    }
  },
  methods: {
    async handleReset() {
      try {
        this.resetting = true

        const params = {
          output_id: this.output_id,
        }
        await axios.delete(this.apiEndpoint, { params })

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Configuration Reset Successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        this.$emit('reset-success')
        this.showModal = false
      } catch (error) {
        const errorMsg = error.response?.data?.error || 'Failed to reset configuration'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: errorMsg,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      } finally {
        this.resetting = false
      }
    },
  },
}
</script>
