<template>
  <b-button
    variant="outline-primary"
    @click="exportToExcel"
  >
    Export
    <b-spinner
      v-if="exporting"
      small
      label="Exporting..."
    />
  </b-button>
</template>

<script>
import {
  BButton,
  BSpinner,
} from 'bootstrap-vue'
import * as XLSX from 'xlsx'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BSpinner,
  },
  props: {
    documents: {
      type: Array,
      required: true,
      default: () => [],
    },
  },
  data() {
    return {
      exporting: false,
    }
  },
  methods: {
    exportToExcel() {
      if (!this.documents || this.documents.length === 0) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'No documents to export',
            icon: 'AlertCircleIcon',
            variant: 'warning',
          },
        })
        return
      }

      this.exporting = true

      try {
        // Prepare data for export
        const exportData = this.documents.map(doc => ({
          'Doc Type': doc.doc_type || '',
          'Translated Doc Type': doc.translated_doc_type || '',
          'Content Location': doc.content_location || '',
          Template: doc.template || '',
          'Name Matching Option': doc.name_matching_option || '',
          'Name Matching Text': doc.name_matching_text || '',
          Category: doc.category || '',
          Language: doc.language || '',
          'OCR Engine': doc.ocr_engine || '',
          'Page Rotate': doc.page_rotate ? 'Yes' : 'No',
          Barcode: doc.barcode ? 'Yes' : 'No',
          'Show Embedded Img': doc.show_embedded_img ? 'Yes' : 'No',
        }))

        // Create worksheet
        const worksheet = XLSX.utils.json_to_sheet(exportData)

        // Create workbook
        const workbook = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Process Documents')

        // Generate file name with timestamp
        const timestamp = new Date().toISOString().slice(0, 10)
        const fileName = `Process_Documents_${timestamp}.xlsx`

        // Export file
        XLSX.writeFile(workbook, fileName)

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Documents exported successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
      } catch (error) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error exporting documents',
            text: error.message,
            icon: 'XIcon',
            variant: 'danger',
          },
        })
      } finally {
        this.exporting = false
      }
    },
  },
}
</script>
