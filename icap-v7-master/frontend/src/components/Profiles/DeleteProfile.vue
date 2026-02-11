<template>
  <b-modal
    v-model="showModal"
    centered
    title="Delete Process"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text class="text-wrap">
      Are you sure you want to delete process
      <!-- <span class="text-primary"> <truncate-text :text="profile.name || ''" :max-length="100" /></span>? -->
      <span class="text-primary">{{ profile.name }}</span>?
    </b-card-text>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="danger"
        :disabled="isDeleting"
        @click="ok()"
      >
        Delete
        <b-spinner
          v-if="isDeleting"
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
// import TruncateText from './TruncateText.vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
    // TruncateText,
  },
  props: {
    profile: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      isDeleting: false,
    }
  },
  methods: {
    confirmHandler(event) {
      event.preventDefault()

      this.isDeleting = true
      axios.delete(`/dashboard/profiles/${this.profile.id}/`)
        .then(() => {
          this.$emit('deleted')
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Process deleted successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.showModal = false
        })
        .catch(error => {
          const message = error?.response?.data?.detail || 'Error deleting process'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          this.isDeleting = false
        })
    },
  },
}

</script>
<style scoped>
.text-wrap {
  overflow-wrap: break-word;
  white-space: normal;
  width: 100%;
}
</style>
