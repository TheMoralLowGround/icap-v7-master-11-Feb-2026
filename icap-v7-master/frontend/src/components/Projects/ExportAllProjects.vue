<template>
  <b-modal
    v-model="showModal"
    centered
    title="Export All Projects"
    @ok="handleExport"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
      <div>
        Are you sure you want to export <span class="text-primary">{{ totalRecords }}</span> projects?
      </div>
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
        :disabled="exporting"
        @click="ok()"
      >
        Export
        <b-spinner
          v-if="exporting"
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
  BButton,
  BCardText,
  BModal,
  BSpinner,
} from 'bootstrap-vue'
import exportFromJSON from 'export-from-json'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BCardText,
    BModal,
    BSpinner,
  },
  props: {
    totalRecords: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      exporting: false,
    }
  },
  methods: {
    handleExport() {
      this.exporting = true

      const payload = {
        ids: [],
        export_all: true,
      }

      this.exportProjects(payload, 'All Projects')
        .then(() => {
          this.exporting = false
          this.$emit('exported')
          this.showModal = false
        })
        .catch(() => {
          this.exporting = false
        })
    },
    exportProjects(data, fileName) {
      return axios.post('/dashboard/admin/projects/export/', data)
        .then(res => {
          exportFromJSON({
            data: res.data,
            fileName,
            exportType: 'json',
          })
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting projects',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          throw error
        })
    },
  },
}
</script>
