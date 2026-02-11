<template>
  <div>
    <b-dropdown
      variant="outline-primary"
      :disabled="downloading"
    >
      <template #button-content>
        Docbuilder Payload
        <b-spinner
          v-if="downloading"
          small
          label="Small Spinner"
        />
      </template>

      <b-dropdown-item @click="download('batch')">
        Download for Batch
      </b-dropdown-item>
      <b-dropdown-item @click="download('document')">
        Download for Document
      </b-dropdown-item>
    </b-dropdown>
  </div>
</template>

<script>
import {
  BDropdownItem, BDropdown, BSpinner,
} from 'bootstrap-vue'
import axios from 'axios'
import exportFromJSON from 'export-from-json'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BDropdownItem,
    BDropdown,
    BSpinner,
  },
  data() {
    return {
      downloading: false,
    }
  },
  methods: {
    download(mode) {
      this.downloading = true

      const batchId = this.$store.getters['batch/batch'].id
      const documentId = this.$store.getters['batch/selectedDocumentId']
      const params = {
        batch_id: batchId,
      }
      if (mode === 'document') {
        params.document_id = documentId
      }

      axios.post('/pipeline/get_docbuilder_payload/', null, {
        params,
      }).then(res => {
        const fileName = mode === 'document' ? `Docbuilder-payload-document-${documentId}` : `Docbuilder-payload-batch-${batchId}`
        exportFromJSON({ data: res.data.docbuilder_payload, fileName, exportType: 'json' })
        this.downloading = false
      }).catch(error => {
        const message = error?.response?.data?.detail || 'Error downloading docbuilder payload'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        this.downloading = false
      })
    },
  },
}
</script>
