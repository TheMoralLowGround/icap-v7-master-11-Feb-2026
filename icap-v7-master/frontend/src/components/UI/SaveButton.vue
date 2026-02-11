<template>
  <b-button
    :disabled="saving"
    :variant="variant"
    @click="save"
  >
    Save
    <b-spinner
      v-if="saving"
      small
      label="Small Spinner"
    />
  </b-button>
</template>

<script>
import { BButton, BSpinner } from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BSpinner,
  },
  props: {
    variant: {
      type: String,
      required: false,
      default: 'outline-primary',
    },
    action: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      saving: false,
    }
  },
  methods: {
    save() {
      this.saving = true

      this.$store.dispatch(this.action).then(res => {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
        this.saving = false
      })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Something went wrong!',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.saving = false
        })
    },
  },
}
</script>
