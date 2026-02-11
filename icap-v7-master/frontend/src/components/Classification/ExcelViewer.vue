<template>
  <div
    ref="excelViewer"
    class="excel-viewer"
  >
    <b-alert
      variant="danger"
      :show="!loading && loadingError !== null ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <div
      v-if="loading"
      class="text-center"
    >
      <b-spinner
        variant="primary"
      />
    </div>

    <gc-spread-sheets
      v-show="!loading && loadingError === null"
      class="spreadsheets"
      host-class="spreadHost"
      @workbookInitialized="initSpread"
    >
      <gc-worksheet />
    </gc-spread-sheets>
  </div>
</template>

<script>
import Vue from 'vue'

// eslint-disable-next-line no-unused-vars
import { GcSpreadSheets, GcWorksheet, GcColumn } from '@grapecity/spread-sheets-vue'
import '@grapecity/spread-sheets/styles/gc.spread.sheets.excel2016colorful.css'
import '@grapecity/spread-sheets-shapes'
import * as GC from '@grapecity/spread-sheets'
import * as ExcelIO from '@grapecity/spread-excelio'
import { BSpinner, BAlert } from 'bootstrap-vue'

import { initSpreadJSLicense } from '@/utils/spreadjs-license'

const spreadNS = GC.Spread.Sheets

const localBus = new Vue()
const resizeOb = new ResizeObserver(() => {
  localBus.$emit('containerSizeChanged')
})

export default {
  components: {
    GcSpreadSheets,
    GcWorksheet,
    BSpinner,
    BAlert,
  },
  props: {
    url: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      spread: null,
      excelFile: null,
      loading: true,
      loadingError: null,
      licenseStatus: null,
      licenseInitialized: false,
    }
  },
  watch: {
    // Watch for changes in the 'url' prop
    url(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.loadFile()
      }
    },
  },
  async created() {
    localBus.$on('containerSizeChanged', this.onContainerSizeChange)
    await this.initializeLicense()
    this.loadFile()
  },
  mounted() {
    resizeOb.observe(this.$refs.excelViewer)
  },
  beforeDestroy() {
    resizeOb.unobserve(this.$refs.excelViewer)
  },
  destroyed() {
    localBus.$off('containerSizeChanged', this.onContainerSizeChange)
  },
  methods: {
    async initializeLicense() {
      try {
        await initSpreadJSLicense()
        this.licenseInitialized = true
      } catch (error) {
        // console.error('Failed to initialize SpreadJS license:', error)
        this.licenseInitialized = false
      }
    },
    initSpread(spread) {
      this.spread = spread
      this.syncLicenseStatus()

      if (this.licenseStatus !== 'valid') {
        this.loading = false
        return
      }
      // eslint-disable-next-line
      spread.options.calcOnDemand = true

      spread.suspendPaint()

      const updateDetails = () => {
        this.setSheetOptions()
      }

      // spread.bind(spreadNS.Events.SelectionChanged, this.updateSelectedCellDetails.bind(this))
      spread.bind(spreadNS.Events.ActiveSheetChanged, updateDetails)

      spread.resumePaint()
      this.loadFile()
    },
    async loadFile() {
      if (!this.licenseInitialized || this.licenseStatus !== 'valid' || !this.url) {
        return
      }

      this.loading = true

      let response
      try {
        response = await this.fetchFile()
      } catch {
        this.loadingError = 'Error fetching excel file'
        this.loading = false
        return
      }

      const fileBlob = await response.blob()
      const file = new File([fileBlob], 'Sample.xlsx')
      await this.loadExcelDataFromFile(file)

      this.setSpreadOptions()
      this.setSheetOptions()

      this.loading = false
      this.loadingError = null
    },
    async fetchFile() {
      const fileUrl = this.url
      return fetch(`${fileUrl}`)
    },
    loadExcelDataFromFile(excelFile) {
      return new Promise(resolve => {
        const excelIo = new ExcelIO.IO()
        excelIo.open(excelFile, json => {
          const workbookObj = json
          this.spread.fromJSON(workbookObj)
          resolve()
        })
      })
    },
    setSpreadOptions() {
      const { spread } = this
      spread.options.allowContextMenu = false
      spread.options.tabEditable = false
      spread.options.allowSheetReorder = false
      spread.options.newTabVisible = false
    },
    setSheetOptions() {
      const sheet = this.spread.getActiveSheet()
      sheet.options.protectionOptions = {
        allowSelectLockedCells: true,
        allowSelectUnlockedCells: true,
        allowSort: true,
        allowFilter: true,
        allowResizeRows: true,
        allowResizeColumns: true,
        allowEditObjects: false,
        allowDragInsertRows: false,
        allowDragInsertColumns: false,
        allowInsertRows: false,
        allowInsertColumns: false,
        allowDeleteRows: false,
        allowDeleteColumns: false,
        allowOutlineColumns: true,
        allowOutlineRows: true,
      }
      sheet.options.isProtected = true
      sheet.selectionPolicy(GC.Spread.Sheets.SelectionPolicy.range)
    },
    onContainerSizeChange() {
      this.spread.refresh()
    },
    syncLicenseStatus() {
      const activeSheet = this.spread.getActiveSheet()
      this.licenseStatus = activeSheet ? 'valid' : 'invalid'
    },
  },
}
</script>

<style scoped>
.excel-viewer {
  height: 100%;
  position: relative;
  overflow: hidden;
}

.spreadsheets {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
}
</style>
