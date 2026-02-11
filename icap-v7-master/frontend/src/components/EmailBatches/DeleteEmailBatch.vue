<template>
  <b-modal
    v-model="showModal"
    centered
    title="Delete Email Batch"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      <div v-if="ids.length === 1">
        Are you sure you want to delete the email batch <span class="text-primary">{{ ids[0] }}</span>?
      </div>
      <div v-else>
        Are you sure you want to delete the following email batches?
        <div
          v-for="(id, index) of ids"
          :key="index"
          class="text-primary"
        >
          {{ id }}
        </div>
      </div>
      <b-alert
        variant="danger"
        :show="hasErrors"
        class="my-1"
      >
        <h5
          class="alert-body"
          style="margin-bottom: -10px;"
        >
          <strong>Unable to Delete the Batch</strong>
        </h5>
        <div class="alert-body">
          <p>{{ errorMessageText }}</p>
          <div class="text-primary">
            {{ firstErrorId }}
          </div>
        </div>
      </b-alert>
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
  BModal, BCardText, BButton, BSpinner, BAlert,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
    BAlert,
  },
  props: {
    ids: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      isDeleting: false,
      errorMessage: null,
    }
  },
  computed: {
    hasErrors() {
      return !!this.errorMessage
    },
    errorMessageText() {
      return this.errorMessage && this.errorMessage.message ? this.errorMessage.message : 'An error occurred'
    },
    firstErrorId() {
      return this.errorMessage && this.errorMessage.ids && this.errorMessage.ids[0] ? this.errorMessage.ids[0] : 'No ID available'
    },
  },
  methods: {
    confirmHandler(event) {
      event.preventDefault()
      this.errorMessage = null

      this.isDeleting = true

      axios.delete('/email-batches/delete_multiple/', {
        data: {
          ids: this.ids,
        },
      })
        .then(() => {
          this.$emit('deleted')

          this.$toast({
            component: ToastificationContent,
            props: {
              title: this.ids.length === 1 ? 'Email Batch deleted sucessfully' : 'Email Batches deleted sucessfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.errorMessage = null
          this.showModal = false
        })
        .catch(error => {
          this.errorMessage = error?.response?.data[0] || 'Error from delete API'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data[0]?.message || error?.response?.data?.detail || 'Somthing went wrong',
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
