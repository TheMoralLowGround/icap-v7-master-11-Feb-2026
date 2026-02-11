<template>
  <b-modal
    v-model="showModal"
    centered
    title="Delete Project"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      Are you sure you want to delete project <span class="text-primary">{{ project.name }}</span>?
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

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
  },
  props: {
    project: {
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
      axios.delete(`/dashboard/admin/projects/${this.project.id}/`)
        .then(() => {
          this.$emit('deleted')

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Project deleted successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.showModal = false
        })
        .catch(error => {
          const message = error?.response?.data?.detail || 'Error deleting project'
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
