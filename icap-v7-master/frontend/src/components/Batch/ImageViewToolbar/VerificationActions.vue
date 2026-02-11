<template>
  <div class="d-flex align-items-center wrapper">
    <!-- Verify Button -->
    <b-button
      variant="outline-primary"
      :disabled="verifying"
      @click="verify"
    >
      Verify
      <!-- Spinner displayed when verifying is true -->
      <b-spinner
        v-if="verifying"
        small
        label="Small Spinner"
      />
    </b-button>

    <!-- Submit Button -->
    <b-button
      :variant="submitting || !verified ? 'secondary' : 'primary'"
      :disabled="submitting || !verified"
      @click="showModal = true"
    >
      Submit
      <b-spinner
        v-if="submitting"
        small
        label="Small Spinner"
      />
    </b-button>

    <!-- Warning Modal -->
    <b-modal
      v-model="showModal"
      centered
      title="Submit Transaction Data"
      @ok="submit"
    >
      <b-card-text>
        Are you sure you want to submit transaction data to CW1 ?
      </b-card-text>

      <!-- Custom Modal Footer -->
      <template #modal-footer="{ ok, cancel }">
        <!-- Cancel Button -->
        <b-button
          variant="secondary"
          @click="cancel()"
        >
          Cancel
        </b-button>
        <b-button
          variant="primary"
          :disabled="submitting"
          @click="ok()"
        >
          Submit
          <b-spinner
            v-if="submitting"
            small
            label="Small Spinner"
          />
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>
import {
  BButton, BSpinner, BModal, BCardText,
} from 'bootstrap-vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton, // Button component
    BSpinner, // Spinner for loading indication
    BModal, // Modal component for confirmation dialogs
    BCardText, // Card text component for modal content
  },
  data() {
    return {
      verifying: false, // Tracks if the data is being verified
      verified: false, // Tracks if data verification is successful
      showModal: false, // Controls visibility of the modal
      submitting: false, // Tracks if the data is being submitted
    }
  },
  computed: {
    // Retrieves verification details from the Vuex store
    verificationDetails() {
      return this.$store.getters['batch/verificationDetails']
    },
  },
  methods: {
    // Verifies the data before allowing submission
    async verify() {
      this.verifying = true // Start verifying process
      let error = null
      let message = 'Data Json saved successfully'

      try {
        const data = {
          data: this.verificationDetails, // Data payload
        }

        await axios.post(`/pipeline/save_verification_details/${this.$route.params.id}/`, data)

        this.verified = true // Mark data as verified
      } catch (err) {
        // Handle error and set error message
        message = err?.message || 'Error verifying Data Json'
        error = err
      }

      // Show toast notification with success or error message
      this.$toast({
        component: ToastificationContent,
        props: {
          title: message,
          icon: error ? 'AlertTriangleIcon' : 'CheckIcon',
          variant: error ? 'danger' : 'success',
        },
      })

      this.verifying = false // End verifying process
    },
    // Submits the data after confirmation
    async submit() {
      this.submitting = true // Start submission process

      try {
        await axios.post(`/pipeline/release_transaction/${this.$route.params.id}/`) // API call for submission

        this.submitting = false // End submission process

        this.$router.push({ name: 'home' }) // Redirect to home on success
      } catch (error) {
        // Handle error and show toast notification
        this.$toast({
          component: ToastificationContent,
          props: {
            title: error?.message || 'Error submitting Data Json',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        this.submitting = false // End submission process
      }
    },
  },
}
</script>

<style scoped>
/* Styling for the wrapper div */
.wrapper {
  column-gap: 1rem; /* Adds spacing between buttons */
}
</style>
