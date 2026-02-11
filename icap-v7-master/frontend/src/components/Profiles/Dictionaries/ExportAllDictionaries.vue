<template>
  <b-button
    variant="outline-success"
    size="md"
    :disabled="loading || disabled"
    @click="handleExport"
    class="mr-1"
  >
    <b-spinner
      v-if="loading"
      small
      class="mr-1"
    />
    {{ loading ? 'Exporting...' : 'Export All' }}
  </b-button>
</template>

<script>
import axios from 'axios'
import download from 'downloadjs'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import {
  BSpinner,
  BButton,
} from 'bootstrap-vue'

export default {
  name: 'ExportAllDictionaries',
  components: {
    BSpinner,
    BButton,
  },
  props: {
    disabled: { type: Boolean, default: false },
  },
  data() {
    return { loading: false }
  },
  computed: {
    processUid() {
      return this.$store.getters['profile/processUid']
    },
    currentProcessName() {
      return this.$store.getters['profile/currentProcessName']
    },
  },
  methods: {
    async handleExport() {
      if (!this.processUid) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'No process selected',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        return
      }

      this.loading = true
      try {
        // Use axios with responseType: 'blob' for file download (request Excel format)
        const response = await axios.post(
          '/pipeline/qdrant_vector_db/',
          {},
          {
            params: {
              endpoint: `dictionaries/processes/${this.processUid}/export`,
              request_type: 'GET',
            },
            responseType: 'blob',
          },
        )

        // Get the blob data
        const blob = response.data

        // Get content type from response headers
        const contentType = response.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        // Always export as Excel (.xlsx)
        const filename = `${this.currentProcessName}_export.xlsx`

        // Trigger download using downloadjs
        download(blob, filename, contentType)

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Export successful',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        // Emit success event
        this.$emit('export-success', this.currentProcessName)
      } catch (error) {
        let errMsg = 'Failed to export data'
        if (error.response?.data) {
          // Try to parse error from response
          try {
            const errorData = typeof error.response.data === 'string'
              ? JSON.parse(error.response.data)
              : error.response.data
            errMsg = errorData.detail || errorData.message || errMsg
          } catch {
            errMsg = error.message || errMsg
          }
        } else {
          errMsg = error.message || errMsg
        }

        this.$toast({
          component: ToastificationContent,
          props: {
            title: errMsg,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        // Emit fail event
        this.$emit('export-fail', { currentProcessName: this.currentProcessName, error })
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
