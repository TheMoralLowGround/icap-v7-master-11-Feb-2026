<!--
 Organization: AIDocbuilder Inc.
 File: ExcelViewer.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code implementation and component design

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component manages the Excel viewer functionality, utilizing the GrapeCity SpreadJS component to display and interact with Excel files.
   It handles loading the Excel data, displaying a loading spinner or error message, and managing selected cells.

 Main Features:
   - Displays an error message if loading the Excel file fails.
   - Shows a loading spinner while the file is loading.
   - Uses GrapeCity's `GcSpreadSheets` to display the Excel workbook and individual worksheets.
   - Handles navigation to a specific cell when triggered.

 Dependencies:
   - `@grapecity/spread-sheets-vue`: For the Excel viewer and sheet manipulation.
   - `@grapecity/spread-excelio`: For loading and saving Excel files in JSON format.
   - `bootstrap-vue`: For UI components like alert and spinner.
   - `vue`: For reactive data binding and event handling.

 Notes:
   - The component listens for container size changes and refreshes the Excel viewer accordingly.
   - It also handles Vuex store updates to reflect the currently selected cell details.
-->

<template>
  <!-- Reference to the main container for the Excel viewer -->
  <div
    ref="excelViewer"
    class="excel-viewer"
  >
    <!-- Alert box for displaying error messages -->
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

    <!-- Spinner for loading state -->
    <div
      v-if="loading"
      class="text-center"
    >
      <b-spinner
        variant="primary"
      />
    </div>

    <!-- Spreadsheet viewer -->
    <gc-spread-sheets
      v-show="!loading && loadingError === null"
      class="spreadsheets"
      host-class="spreadHost"
      @workbookInitialized="initSpread"
    >
      <!-- Single worksheet inside the spreadsheet viewer -->
      <gc-worksheet />
    </gc-spread-sheets>
  </div>
</template>

<script>
import Vue from 'vue'

// eslint-disable-next-line no-unused-vars
import * as ExcelIO from '@grapecity/spread-excelio'
import * as GC from '@grapecity/spread-sheets'
import '@grapecity/spread-sheets-shapes'
import { GcSpreadSheets, GcWorksheet } from '@grapecity/spread-sheets-vue'
import '@grapecity/spread-sheets/styles/gc.spread.sheets.excel2016colorful.css'
import { BAlert, BSpinner } from 'bootstrap-vue'

import bus from '@/bus'
import { getBatchMediaURL } from '@/store/batch/helper'
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
  data() {
    // Reactive properties for component state
    return {
      spread: null, // Reference to the spreadsheet instance
      excelFile: null, // Stores the loaded Excel file
      selectedCellDetails: null,
      loading: true,
      loadingError: null,
      licenseStatus: null, // Status of the software license
      licenseInitialized: false, // Whether the license has been fetched from backend
      zoomLevel: 1.0, // Default zoom (100%)
    }
  },
  computed: {
    // Fetches the Excel data from the Vuex store
    excelData() {
      return this.$store.getters['batch/documentData'].excelData
    },
    // Fetches the currently selected node from the Vuex store
    selectedNode() {
      return this.$store.getters['batch/selectedNode']
    },
  },
  watch: {
    // Watches for changes in the Excel data and reloads the file when changes occur
    excelData: {
      deep: true,
      handler() {
        this.loadFile()
      },
    },
    // Watches for changes in selected cell details and updates the Vuex store
    selectedCellDetails: {
      handler() {
        this.$store.commit('batch/SET_SELECTED_CELL_DETAILS', this.selectedCellDetails)
      },
      deep: true,
    },
  },
  async created() {
    // Sets up event listeners on component creation
    localBus.$on('containerSizeChanged', this.onContainerSizeChange)
    bus.$on('goToSelectedNodeCell', this.goToSelectedNodeCell) // Handles navigation to a specific cell
    bus.$on('excelViewer/goToCell', this.goToCellEventHandler) // Responds to requests to navigate to a cell
    bus.$on('excelZoomIn', this.excelZoomIn)
    bus.$on('excelZoomOut', this.excelZoomOut)
    bus.$on('excelFitToWidth', this.excelFitToWidth)
    // Initialize the SpreadJS license from backend
    await this.initializeLicense()
  },
  mounted() {
    // Observes size changes of the Excel viewer for responsive adjustments
    resizeOb.observe(this.$refs.excelViewer)
  },
  beforeDestroy() {
    // Removes size observer before the component is destroyed
    resizeOb.unobserve(this.$refs.excelViewer)
  },
  destroyed() {
    // Cleans up event listeners to prevent memory leaks
    localBus.$off('containerSizeChanged', this.onContainerSizeChange)
    bus.$off('goToSelectedNodeCell', this.goToSelectedNodeCell)
    bus.$off('excelViewer/goToCell', this.goToCellEventHandler)
    bus.$off('excelZoomIn', this.excelZoomIn)
    bus.$off('excelZoomOut', this.excelZoomOut)
    bus.$off('excelFitToWidth', this.excelFitToWidth)
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
      // Assign the provided SpreadJS instance to the component's 'spread' property
      this.spread = spread

      // Synchronize the license status to ensure it's up-to-date
      this.syncLicenseStatus()

      // Check if the license status is valid
      if (this.licenseStatus !== 'valid') {
        // If the license is invalid, set loading to false and exit the function
        this.loading = false
        return
      }

      this.applyZoomToAllSheets(this.zoomLevel) // Set default zoom for all sheets

      // Enable calculation on demand to control when calculations occur
      // eslint-disable-next-line
      spread.options.calcOnDemand = true

      // Suspend painting to batch UI updates for performance optimization
      spread.suspendPaint()

      // Define a function to update selected cell details and sheet options
      const updateDetails = () => {
        this.updateSelectedCellDetails()
        this.setSheetOptions()
      }

      // Bind the 'SelectionChanged' event to update selected cell details
      spread.bind(spreadNS.Events.SelectionChanged, this.updateSelectedCellDetails.bind(this))

      // Bind the 'ActiveSheetChanged' event to update details when the active sheet changes
      spread.bind(spreadNS.Events.ActiveSheetChanged, updateDetails)

      // Resume painting to apply all pending UI updates
      spread.resumePaint()

      // Load the Excel file into the spreadsheet
      this.loadFile()
    },
    excelZoomIn() {
      if (this.spread) {
        this.zoomLevel = Math.min(this.zoomLevel + 0.1, 2.0) // Max zoom 200%
        this.applyZoomToAllSheets(this.zoomLevel)
      }
    },
    excelZoomOut() {
      if (this.spread) {
        this.zoomLevel = Math.max(this.zoomLevel - 0.1, 0.5) // Min zoom 50%
        this.applyZoomToAllSheets(this.zoomLevel)
      }
    },
    excelFitToWidth() {
      if (this.spread) {
        this.zoomLevel = 1.0 // Reset to 100% zoom
        this.applyZoomToAllSheets(this.zoomLevel)
      }
    },
    applyZoomToAllSheets(zoomLevel) {
      if (!this.spread) return

      const sheetCount = this.spread.getSheetCount()
      for (let i = 0; i < sheetCount; i += 1) {
        const sheet = this.spread.getSheet(i)
        if (sheet) {
          sheet.zoom(zoomLevel) // Apply zoom to each sheet
        }
      }
    },
    updateSelectedCellDetails() {
      const activeSheet = this.spread.getActiveSheet()
      const activeSheetIndex = this.spread.getActiveSheetIndex()
      const ranges = activeSheet.getSelections()
      const rangesAddress = spreadNS.CalcEngine.rangesToFormula(ranges, 0, 0, spreadNS.CalcEngine.RangeReferenceRelative.allRelative, false)

      // Function to convert column letter to zero-based index
      function columnLetterToIndex(letter) {
        return letter.split('').reduce((column, char, index) => column + (char.charCodeAt(0) - 64) * (26 ** (letter.length - index - 1)), 0) - 1
      }

      // Extract row and column from rangesAddress (assuming single cell selection for simplicity)
      const match = rangesAddress.match(/^([A-Z]+)(\d+)$/)
      let cellValue = null
      if (match) {
        const column = columnLetterToIndex(match[1])
        const row = parseInt(match[2], 10) - 1 // Convert to zero-based index
        cellValue = activeSheet.getValue(row, column)
      }

      this.selectedCellDetails = {
        sheetNumber: activeSheetIndex + 1, // Convert to 1-based sheet number
        sheetName: activeSheet.name(),
        cellRange: rangesAddress,
        cellValue,
      }
    },
    // load the excel file
    async loadFile() {
      if (!this.licenseInitialized || this.licenseStatus !== 'valid' || !this.excelData) return

      this.loading = true
      this.loadingError = null

      try {
        const response = await this.fetchFile()
        const fileBlob = await response.blob()
        const arrayBuffer = await fileBlob.arrayBuffer()
        const file = new File([arrayBuffer], 'Sample.xlsx', { type: fileBlob.type })

        await this.loadExcelDataFromFile(file)

        this.setSpreadOptions()
        this.setSheetOptions()
        this.updateSelectedCellDetails()
      } catch (error) {
        this.loadingError = 'Error loading Excel file'
      } finally {
        this.loading = false
        this.loadingError = null
      }
    },
    async fetchFile() {
      // Fetch the Excel file URL using batch details
      const batch = this.$store.getters['batch/batch'] // Get batch data from the Vuex store
      const { subPath } = batch // Extract the subPath from the batch data
      const { fileName } = this.excelData // Extract the fileName from the component's excelData
      const fileUrl = getBatchMediaURL(batch.id, subPath, fileName) // Construct the file URL
      return fetch(`${fileUrl}`) // Fetch the file from the constructed URL
    },

    loadExcelDataFromFile(excelFile) {
      // Load Excel data from the provided file
      return new Promise((resolve, reject) => {
        const excelIo = new ExcelIO.IO() // Create a new instance of ExcelIO
        excelIo.open(excelFile, json => {
          const workbookObj = json // Parse the JSON representation of the Excel file

          // Remove problematic shape formulas
          // eslint-disable-next-line no-unused-expressions
          // workbookObj.sheets?.forEach(sheet => {
          //   if (sheet.shapes) {
          //     sheet.shapes.forEach(shape => {
          //       const sformula = shape?.formula
          //       if (sformula === null || sformula === undefined) {
          //         // Skip null or undefined formulas
          //         // eslint-disable-next-line no-param-reassign
          //         shape.formula = ''
          //       }
          //     })
          //   }
          // })

          this.spread.fromJSON(workbookObj) // Load the workbook data into the spreadsheet
          resolve() // Resolve the promise once loading is complete
        },
        error => {
          // eslint-disable-next-line no-console
          // console.error('ExcelIO open error:', error)
          reject(error)
        })
      })
    },

    setSpreadOptions() {
      // Set general options for the spreadsheet instance
      const { spread } = this // Access the spreadsheet instance
      spread.options.allowContextMenu = false // Disable the context menu
      spread.options.tabEditable = false // Disable tab editing
      spread.options.allowSheetReorder = false // Disable sheet reordering
      spread.options.newTabVisible = false // Hide the option to add new tabs
      spread.options.readOnly = true
    },
    setSheetOptions() {
      // Configure specific options for the active sheet
      const sheet = this.spread.getActiveSheet() // Get the active sheet of the spreadsheet
      sheet.options.protectionOptions = {
        allowSelectLockedCells: true, // Allow selecting locked cells
        allowSelectUnlockedCells: true, // Allow selecting unlocked cells
        allowSort: true, // Allow sorting
        allowFilter: true, // Allow filtering
        allowResizeRows: true, // Allow resizing rows
        allowResizeColumns: true, // Allow resizing columns
        allowEditObjects: false, // Disallow editing objects
        allowDragInsertRows: false, // Disallow drag-and-insert rows
        allowDragInsertColumns: false, // Disallow drag-and-insert columns
        allowInsertRows: false, // Disallow inserting rows
        allowInsertColumns: false, // Disallow inserting columns
        allowDeleteRows: false, // Disallow deleting rows
        allowDeleteColumns: false, // Disallow deleting columns
        allowOutlineColumns: true, // Allow outlining columns
        allowOutlineRows: true, // Allow outlining rows
      }
      sheet.options.isProtected = true // Enable sheet protection

      // 🚫 Prevent double-click cell editing
      sheet.bind(GC.Spread.Sheets.Events.EditStarting, (e, args) => {
        // eslint-disable-next-line no-param-reassign
        args.cancel = true
      })

      // ✅ Prevent checkboxes and radio buttons from being clicked
      sheet.bind(GC.Spread.Sheets.Events.EditChange, (e, args) => {
        const cellType = args.sheet.getCellType(args.row, args.col)
        if (cellType instanceof GC.Spread.Sheets.CellTypes.CheckBox
         || cellType instanceof GC.Spread.Sheets.CellTypes.RadioButton) {
          // eslint-disable-next-line no-param-reassign
          args.cancel = true // Prevent toggling
        }
      })

      // ✅ Explicitly disable checkboxes and radio buttons in all cells
      // ✅ Only iterate through USED CELLS to improve performance
      const usedRange = sheet.getUsedRange()
      if (usedRange) {
        // eslint-disable-next-line no-plusplus
        for (let r = usedRange.row; r < usedRange.row + usedRange.rowCount; r++) {
          // eslint-disable-next-line no-plusplus
          for (let c = usedRange.col; c < usedRange.col + usedRange.colCount; c++) {
            const cellType = sheet.getCellType(r, c)

            // Skip empty cells and invalid types
            // eslint-disable-next-line no-continue
            if (!cellType) continue

            // Disable Checkboxes
            if (cellType instanceof GC.Spread.Sheets.CellTypes.CheckBox) {
              cellType.enabled(false) // Disable interaction
              sheet.setCellType(r, c, cellType)
              sheet.getCell(r, c).locked(true) // Lock the cell
            } else if (cellType instanceof GC.Spread.Sheets.CellTypes.RadioButton) {
              cellType.enabled(false)
              sheet.setCellType(r, c, cellType)
              sheet.getCell(r, c).locked(true) // Lock the cell
            }
          }
        }
      }

      // 🚫 Disable clicking on all floating objects (e.g., shapes, buttons, images)
      sheet.bind(GC.Spread.Sheets.Events.ShapeClick, (e, args) => {
        // eslint-disable-next-line no-param-reassign
        args.cancel = true
      })

      // 🚫 Disable FLOATING OBJECTS (shapes)
      const shapes = sheet.shapes.all()
      if (shapes && shapes.length > 0) {
        shapes.forEach(shape => {
          if (shape.options) {
            // eslint-disable-next-line no-param-reassign
            shape.options.isInteractive = false
          }
          // const formula = shape.formula()
          // if (!formula || typeof formula !== 'string') {
          //   shape.formula('') // clear it or assign safe default
          // }
        })
      }

      sheet.selectionPolicy(GC.Spread.Sheets.SelectionPolicy.range) // Set selection policy to range
    },

    onContainerSizeChange() {
      // Refresh the spreadsheet when the container size changes
      this.spread.refresh()
    },

    syncLicenseStatus() {
      // Synchronize the license status based on the spreadsheet's active sheet
      const activeSheet = this.spread.getActiveSheet() // Get the active sheet
      this.licenseStatus = activeSheet ? 'valid' : 'invalid' // Determine license status
    },

    goToSelectedNodeCell() {
      // Navigate to the cell corresponding to the selected node
      const { selectedNode } = this // Get the selected node

      if (selectedNode && selectedNode.highlight) {
        // If the selected node exists and has a highlight property
        this.goToCell(selectedNode.sheetName, selectedNode.cellRange) // Navigate to the specified cell
      }
    },

    goToCellEventHandler(data) {
      // Event handler to navigate to a specific cell
      this.goToCell(data.sheetName, data.cellRange)
    },

    goToCell(sheetName, cellRange) {
      // Navigate to a specified cell in the spreadsheet
      this.spread.setActiveSheet(sheetName) // Set the active sheet by its name

      const activeSheet = this.spread.getActiveSheet() // Get the active sheet
      const ranges = spreadNS.CalcEngine.formulaToRanges(activeSheet, cellRange, 0, 0) // Convert cell range to spreadsheet ranges
      const range = ranges[0].ranges[0] // Extract the first range from the result
      activeSheet.setSelection(range.row, range.col, range.rowCount, range.colCount) // Set the selection to the specified range
      activeSheet.showCell(range.row, range.col, spreadNS.VerticalPosition.top, spreadNS.HorizontalPosition.left) // Scroll to the specified cell

      this.updateSelectedCellDetails() // Update the details of the selected cell
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
