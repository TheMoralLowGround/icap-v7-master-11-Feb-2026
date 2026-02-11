<template>
  <b-card title="Delete not in use batches from disk">
    <b-button
      variant="primary"
      @click="showConfirmationModal = true"
    >
      Delete
    </b-button>

    <b-modal
      v-model="showConfirmationModal"
      centered
      title="Delete not in use batches from disk"
      @ok="submit"
    >
      <b-card-text>
        Are you sure you want to delete not in use batches from disk?
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
          :disabled="submiting"
          @click="ok()"
        >
          Delete
          <b-spinner
            v-if="submiting"
            small
            label="Small Spinner"
          />
        </b-button>
      </template>
    </b-modal>
  </b-card>
</template>

<script>
import {
  BButton, BCard, BCardText, BSpinner,
} from 'bootstrap-vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BCard,
    BCardText,
    BSpinner,
  },
  data() {
    return {
      showConfirmationModal: false,
      submiting: false,
    }
  },
  methods: {
    submit(event) {
      event.preventDefault()
      this.submiting = true

      axios.post('/pipeline/remove_not_in_use_batches/')
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.showConfirmationModal = false
          this.submiting = false
        })
        .catch(error => {
          const message = error?.response?.data?.detail || 'Somthing went wrong'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.submiting = false
        })
    },
  },
}
</script>
