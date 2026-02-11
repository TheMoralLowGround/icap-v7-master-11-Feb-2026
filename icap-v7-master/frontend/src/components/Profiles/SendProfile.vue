<template>
  <b-modal
    v-model="showModal"
    centered
    title="Send Process"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text class="send-process-message">
      Are you sure you want to send process <span class="text-primary process-name">{{ definition.name }}</span> to <span class="text-primary">{{ exportSystemName }}</span>?
    </b-card-text>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="sending"
        @click="ok()"
      >
        Send
        <b-spinner
          v-if="sending"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import axios from 'axios'
import {
  BModal, BCardText, BButton, BSpinner,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
  },
  props: {
    definition: {
      type: Object,
      required: true,
    },
    exportSystemName: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      sending: false,
    }
  },
  methods: {
    confirmHandler(event) {
      event.preventDefault()

      this.sending = true
      axios.post(`/dashboard/send_profile_to_remote_system/${this.definition.id}/`)
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.showModal = false
        })
        .catch(error => {
          const message = error?.response?.data?.detail || 'Error sending definition'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          this.sending = false
        })
    },
  },
}

</script>

<style scoped>
.send-process-message {
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  line-height: 1.5; /* Add some breathing room */
}

.process-name {
  font-weight: 600;
  display: inline; /* Changed from inline-block */
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
}
</style>
