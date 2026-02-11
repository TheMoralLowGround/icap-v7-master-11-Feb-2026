<template>
  <b-modal
    v-model="showModal"
    title="Import Data"
    @ok="onSubmit"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
      <b-form-group
        label="Table"
      >
        <v-select
          ref="vSelect"
          v-model="tableName"
          transition=""
          :clearable="false"
          :options="tableOptions"
          @open="scrollToSelected"
        />
      </b-form-group>

      <div class="my-1">
        Process: {{ profileName }}
      </div>

      <div
        class="d-flex"
        style="column-gap:10px;"
      >
        <div>
          <b-form-group>
            <b-form-radio-group
              v-model="fileMode"
              button-variant="outline-primary"
              :options="[
                { text: 'Excel', value: 'excel' },
                { text: 'CSV', value: 'csv' },
              ]"
              buttons
            />
          </b-form-group>
        </div>
        <div>
          <b-button
            variant="outline-primary"
            :disabled="!tableName || downloading"
            @click="downloadTemplateFile"
          >
            Download Template {{ fileMode === 'csv' ? 'CSV' : 'Excel' }}
            <b-spinner
              v-if="downloading"
              small
              label="Small Spinner"
            />
          </b-button>
        </div>
      </div>

      <div v-if="fileMode === 'csv'">
        <b-form-group
          label="CSV File"
        >
          <b-form-file
            v-model="csvFile"
            accept=".csv"
          />
        </b-form-group>
      </div>

      <div v-if="fileMode === 'excel'">
        <b-form-group
          label="Excel File"
        >
          <b-form-file
            v-model="excelFile"
            accept=".xlsx"
            @input="parseSheetNames"
          />
        </b-form-group>

        <b-form-group
          label="Sheet"
        >
          <v-select
            v-model="excelSheet"
            transition=""
            :clearable="false"
            :options="excelSheetOptions"
          />
        </b-form-group>
      </div>

      <b-form-group>
        <b-form-checkbox
          v-model="deleteExistingRecords"
        >
          Replace all existing records for {{ profileName }} process
        </b-form-checkbox>
      </b-form-group>

      <b-alert
        class="my-1"
        variant="danger"
        :show="errorMessage !== null ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ errorMessage }}
          </p>
        </div>
      </b-alert>

      <detailed-error-messages :messages="detailedErrorMessages" />
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
        :disabled="submitting || !enableSubmit"
        @click="ok()"
      >
        Submit
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BButton, BModal, BSpinner, BCardText, BFormGroup, BFormFile, BFormRadioGroup,
  BFormCheckbox, BAlert,
} from 'bootstrap-vue'
import axios from '@/rules-backend-axios'
import vSelect from 'vue-select'
import * as XLSX from 'xlsx'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import DetailedErrorMessages from '../DetailedErrorMessages.vue'

export default {
  components: {
    BButton,
    BModal,
    BSpinner,
    BCardText,
    vSelect,
    BFormGroup,
    BFormFile,
    BFormRadioGroup,
    BFormCheckbox,
    BAlert,
    DetailedErrorMessages,
  },
  data() {
    return {
      fileMode: 'excel',
      showModal: true,
      submitting: false,
      downloading: false,
      tableName: null,
      csvFile: null,
      excelFile: null,
      excelSheet: null,
      excelSheetOptions: [],
      deleteExistingRecords: false,
      errorMessage: null,
      detailedErrorMessages: [],
    }
  },
  computed: {
    enableSubmit() {
      if (this.fileMode === 'csv') {
        return this.tableName && this.csvFile
      } if (this.fileMode === 'excel') {
        return this.tableName && this.excelFile && this.excelSheet
      }
      return false
    },
    tableOptions() {
      return this.$store.getters['lookup/tables']
    },
    selectedDefintionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },
    profileName() {
      return this.$store.getters['dataView/selectedDefinition'].definition_id
    },
  },
  methods: {
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs.vSelect.$refs.dropdownMenu
        const selectedIndex = this.tableOptions.indexOf(this.tableName)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.tableOptions.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
    parseSheetNames() {
      if (this.excelFile) {
        const reader = new FileReader()
        reader.onload = event => {
          const data = event.target.result
          const workBook = XLSX.read(data, { type: 'binary' })
          this.excelSheetOptions = workBook.SheetNames
          this.excelSheet = workBook.SheetNames ? workBook.SheetNames[0] : null
        }
        reader.readAsBinaryString(this.excelFile)
      } else {
        this.excelSheetOptions = []
        this.excelSheet = null
      }
    },
    downloadTemplateFile() {
      this.downloading = true

      axios.get('/get_upload_template/', {
        params: {
          table_name: this.tableName,
          definition_version: this.selectedDefintionVersion,
          file_type: this.fileMode === 'csv' ? 'csv' : 'xlsx',
        },
        responseType: 'blob',
      }).then(response => {
        const fileExtention = this.fileMode === 'csv' ? 'csv' : 'xlsx'
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${this.tableName} Template.${fileExtention}`)
        document.body.appendChild(link)
        link.click()

        this.downloading = false
      }).catch(async error => {
        // convert blob response to json
        let responseDataJSON = null
        if (error?.response?.data) {
          const responseData = await error?.response?.data.text()
          responseDataJSON = JSON.parse(responseData)
        }

        const message = responseDataJSON?.detail || 'Error downloading template file'
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
    onSubmit(event) {
      event.preventDefault()
      this.submitting = true

      const formData = new FormData()
      formData.append('table_name', this.tableName)
      formData.append('profile_name', this.profileName)
      formData.append('delete_existing_records', this.deleteExistingRecords)

      if (this.fileMode === 'csv') {
        formData.append('csv_file', this.csvFile)
      } else if (this.fileMode === 'excel') {
        formData.append('xlsx_file', this.excelFile)
        formData.append('sheet_name', this.excelSheet)
      }

      axios.post('/upload_records_to_db/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }).then(res => {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        this.submitting = false
        this.errorMessage = null
        this.detailedErrorMessages = []
        this.showModal = false
      }).catch(error => {
        this.errorMessage = error?.response?.data?.detail || 'Error importing data'
        this.detailedErrorMessages = error?.response?.data?.messages || []
        this.submitting = false
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
