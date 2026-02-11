<template>
  <b-modal
    :visible="modelValue"
    title="Import Doctypes"
    size="md"
    centered
    no-close-on-backdrop
    @hide="close"
  >
    <b-form @submit.prevent="handleImport">
      <b-row>
        <b-col md="12">
          <b-form-group
            label="Select File"
          >
            <b-form-file
              ref="fileInput"
              v-model="file"
              accept=".csv,.xlsx,.xls"
              placeholder="Choose a CSV or Excel file..."
              @change="onFileChange"
            />
          </b-form-group>
        </b-col>
      </b-row>

      <b-alert
        variant="danger"
        :show="errorMessage !== null"
        class="mt-3"
      >
        <div class="alert-body">
          <p class="mb-0">
            {{ errorMessage }}
          </p>
        </div>
      </b-alert>

      <b-alert
        variant="warning"
        :show="parsedData.length > 0"
        class="mt-1"
      >
        <div class="alert-body">
          <p class="mb-0">
            <strong>Warning:</strong>
            Importing will replace all existing doctypes with the data from the file.
          </p>
        </div>
      </b-alert>
    </b-form>

    <template #modal-footer="{ cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        variant="primary"
        :disabled="parsedData.length === 0 || importing"
        @click="handleImport"
      >
        Import & Replace
        <b-spinner
          v-if="importing"
          small
          label="Importing..."
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BAlert,
  BButton,
  BCol,
  BForm,
  BFormFile,
  BFormGroup,
  BRow,
  BSpinner,
} from 'bootstrap-vue'
import * as XLSX from 'xlsx'

export default {
  components: {
    BAlert,
    BButton,
    BCol,
    BForm,
    BFormFile,
    BFormGroup,
    BRow,
    BSpinner,
  },
  props: {
    modelValue: Boolean,
  },
  data() {
    return {
      file: null,
      parsedData: [],
      errorMessage: null,
      importing: false,
    }
  },
  computed: {
    previewData() {
      return this.parsedData.slice(0, 5)
    },
  },
  watch: {
    modelValue(newVal) {
      if (!newVal) {
        this.resetDialog()
      }
    },
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files[0]
      if (!file) {
        this.parsedData = []
        return
      }

      this.errorMessage = null
      const fileName = file.name.toLowerCase()

      if (fileName.endsWith('.csv')) {
        this.parseCSV(file)
      } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
        this.parseExcel(file)
      } else {
        this.errorMessage = 'Unsupported file format. Please upload a CSV, XLSX, or XLS file.'
        this.parsedData = []
      }
    },
    parseCSV(file) {
      const reader = new FileReader()

      reader.onload = e => {
        try {
          const text = e.target.result
          const lines = text.split('\n').filter(line => line.trim())

          if (lines.length < 2) {
            this.errorMessage = 'File must contain a header row and at least one data row'
            this.parsedData = []
            return
          }

          // Parse header - normalize by removing spaces and converting to lowercase
          const header = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/\s+/g, ''))
          const docTypeIndex = header.indexOf('doctype')
          const docCodeIndex = header.indexOf('doccode')
          const addToProcessIndex = header.indexOf('addtoprocess')

          if (docTypeIndex === -1 || docCodeIndex === -1) {
            this.errorMessage = 'File must contain "docType" and "docCode" columns'
            this.parsedData = []
            return
          }

          // Parse data rows
          const data = []
          for (let i = 1; i < lines.length; i += 1) {
            const values = this.parseCSVLine(lines[i])

            if (values.length >= 2) {
              const docType = values[docTypeIndex]?.trim()
              const docCode = values[docCodeIndex]?.trim()
              const addToProcess = addToProcessIndex !== -1
                ? this.parseBoolean(values[addToProcessIndex]?.trim())
                : false

              if (docType && docCode) {
                data.push({
                  docType,
                  docCode,
                  addToProcess,
                })
              }
            }
          }

          if (data.length === 0) {
            this.errorMessage = 'No valid data found in file'
            this.parsedData = []
            return
          }

          this.parsedData = data
        } catch (error) {
          this.errorMessage = `Error parsing CSV: ${error.message}`
          this.parsedData = []
        }
      }

      reader.onerror = () => {
        this.errorMessage = 'Error reading file'
        this.parsedData = []
      }

      reader.readAsText(file)
    },
    parseExcel(file) {
      const reader = new FileReader()

      reader.onload = e => {
        try {
          const data = new Uint8Array(e.target.result)
          const workbook = XLSX.read(data, { type: 'array' })

          // Get the first sheet
          const firstSheetName = workbook.SheetNames[0]
          const worksheet = workbook.Sheets[firstSheetName]

          // Convert to JSON
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

          if (jsonData.length < 2) {
            this.errorMessage = 'File must contain a header row and at least one data row'
            this.parsedData = []
            return
          }

          // Parse header - normalize by removing spaces and converting to lowercase
          const header = jsonData[0].map(h => (h || '').toString().trim().toLowerCase().replace(/\s+/g, ''))
          const docTypeIndex = header.indexOf('doctype')
          const docCodeIndex = header.indexOf('doccode')
          const addToProcessIndex = header.indexOf('addtoprocess')

          if (docTypeIndex === -1 || docCodeIndex === -1) {
            this.errorMessage = 'File must contain "docType" and "docCode" columns'
            this.parsedData = []
            return
          }

          // Parse data rows
          const parsedData = []
          for (let i = 1; i < jsonData.length; i += 1) {
            const row = jsonData[i]

            if (row && row.length >= 2) {
              const docType = row[docTypeIndex] ? row[docTypeIndex].toString().trim() : ''
              const docCode = row[docCodeIndex] ? row[docCodeIndex].toString().trim() : ''
              const addToProcess = addToProcessIndex !== -1
                ? this.parseBoolean(row[addToProcessIndex])
                : false

              if (docType && docCode) {
                parsedData.push({
                  docType,
                  docCode,
                  addToProcess,
                })
              }
            }
          }

          if (parsedData.length === 0) {
            this.errorMessage = 'No valid data found in file'
            this.parsedData = []
            return
          }

          this.parsedData = parsedData
        } catch (error) {
          this.errorMessage = `Error parsing Excel file: ${error.message}`
          this.parsedData = []
        }
      }

      reader.onerror = () => {
        this.errorMessage = 'Error reading file'
        this.parsedData = []
      }

      reader.readAsArrayBuffer(file)
    },
    parseCSVLine(line) {
      const result = []
      let current = ''
      let inQuotes = false

      for (let i = 0; i < line.length; i += 1) {
        const char = line[i]

        if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === ',' && !inQuotes) {
          result.push(current)
          current = ''
        } else {
          current += char
        }
      }
      result.push(current)

      return result
    },
    parseBoolean(value) {
      if (!value) return false
      // Handle boolean type directly
      if (typeof value === 'boolean') return value
      // Handle number type
      if (typeof value === 'number') return value === 1
      // Handle string type
      const normalized = value.toString().toLowerCase().trim()
      return normalized === 'true' || normalized === '1' || normalized === 'yes'
    },
    handleImport() {
      if (this.parsedData.length === 0) {
        this.errorMessage = 'No data to import'
        return
      }

      this.importing = true

      // Emit the parsed data to parent component
      this.$emit('import', this.parsedData)

      // Close modal
      setTimeout(() => {
        this.importing = false
        this.$emit('update:modelValue', false)
      }, 500)
    },
    resetDialog() {
      this.file = null
      this.parsedData = []
      this.errorMessage = null
      this.importing = false
      if (this.$refs.fileInput) {
        this.$refs.fileInput.reset()
      }
    },
    close() {
      this.resetDialog()
      this.$emit('update:modelValue', false)
    },
  },
}
</script>

<style scoped>
.preview-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>
