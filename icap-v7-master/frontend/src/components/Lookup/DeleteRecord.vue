<template>
  <b-modal
    v-model="showModal"
    centered
    title="Delete Record"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      <p>Are you sure you want to delete a record with following details?</p>
      <p><b>Table</b>: {{ tableName }}</p>
      <p><b>ID</b>: {{ record.ID }}</p>
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
import axios from '@/rules-backend-axios'
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
    record: {
      type: Object,
      required: true,
    },
    tableName: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      isDeleting: false,
    }
  },
  computed: {
    selectedDefintionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },
  },
  methods: {
    confirmHandler(event) {
      event.preventDefault()

      this.isDeleting = true
      axios.post('/delete_db_record/', {
        table_name: this.tableName,
        record_id: this.record.ID,
        definition_version: this.selectedDefintionVersion,
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
          this.showModal = false
        })
        .catch(error => {
          const message = error?.response?.data?.detail || 'Error deleting record'
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
