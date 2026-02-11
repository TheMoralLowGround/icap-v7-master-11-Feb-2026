<template>
  <b-button
    variant="primary"
    :disabled="submitting"
    @click="submit"
  >
    Submit
    <b-spinner
      v-if="submitting"
      small
      label="Small Spinner"
    />
  </b-button>
</template>

<script>
import { BButton, BSpinner } from 'bootstrap-vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BSpinner,
  },
  data() {
    return {
      submitting: false,
    }
  },
  methods: {
    // submit definition
    submit() {
      this.submitting = true
      const batch = this.$store.getters['batch/batch']
      axios.post('/pipeline/submit_definition_data/', null, {
        params: {
          batch_id: batch.id,
        },
      })
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.submitting = false
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Error submitting data',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
              text: error?.response?.data?.detail,
            },
          },
          {
            timeout: false,
          })
          this.submitting = false
        })
    },
  },
}
</script>
