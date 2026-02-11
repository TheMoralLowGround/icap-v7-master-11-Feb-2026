<template>
  <b-button
    variant="outline-success"
    size="md"
    :disabled="loading || disabled"
    @click="handleExport"
  >
    <b-spinner
      v-if="loading"
      small
      class="mr-1"
    />
    {{ loading ? 'Exporting...' : 'Export' }}
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
  name: 'ExportToExcel',
  components: {
    BSpinner,
    BButton,
  },
  props: {
    tableName: { type: String, required: true },
    disabled: { type: Boolean, default: false },
  },
  data() {
    return { loading: false }
  },
  computed: {
    processUid() {
      return this.$store.getters['profile/processUid']
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
        // Use same API pattern as dictionaries - GET request with Excel format
        const response = await axios.post(
          '/pipeline/qdrant_vector_db/',
          {},
          {
            params: {
              endpoint: `parties/processes/${this.processUid}/tables/${this.tableName}/export`,
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
        const filename = `${this.tableName}_export.xlsx`

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
        this.$emit('export-success', this.tableName)
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
        this.$emit('export-fail', { tableName: this.tableName, error })
      } finally {
        this.loading = false
      }
    },

    // async handleExport() {
    //   this.loading = true
    //   try {
    //     const response = await axios.post(
    //       '/dashboard/export_lookup_data/',
    //       { dictionary_name: this.tableName },
    //       { responseType: 'blob' },
    //     )

    //     const url = window.URL.createObjectURL(new Blob([response.data]))
    //     const link = document.createElement('a')
    //     link.href = url
    //     link.setAttribute('download', `${this.tableName}_export.xlsx`)
    //     document.body.appendChild(link)
    //     link.click()
    //     document.body.removeChild(link)
    //     window.URL.revokeObjectURL(url)

    //     this.$toast({
    //       component: ToastificationContent,
    //       props: {
    //         title: 'Export successful',
    //         icon: 'CheckIcon',
    //         variant: 'success',
    //       },
    //     })

    //     // Emit success event
    //     this.$emit('export-success', this.tableName)
    //   } catch (error) {
    //     const errMsg = error.response?.data?.message || 'Failed to export data'
    //     this.$toast({
    //       component: ToastificationContent,
    //       props: {
    //         title: errMsg,
    //         icon: 'AlertTriangleIcon',
    //         variant: 'danger',
    //       },
    //     })
    //     // Emit fail event
    //     this.$emit('export-fail', { tableName: this.tableName, error })
    //   } finally {
    //     this.loading = false
    //   }
    // },

  },
}
</script>
