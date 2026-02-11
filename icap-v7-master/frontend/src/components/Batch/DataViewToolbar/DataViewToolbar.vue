<!--
Organization: AIDocbuilder Inc.
File: DataViewToolbar.vue
Version: 6.0

Authors:
    - Vinay - Initial implementation
    - Ali - Code optimization

Last Updated By: Ali
Last Updated At: 2024-12-17

Description:
    This is a vue component for show the toolbar related to the data view. All tool bar components trigger from here conditionally.

Dependencies:
    - perant components

Main Features:
    - Save tables and keys.
    - Update tables and keys.
    - Add rules, columns, lookups and others.
 -->
<template>
  <!-- Main container for the definitions toolbar -->
  <div class="d-flex align-items-center definitions-toolbar">
    <!-- Verification Toolbar: Displays selectors for document and table in 'verification' mode -->
    <div
      v-if="mainMode === 'verification'"
      class="verification-toolbar-wrapper d-flex align-items-center"
    >
      <div class="document-selector-wrapper">
        <!-- Component for selecting a document -->
        <document-selector />
      </div>
      <div class="table-selector-wrapper">
        <!-- Component for selecting a table -->
        <table-selector />
      </div>
    </div>

    <!-- Node Editor: Displays a node editor if the mode is 'verification' -->
    <node-editor
      v-if="mainMode === 'verification'"
      width="30"
    />

    <!-- Add Table Button: Displayed when the mode is 'automated-table-model' and data is loading -->
    <div
      v-if="dataViewerLoading && ['automated-table-model'].includes(mode)"
      class="add-table"
    >
      <add-table
        label="Table"
        button-variant="outline-primary"
        @add="addTable"
      />
    </div>

    <!-- Main toolbar functionality when data is not loading or errors are not present -->
    <template v-if="!dataViewerLoading && !dataViewerLoadingError">

      <!-- Add Table Button: Displayed for specific modes -->
      <div
        v-if="['automated-table-model', 'table-models', 'table-columns', 'table-keys', 'table-rule-items', 'table-lookup-items', 'table-normalizer', 'test'].includes(mode)"
        class="add-table"
        :class="{'add-table-responsive': mode === 'test'}"
      >
        <add-table
          label="Table"
          button-variant="outline-primary"
          @add="addTable"
        />
      </div>

      <!-- Defined Key Actions: Displayed when the mode is 'definedKeys' -->
      <defined-key-actions v-if="mainMode === 'definedKeys'" />

      <!-- Mode Options: Displayed for key or table settings modes -->
      <mode-options v-if="mainMode === 'keySettings' || mainMode === 'tableSettings'" />

      <!-- Explore Lookup Button: Visible in the 'explore-lookup' view -->
      <b-button
        v-if="batchView === 'explore-lookup'"
        :variant="'primary'"
      >
        Explore Lookup
      </b-button>

      <!-- Add Columns Button: Displayed in 'table-columns' mode -->
      <div
        v-if="mode === 'table-columns'"
        class="add-columns"
      >
        <add-item
          label="Column"
          button-variant="outline-primary"
          @add="addColumns"
        />
      </div>

      <!-- Add Table Normalizer Items Button: Displayed in 'table-normalizer' mode -->
      <div
        v-if="mode === 'table-normalizer'"
        class="add-columns"
      >
        <add-item
          label="Rule"
          button-variant="outline-primary"
          @add="addTableNormalizerItems"
        />
      </div>

      <!-- Add Rule Button and Dropdown: Displayed in 'table-rule-items' mode -->
      <b-button
        v-if="mode === 'table-rule-items' && tableFields.length"
        :disabled="!label"
        variant="outline-primary"
        @click.stop="selectOption('rules')"
      >
        <feather-icon
          icon="PlusIcon"
        />
        Add Rule
      </b-button>
      <v-select
        v-if="mode === 'table-rule-items' && tableFields.length"
        ref="tableFields"
        v-model="label"
        :options="tableFields"
        style="min-width: 150px;"
        @open="scrollToSelected"
      />

      <!-- Test Options: Displayed in 'test' mode -->
      <template v-if="mode === 'test'">
        <test-options />
        <div>
          <!-- Checkbox to toggle the display of unused fields -->
          <b-form-checkbox
            v-model="displayNotInUseFields"
            v-b-tooltip.hover.top="{boundary:'window'}"
            title="Display Not in use fields"
          >
            Not in use
          </b-form-checkbox>
        </div>

        <div>
          <!-- Batch Definition Version Selector -->
          <batch-defintion-version />
        </div>
      </template>

      <!-- Add Key Model Button -->
      <div
        v-if="mode === 'key-models'"
      >
        <b-button
          variant="outline-primary"
          :disabled="!enableAddKeyModel"
          @click="addKeyModel"
        >
          <feather-icon
            icon="PlusIcon"
            class="mr-25"
          />
          <span>Model</span>
        </b-button>
      </div>

      <!-- Add Key Button: Displayed in 'key-items', 'table-keys', or 'table-column-prompts' modes -->
      <div
        v-if="mode === 'key-items' || mode === 'table-keys' || mode === 'table-column-prompts'"
        class="add-keys"
      >
        <add-item
          label="Key"
          button-variant="outline-primary"
          @add="addKeys"
        />
      </div>

      <!-- Add Key Rules Button: Displayed in 'key-rules' mode -->
      <div
        v-if="mode === 'key-rules'"
        class="add-columns"
      >
        <add-item
          label="Rule"
          button-variant="outline-primary"
          @add="addKeyRules"
        />
      </div>

      <!-- Copy Rules Button: Visible in 'key-rules' mode -->
      <b-button
        v-if="mode === 'key-rules'"
        variant="outline-primary"
        @click="displayCopyKeyRules = true"
      >
        Copy Rules
      </b-button>

      <!-- Lookup Section: Add Queries and Run Lookup -->
      <template v-if="lookupInitialized && (mode === 'key-lookup' || mode === 'table-lookup' || batchView === 'explore-lookup' )">
        <div
          class="add-columns"
        >
          <add-item
            label="Query"
            plural-label="Queries"
            button-variant="outline-primary"
            @add="addQueries"
          />
        </div>
        <run-lookup />
      </template>

      <!-- Add Table Rules Button: Displayed in 'table-rules' mode -->
      <div
        v-if="mode === 'table-rules'"
        class="add-columns"
      >
        <add-item
          label="Rule"
          button-variant="outline-primary"
          @add="addTableRules"
        />
      </div>

      <!-- Copy Table Rules Button: Visible in 'table-rules' mode -->
      <b-button
        v-if="mode === 'table-rules'"
        variant="outline-primary"
        @click="displayCopyTableRules = true"
      >
        Copy Rules
      </b-button>

      <!-- Save Keys Button: Shown in key-related modes -->
      <b-button
        v-if="(mainMode === 'keySettings' && mode !== 'key-lookup') || (mode === 'key-lookup' && lookupInitialized)"
        variant="outline-primary"
        :disabled="savingKeys || validatingKeys"
        @click="saveKeys"
      >
        Save
        <b-spinner
          v-if="savingKeys"
          small
          label="Small Spinner"
        />
      </b-button>

      <!-- Test Options: Available in 'keySettings' mode or when exploring lookup -->
      <test-options
        v-if="mainMode === 'keySettings' || batchView === 'explore-lookup'"
      />

      <!-- Spacer for Layout Flexibility -->
      <div class="flex-grow-1" />

      <!-- Test Models Button: Visible in 'table-models' mode -->
      <b-button
        v-if="mode === 'table-models' && !isExcelBatch"
        :variant="testModelDisabled ? 'outline-secondary' : 'outline-primary'"
        :disabled="testModelDisabled || submittingModelsTestRequst"
        @click="testModels"
      >
        Test Models
        <b-spinner
          v-if="submittingModelsTestRequst"
          small
          label="Small Spinner"
        />
      </b-button>

      <!-- Toggle Cell Label Button: Visible for Excel batches -->
      <b-dropdown
        v-if="isExcelBatch"
        text="Cell Range Permissions"
        variant="primary"
        class="ml-auto"
        right
      >
        <template #button-content>
          <span>{{ cellRangePermission }}</span>
        </template>

        <b-form-group>
          <b-form-radio-group
            v-model="cellRangePermission"
            name="cellRangePermissions"
            class="p-1"
          >
            <b-form-radio value="Capture 1st Sheet Only">
              Capture 1st Sheet Only
            </b-form-radio>
            <b-form-radio value="Capture by Sheet Names">
              Capture by Sheet Names
            </b-form-radio>
            <b-form-radio value="Capture by Sheet Numbers">
              Capture by Sheet Numbers
            </b-form-radio>
          </b-form-radio-group>
        </b-form-group>
      </b-dropdown>

      <!-- Save Table Button: Available in 'tableSettings' mode -->
      <b-button
        v-if="mainMode === 'tableSettings' && mode !== 'test' "
        variant="outline-primary"
        :disabled="savingTable || validatingTable"
        @click="saveTable"
      >
        Save
        <b-spinner
          v-if="savingTable"
          small
          label="Small Spinner"
        />
      </b-button>

      <!-- Navigation Buttons: Back to Previous Modes -->
      <b-button
        v-if="mode === 'key-rules'"
        variant="outline-primary"
        @click="closeKeyRules"
      >
        <feather-icon
          icon="ChevronsLeftIcon"
          class="mr-25"
        />
        <span class="pb_1px">Back to Rules</span>
      </b-button>

      <b-button
        v-if="mode === 'key-lookup'"
        variant="outline-primary"
        @click="closeKeyLookups"
      >
        <feather-icon
          icon="ChevronsLeftIcon"
          class="mr-25"
        />
        <span class="pb_1px">Back to Lookups</span>
      </b-button>

      <b-button
        v-if="mode === 'table-lookup'"
        variant="outline-primary"
        @click="closeTableLookups"
      >
        <feather-icon
          icon="ChevronsLeftIcon"
          class="mr-25"
        />
        <span class="pb_1px">Back to Table Lookups</span>
      </b-button>

      <b-button
        v-if="mode === 'table-rules'"
        variant="outline-primary"
        @click="closeTableRules"
      >
        <feather-icon
          icon="ChevronsLeftIcon"
          class="mr-25"
        />
        <span class="pb_1px">Back to Table Rules</span>
      </b-button>

      <!-- Switch to Key View Button -->
      <b-button
        v-if="batchView === 'explore-lookup'"
        variant="outline-primary"
        @click="switchToKeyView"
      >
        Back to Key View
      </b-button>
    </template>

    <!-- Automated Table Model Actions -->
    <atm-actions v-if="mainMode === 'automatedTableModel'" />

    <!-- Copy Key Rules Modal -->
    <copy-rules
      v-if="displayCopyKeyRules"
      mode="key"
      @modal-closed="displayCopyKeyRules = false"
    />

    <!-- Copy Table Rules Modal -->
    <copy-rules
      v-if="displayCopyTableRules"
      mode="table"
      @modal-closed="displayCopyTableRules = false"
    />

    <!-- Add Row Button -->
    <b-button
      v-if="mainMode === 'verification' && !isDeleteRow"
      class="ml-auto"
      :variant="isAddRow ? 'primary' : 'secondary'"
      @click="activeAddRow"
    >
      <feather-icon icon="CopyIcon" />
      Add a row
    </b-button>

    <!-- Delete Row Button -->
    <b-button
      v-if="mainMode === 'verification' && !isAddRow && !isRowDeleteOption && isAnyDeletableRow"
      class="ml-auto"
      :variant="isDeleteRow ? 'danger' : 'secondary'"
      @click="activeDeleteRow"
    >
      <feather-icon icon="Trash2Icon" />
      Delete a row
    </b-button>

    <!-- Row Deletion Confirmation -->
    <template v-if="isDeleteRow && isRowDeleteOption">
      <p class="text-danger mb-0">
        Delete selected row?
      </p>
      <b-button-group size="sm">
        <!-- Confirm Delete Button -->
        <b-button
          variant="outline-danger"
          @click="confirmRowDelete"
        >
          <feather-icon
            icon="CheckIcon"
            size="16"
          />
        </b-button>
        <!-- Cancel Delete Button -->
        <b-button
          variant="outline-secondary"
          @click="cancleRowDelete"
        >
          <feather-icon
            icon="XIcon"
            size="16"
          />
        </b-button>
      </b-button-group>
    </template>
  </div>
</template>

<script>
import {
  BButton, BSpinner, BFormCheckbox, VBTooltip, BButtonGroup, BDropdown, BFormGroup, BFormRadioGroup, BFormRadio,
} from 'bootstrap-vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import AddItem from '@/components/UI/AddItem.vue'
import AddTable from '@/components/UI/AddTable.vue'
import vSelect from 'vue-select'
import bus from '@/bus'
import BatchDefintionVersion from '@/components/Batch/BatchDefinitionVersion.vue'

import TableSelector from '@/components/UI/TableSelector.vue'
import { cloneDeep } from 'lodash'
import DocumentSelector from '../SelectorToolbar/DocumentSelector.vue'
import ModeOptions from './ModeOptions.vue'
import DefinedKeyActions from './DefinedKeyActions.vue'
import AtmActions from './AtmActions.vue'
import TestOptions from './TestOptions.vue'
import RunLookup from './RunLookup.vue'
import CopyRules from './CopyRules.vue'
import NodeEditor from '../NodeEditor.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BButton,
    BButtonGroup,
    BSpinner,
    AddItem,
    AddTable,
    BFormCheckbox,
    DefinedKeyActions,
    AtmActions,
    TestOptions,
    vSelect,
    BatchDefintionVersion,
    RunLookup,
    CopyRules,
    NodeEditor,
    ModeOptions,
    TableSelector,
    DocumentSelector,
    BDropdown,
    BFormGroup,
    BFormRadioGroup,
    BFormRadio,
  },
  data() {
    return {
      // Flags for various operations like saving, validating, etc.
      savingTable: false,
      savingKeys: false,
      validatingTable: false,
      validatingKeys: false,
      submittingModelsTestRequst: false,
      displayCopyKeyRules: false,
      displayCopyTableRules: false,
      isRowDeleteOption: false,

      // Variables for table and sheet settings
      label: '',
      // Tracks the selected radio option
      cellRangePermission: 'Capture by Sheet Names', // Default selected item,
      definitionVersion: this.$store.getters['dataView/selectedDefinitionVersion'],
    }
  },
  computed: {
    getCellRangePermission() {
      return this.$store.getters['dataView/getCellRangePermission']
    },
    selectedDocument() {
      return this.$store.getters['batch/selectedDocument'] // Returns the current route name from Vue Router
    },
    raJsonDocumentData() {
      return this.$store.getters['batch/documentData'] // Selected document from ra json
    },
    showSheetName() {
      return this.cellRangePermission === 'Capture by Sheet Names'
    },
    showSheetNumber() {
      return this.cellRangePermission === 'Capture by Sheet Numbers'
    },
    isCaptureByFirstSheet() {
      return this.cellRangePermission === 'Capture 1st Sheet Only'
    },

    // Current route name (used for route-based logic)
    currentRouteName() {
      return this.$route.name
    },

    // Profile name is used for document identification, currently returns empty string
    profileName() {
      // if (this.name && this.project && this.documents.docType) {
      //   return `${this.name.toUpperCase()}_${this.project}_${this.documents.docType}`
      // }
      return ''
    },

    // Getter for the batch view state from the store
    batchView() {
      return this.$store.getters['batch/view']
    },

    // Getter to check if the data viewer is loading
    dataViewerLoading() {
      return this.$store.getters['dataView/loading']
    },

    // Getter for any loading errors in the data viewer
    dataViewerLoadingError() {
      return this.$store.getters['dataView/loadingError']
    },

    // Main mode state with getter and setter to update the store
    mainMode: {
      get() {
        return this.$store.getters['dataView/mainMode']
      },
      set(value) {
        this.$store.dispatch('dataView/setMainMode', value)
      },
    },

    // Getter for current mode (e.g., view or edit mode)
    mode() {
      return this.$store.getters['dataView/mode']
    },

    // Getter for the selected definition (data model) from the store
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition']
    },

    // Getter for the selected model type from the store
    selectedModelType() {
      return this.$store.getters['dataView/selectedModelType']
    },

    // Getter for application settings options
    options() {
      return this.$store.getters['applicationSettings/options']
    },

    // Getter and setter for displaying not-in-use fields in the data view
    displayNotInUseFields: {
      get() {
        return this.$store.getters['dataView/displayNotInUseFields']
      },
      set(value) {
        this.$store.commit('dataView/SET_DISPLAY_NOT_IN_USE_FIELDS', value)
      },
    },

    // Getter to check if the lookup is initialized
    lookupInitialized() {
      return this.$store.getters['lookup/initialized']
    },

    // Check if the batch is Excel based
    isExcelBatch() {
      return this.$store.getters['batch/batch']?.isExcel
    },

    // Check if adding a new key model is enabled (when there are no existing key models)
    enableAddKeyModel() {
      return this.$store.getters['dataView/keyModels'].length === 0
    },

    // Check if testing the selected model type is disabled based on the options
    testModelDisabled() {
      const modeltypes = this.options['options-meta-root-model-type'].items
      const modeltype = modeltypes.find(e => e.value === this.selectedModelType)

      return !modeltype?.applicableFor.includes('test')
    },

    // Getter for whether the add row option is enabled in the batch
    isAddRow() {
      return this.$store.getters['batch/getIsAddRow']
    },

    // Getter for whether the delete row option is enabled in the batch
    isDeleteRow() {
      return this.$store.getters['batch/getIsDeleteRow']
    },

    // Getter for checking if any deletable rows exist in the batch
    isAnyDeletableRow() {
      return this.$store.getters['batch/getIsAnyDeletableRow']
    },

    // Retrieve selected document's tables
    tables() {
      // eslint-disable-next-line no-unused-expressions
      return this.$store.getters['batch/selectedDocument']?.tables || []
    },
    // Getter for the selected table ID from the store
    selectedTableName() {
      return this.$store.getters['dataView/selectedTableName']
    },

    // Retrieve the current table based on selected table ID
    table() {
      const definitionTables = this.$store.getters['dataView/table']

      if (!definitionTables.length) {
        return null
      }

      // Find matching definition table by name
      // eslint-disable-next-line camelcase
      const definitionTable = definitionTables.find(table => table.table_name === this.selectedTableName)

      // If no matching definition table, try to find document table directly by name
      if (!definitionTable) {
        return this.tables.find(i => i.table_name === this.selectedTableName) || null
      }

      // eslint-disable-next-line camelcase
      const { table_unique_id } = definitionTable
      // eslint-disable-next-line camelcase
      return this.tables.find(i => i.table_unique_id === table_unique_id)
    },

    // Retrieve table columns based on the current definition
    definitionTableColumns() {
      const tableColumns = this.$store.getters['dataView/tableColumns']

      if (!tableColumns) { return [] }
      return tableColumns.map(tableColumn => tableColumn.colLabel)
    },

    // Return the sorted list of keys (fields) in the table
    tableFields() {
      if (!this.table) return []

      let keys = []
      this.table.rows.forEach(item => {
        keys = keys.concat(Object.keys(item))
      })
      keys = [...new Set(keys)]

      const sortedKeys = []

      // Sort keys based on table columns
      this.definitionTableColumns.forEach(definitionTableColumn => {
        if (keys.includes(definitionTableColumn) && !sortedKeys.includes(definitionTableColumn)) {
          sortedKeys.push(definitionTableColumn)
        }
      })

      // In verification mode, include additional keys
      if (this.mainMode === 'verification') {
        keys.forEach(key => {
          if (!sortedKeys.includes(key) && !key.startsWith('None') && !key.startsWith('notInUse') && !key.endsWith('_1') && !key.endsWith('_2')) {
            sortedKeys.push(key)
          }
        })
      } else {
        keys.forEach(key => {
          if (!sortedKeys.includes(key)) {
            sortedKeys.push(key)
          }
        })
      }
      return sortedKeys
    },
    selectedBatch() {
      return this.$store.getters['batch/batch']
    },
    keyItemsDefinition() {
      return this.$store.getters['dataView/keyItems']
    },

  },
  watch: {
    cellRangePermission(val) {
      this.$store.commit('dataView/SET_CELL_RANGE_PERMISSION', val)
    },
  },
  created() {
    // Register event listeners for various events related to table changes
    bus.$on('dataView/onTableChange', this.onTableChange) // When table changes
    bus.$on('dataView/saveTableData', this.saveTableData) // When table data needs to be saved
    bus.$on('dataView/toggleRowDeleteOption', this.toggleRowDeleteOption) // When row delete option is toggled

    // Set initial value for full cell label based on the store value
    if (this.getCellRangePermission != null) {
      const permissionMapping = {
        captureFirstSheet: 'Capture 1st Sheet Only',
        captureBySheetNames: 'Capture by Sheet Names',
        captureBySheetNumbers: 'Capture by Sheet Numbers',
      }

      this.cellRangePermission = permissionMapping[this.getCellRangePermission] || this.getCellRangePermission
    }
  },
  destroyed() {
    // Remove event listeners when the component is destroyed
    bus.$off('dataView/onTableChange', this.onTableChange)
    bus.$off('dataView/saveTableData', this.saveTableData)
    bus.$off('dataView/toggleRowDeleteOption', this.toggleRowDeleteOption)
  },
  methods: {
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs?.tableFields?.$refs?.dropdownMenu
        const selectedIndex = this.tableFields.indexOf(this.label)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.tableFields.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
    // Event handler for table changes
    async onTableChange(data) {
      const { curentTableId, prevTableId } = data
      let noValidationError = true
      // Only save the table if not in "test" or "automated-table-model" mode
      if (!['test', 'automated-table-model'].includes(this.mode)) {
        noValidationError = await this.saveTable() // Validate and save table
      }

      if (!noValidationError) {
        // If validation fails, revert to the previous table
        this.$store.commit('dataView/SET_SELECTED_TABLE_ID', prevTableId)

        return
      }

      // Update the store with the new table ID and refresh the data view
      this.$store.commit('dataView/SET_SELECTED_TABLE_ID', curentTableId)
      bus.$emit('dataView/refreshData')
    },

    // Display an error message if the form has invalid data
    displayInvalidFormError() {
      this.$toast({
        component: ToastificationContent,
        props: {
          title: 'Please correct the form errors',
          icon: 'AlertTriangleIcon',
          variant: 'danger',
        },
      })
    },

    // Save table data after validating it
    async saveTable(PointerEvent) {
      this.validatingTable = true

      // Skip validation for table-column-prompts mode
      if (this.mode !== 'table-column-prompts') {
        // Validate the table model first
        const tableModelsIsValid = await this.validateForm('validateTableModel')
        if (!tableModelsIsValid) {
          // Switch to table-models mode if validation fails
          if (this.mode !== 'table-models') {
            this.$store.dispatch('dataView/setMode', 'table-models')
          }
          this.displayInvalidFormError()
          this.validatingTable = false
          return
        }

        // Validate the table keys
        const tablKeysIsValid = await this.validateForm('validateKeyItems')
        if (!tablKeysIsValid) {
          // Switch to table-keys mode if validation fails
          if (this.mode !== 'table-keys') {
            this.$store.dispatch('dataView/setMode', 'table-keys')
          }
          this.displayInvalidFormError()
          this.validatingTable = false
          return
        }

        // Validate the table normalizer items
        const tableNormalizerItemsIsValid = await this.validateForm('validateTableNormalizerItems')
        if (!tableNormalizerItemsIsValid) {
          // Switch to table-normalizer mode if validation fails
          if (this.mode !== 'table-normalizer') {
            this.$store.dispatch('dataView/setMode', 'table-normalizer')
          }
          this.displayInvalidFormError()
          this.validatingTable = false
          return
        }

        // Validate the table rules if in 'table-rules' mode
        if (this.mode === 'table-rules') {
          const tableRulesIsValid = await this.validateForm('validateTableRules')
          if (!tableRulesIsValid) {
            this.displayInvalidFormError()
            this.validatingTable = false
            return
          }
        }
      }

      // If all validations pass, proceed to save the table
      this.validatingTable = false

      if (!PointerEvent) {
        // Return early if there is no pointer event (e.g., just validating)
        // eslint-disable-next-line consistent-return
        return true
      }

      // Trigger the save table data function if a pointer event occurred
      this.saveTableData()
    },

    // Save the table data to the server
    async saveTableData(cusTableName = '') {
      this.savingTable = true

      // Note: Removed special handling for table-column-prompts mode
      // Now uses the same save flow as table-keys to save columnPrompts
      // to table_definition_data.columnPrompts in the definition

      // If in table-rules mode, save the table rule items first
      if (this.mode === 'table-rules') {
        await this.$store.dispatch('dataView/saveTableRuleItem')
      }

      if (this.mode === 'table-lookup') {
        this.$store.dispatch('dataView/saveTableLookupItem')
      }

      // Check if selected table from document needs to be added to definition
      // This handles the case where a document table doesn't exist in definition
      const definitionTables = this.$store.getters['dataView/table'] || []
      const selectedTableName = this.$store.getters['dataView/selectedTableName']

      if (selectedTableName) {
        const tableExistsInDefinition = definitionTables.some(t => t.table_name === selectedTableName)

        // If table doesn't exist in definition but exists in document, add it
        if (!tableExistsInDefinition) {
          const documentTables = this.$store.getters['batch/selectedDocument']?.tables || []
          const documentTable = documentTables.find(t => t.table_name === selectedTableName)

          if (documentTable) {
            // Add table to definition with same structure as AddTable
            const tableId = definitionTables.length
            await this.$store.dispatch('dataView/addTable', {
              tableName: selectedTableName,
              tableId,
              isAuto: 'auto',
            })

            // Update selected table references
            this.$store.commit('dataView/SET_SELECTED_TABLE_NAME', selectedTableName)
            this.$store.commit('dataView/SET_SELECTED_TABLE_ID', selectedTableName)
          }
        }
      }

      // Get the current table data and batch information from the store
      const table = this.$store.getters['dataView/table']
      const key = this.$store.getters['dataView/key']
      let url
      let payload
      const batch = this.$store.getters['batch/batch']

      // If the full cell label feature is disabled, remove the sheetName and sheetNumber properties
      const { identifier, tableStart, tableEnd } = table[0]?.table_definition_data?.models

      if (!this.showSheetName || this.isCaptureByFirstSheet) {
        delete identifier?.sheetName
        delete tableStart?.sheetName
        delete tableEnd?.sheetName
      }
      if (!this.showSheetNumber || this.isCaptureByFirstSheet) {
        delete identifier?.sheetNumber
        delete tableStart?.sheetNumber
        delete tableEnd?.sheetNumber
      }

      const { columns, keyItems } = table[0]?.table_definition_data
      // If the full cell label feature is disabled, reset the sheet name in key items
      if (!this.showSheetName || !this.showSheetNumber || this.isCaptureByFirstSheet) {
        // eslint-disable-next-line no-unused-expressions
        keyItems?.forEach(item => {
          if (item.typeData && item?.typeData?.cellRangeItems) {
            item.typeData.cellRangeItems.forEach(cellRangeItem => {
              if (!this.showSheetName || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                delete cellRangeItem.sheetName
              }
              if (!this.showSheetNumber || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                delete cellRangeItem.sheetNumber
              }
            })
          }
          // Additional reset for `excelRegexExtractor` structure
          if (item?.excelRegexExtractor?.cellRanges) {
            item.excelRegexExtractor.cellRanges.forEach(cellRange => {
              if (!this.showSheetName || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                delete cellRange.sheetName
              }
              if (!this.showSheetNumber || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                delete cellRange.sheetNumber
              }
            })
          }
        })
      }

      if (columns) {
        // eslint-disable-next-line no-unused-expressions
        columns?.forEach(column => {
        // eslint-disable-next-line no-unused-expressions
          column?.cellRanges?.forEach(cellRange => {
            if (!this.showSheetName || this.isCaptureByFirstSheet) {
              // eslint-disable-next-line no-param-reassign
              delete cellRange.sheetName
            }
            if (!this.showSheetNumber || this.isCaptureByFirstSheet) {
              // eslint-disable-next-line no-param-reassign
              delete cellRange.sheetNumber
            }
          })
        })
      }

      key.cell_range_permission = this.cellRangePermission
      // Determine the correct URL and payload for saving based on the current route
      if (this.currentRouteName === 'template-batch') {
        url = 'dashboard/update_template_definition_by_version/'
        payload = {
          template_name: batch.definitionId || '',
          definition_version: this.$store.getters['dataView/selectedDefinitionVersion'],
          table,
        }
      } else {
        url = '/update_definition_by_version/'

        payload = {
          layout_id: this.raJsonDocumentData.pages[0]?.layout_id || this.selectedDocument.layoutId,
          definition_id: this.selectedDefinition.definition_id || this.selectedBatch.definitionId,
          vendor: this.selectedDocument.vendor,
          definition_version: this.$store.getters['dataView/selectedDefinitionVersion'],
          table,
          key,
        }
      }
      if (!this.raJsonDocumentData.pages[0]?.layout_id) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'No layoutId Available',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        this.savingTable = false
      } else {
        // Send the data to the server using axios and handle the response
        axios.post(url, payload)
          .then(res => {
            // Show a success message upon successful save
            this.$toast({
              component: ToastificationContent,
              props: {
                title: 'Definition updated successfully',
                icon: 'CheckIcon',
                variant: 'success',
              },
            })
            this.savingTable = false
            this.$store.dispatch('dataView/setSelectedDefinition', res.data)
          })
          .catch(async error => {
            // Handle 404 error with fallback definition creation
            if (error.response && error.response.status === 404) {
              // If 404, fallback to calling /definitions/ to create new definition
              try {
                const definitionVersion = this.$store.getters['dataView/selectedDefinitionVersion']
                const allTables = cloneDeep(this.$store.getters['dataView/table']) // ← array
                const allKeys = cloneDeep(this.$store.getters['dataView/key'])

                const filteredTables = env => {
                  if (definitionVersion === env) {
                    return allTables
                  }

                  // Filter out tables where table_name matches cusTableName
                  const filtered = allTables.filter(t => t.table_name !== cusTableName)

                  // Reset table definition data while preserving table metadata
                  return filtered.map(t => ({
                    table_id: t.table_id,
                    table_name: t.table_name,
                    table_unique_id: t.table_unique_id,
                    table_definition_data: {
                      models: {
                        type: 'auto',
                        headerTrigger: '',
                        close: '',
                        open: '',
                        endingSep: '',
                        patterns: '',
                        autoPatterns: [],
                        userSelectedPatterns: [],
                        extendedUserSelectedPatterns: [],
                        userSelectedOb: [],
                        storedPosition: '',
                        multipleLineRecord: false,
                        tableStart: '',
                        tableEnd: '',
                        identifier: '',
                        multishipmentType: 'Singlesheet Multishipment',
                        sheetName: '',
                        sheetNameIdentifierCondition: '',
                        gLAction: '',
                        posCheck: 'true',
                        shapeCheck: 'true',
                        chunkThreshold: '20',
                        tableThreshold: '20',
                        lineThreshold: '15',
                        extraChunkSpace: '0',
                        allowMerging: 'false',
                        keyValtoCol: 'true',
                        autoPositionShiftCal: 'false',
                        ignoreChargesTable: 'false',
                        forceLiner: 'true',
                        sumOfChargeAmount: {
                          dty: false,
                          vat: false,
                          oth: false,
                        },
                      },
                      columns: [],
                      keyItems: [],
                      ruleItems: [],
                      normalizerItems: [],
                      lookupItems: [],
                    },
                  }))
                }

                const fallbackPayload = {
                  vendor: this.selectedDocument.vendor,
                  definition_id: this.selectedDefinition?.definition_id || batch?.definitionId,
                  layout_id: this.raJsonDocumentData.pages[0]?.layout_id || this.selectedDocument.layoutId,
                  data: {
                    uat: {
                      key: allKeys,
                      table: filteredTables('uat'),
                    },
                    prod: {
                      key: allKeys,
                      table: filteredTables('prod'),
                    },
                    draft: {
                      key: allKeys,
                      table: filteredTables('draft'),
                    },
                  },
                }
                const response = await axios.post('/definitions/', fallbackPayload)

                if (response) {
                  this.$toast({
                    component: ToastificationContent,
                    props: {
                      title: 'Definition Added Successfully.',
                      icon: 'InfoIcon',
                      variant: 'info',
                    },
                  })
                  // this.$store.dispatch('dataView/setSelectedDefinition', response.data)
                  await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
                }
              } catch (fallbackErr) {
                const fallbackMsg = fallbackErr?.response?.data?.detail || 'Unable to Add Definition'

                this.$toast({
                  component: ToastificationContent,
                  props: {
                    title: fallbackMsg,
                    icon: 'AlertTriangleIcon',
                    variant: 'danger',
                  },
                })
              }
            } else {
              // Handle other types of errors
              const message = error?.response?.data?.detail || 'Something went wrong'
              this.$toast({
                component: ToastificationContent,
                props: {
                  title: message,
                  icon: 'AlertTriangleIcon',
                  variant: 'danger',
                },
              })
            }
          })
          .finally(() => {
            this.savingTable = false
          })
      }
    },
    async addTable(data) {
      // Check if the current view is 'table' and validate the current table before proceeding
      if (this.batchView === 'table') {
        const noValidationError = await this.saveTable()
        if (!noValidationError) {
          // Stop the process if the table validation fails
          return
        }
      }
      // Dispatch an action to add a new table with the provided data
      await this.$store.dispatch('dataView/addTable', {
        tableName: data?.tableName,
        tableId: data?.tableId,
      })

      // Update the store with the new table's ID as the selected table
      this.$store.commit('dataView/SET_SELECTED_TABLE_NAME', data?.tableName)
      this.$store.commit('dataView/SET_SELECTED_TABLE_ID', data?.tableName)
      // Save the current table data to persist changes
      this.saveTableData(data?.tableName)
      // If not in 'automated-table-model' mode, switch to 'table-models' mode
      if (this.mode !== 'automated-table-model') {
        this.$store.dispatch('dataView/setMode', 'table-models')
      }
    },
    addColumns(count) {
      // Emit an event to add columns to the table
      bus.$emit('dataView/addColumns', count)
    },
    addTableNormalizerItems(count) {
      // Emit an event to add normalizer items to the table
      bus.$emit('dataView/addTableNormalizerItems', count)
    },

    async saveKeys() {
      this.validatingKeys = true // Begin the key validation process

      // Validate the key items in the form
      const keyItemsIsValid = await this.validateForm('validateKeyItems')
      if (!keyItemsIsValid) {
        // Switch to 'key-items' mode if validation fails
        if (this.mode !== 'key-items') {
          this.$store.dispatch('dataView/setMode', 'key-items')
        }
        this.displayInvalidFormError() // Display an error message
        this.validatingKeys = false
        return
      }

      // If in 'key-rules' mode, validate the key rules
      if (this.mode === 'key-rules') {
        const keyRulesIsValid = await this.validateForm('validateKeyRules')
        if (!keyRulesIsValid) {
          this.displayInvalidFormError() // Display an error message
          this.validatingKeys = false
          return
        }
      }

      this.validatingKeys = false // End the validation process

      // Save the validated keys data
      this.saveKeysData()
    },
    validateForm(eventName) {
      // Return a promise that resolves when the form validation emits its result
      return new Promise(resolve => {
        bus.$emit(eventName, isValid => {
          resolve(isValid)
        })
      })
    },
    async saveKeysData() {
      this.savingKeys = true // Start the process of saving keys

      // Save specific key data based on the current mode
      if (this.mode === 'key-rules') {
        await this.$store.dispatch('dataView/saveKeyRuleItem')
      }
      if (this.mode === 'key-lookup') {
        this.$store.dispatch('dataView/saveKeyLookupItem')
      }

      // Prepare the payload to send to the server
      let url
      let payload
      // IMPORTANT: Clone the key object to avoid directly mutating Vuex state
      const key = cloneDeep(this.$store.getters['dataView/key'])

      // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
      // Get prompt keys from key.items - this represents the complete current state
      // including any additions, edits, or deletions made by the user
      // const promptKeys = key.items.filter(item => item.type === 'prompt')

      // Filter out auto keys only (keep everything else including prompt keys in definition now)
      const definitionKeys = key.items.filter(item => item.type !== 'auto')

      // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
      // Save prompt keys separately via updatePromptKeys API (always call, even with empty array)
      // Note: We don't manually update the profile store here because we'll fetch fresh data
      // from the API after saving (via getPromptKeys call below)
      // try {
      //   // Transform prompt keys to match backend expected structure
      //   const transformedPromptKeys = promptKeys.map(item => ({
      //     type: 'prompt',
      //     label: item.keyLabel,
      //     keyValue: item.keyLabel,
      //     prompt: item.prompt || {},
      //   }))
      //   await this.$store.dispatch('profile/updatePromptKeys', transformedPromptKeys)
      // } catch (error) {
      //   // Handle duplicate key error
      //   if (error.response?.data?.duplicates) {
      //     const { duplicates } = error.response.data
      //     const duplicateKeyNames = duplicates.map(dup => dup.key_value).join(', ')

      //     // Show error toast
      //     this.$toast({
      //       component: ToastificationContent,
      //       props: {
      //         title: 'Duplicate Prompt Keys Found',
      //         text: `The following keys are duplicated: ${duplicateKeyNames}. Please remove duplicates and try again.`,
      //         icon: 'AlertTriangleIcon',
      //         variant: 'danger',
      //       },
      //     })

      //     // Highlight duplicate keys in the UI
      //     this.$store.commit('dataView/SET_DUPLICATE_PROMPT_KEYS', duplicates)

      //     // Stop loading and return early
      //     this.savingKeys = false
      //     return
      //   }

      //   // Handle other errors
      //   const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Error saving prompt keys'
      //   this.$toast({
      //     component: ToastificationContent,
      //     props: {
      //       title: 'Error Saving Prompt Keys',
      //       text: errorMessage,
      //       icon: 'AlertTriangleIcon',
      //       variant: 'danger',
      //     },
      //   })
      //   this.savingKeys = false
      //   return
      // }

      // Update key.items to only include definition keys (not auto)
      // This is safe now because we're working with a cloned object
      key.items = definitionKeys
      // If the full cell label feature is disabled, reset the sheet name in key items
      if (!this.showSheetName || !this.showSheetNumber || this.isCaptureByFirstSheet) {
        key.items.forEach(item => {
          if (item.typeData && item?.typeData?.cellRangeItems) {
            item.typeData.cellRangeItems.forEach(cellRangeItem => {
              if (!this.showSheetName || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                cellRangeItem.sheetName = '' // Reset sheet name
              }
              if (!this.showSheetNumber || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                cellRangeItem.sheetNumber = null
              }
            })
          }
          // Additional reset for `excelRegexExtractor` structure
          if (item.excelRegexExtractor?.cellRanges) {
            item.excelRegexExtractor.cellRanges.forEach(cellRange => {
              if (!this.showSheetName || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                cellRange.sheetName = ''
              }
              if (!this.showSheetNumber || this.isCaptureByFirstSheet) {
                // eslint-disable-next-line no-param-reassign
                cellRange.sheetNumber = ''
              }
            })
          }
        })
      }
      key.cell_range_permission = this.cellRangePermission

      // Get batch information from the store to determine the correct API endpoint
      const batch = this.$store.getters['batch/batch']
      if (this.currentRouteName === 'template-batch') {
        // Use the template batch endpoint
        url = 'dashboard/update_template_definition_by_version/'
        payload = {
          template_name: batch?.definitionId || '',
          definition_version: this.$store.getters['dataView/selectedDefinitionVersion'],
          key,
        }
      } else {
        // Use the default endpoint
        url = '/update_definition_by_version/'
        payload = {
          layout_id: this.raJsonDocumentData.pages[0]?.layout_id || this.selectedDocument.layoutId,
          definition_id: this.selectedDefinition.definition_id || batch?.definitionId,
          vendor: this.selectedDocument.vendor,
          definition_version: this.$store.getters['dataView/selectedDefinitionVersion'],
          key,
        }
      }
      if (!this.raJsonDocumentData.pages[0]?.layout_id) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'No LayoutId Available',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        this.savingKeys = false
      } else {
        try {
          const res = await axios.post(url, payload)

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Definition updated successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
          // Clear duplicate highlights on successful save
          // this.$store.commit('dataView/SET_DUPLICATE_PROMPT_KEYS', [])
          this.$store.dispatch('dataView/setSelectedDefinition', res.data)
        } catch (error) {
          if (error.response && error.response.status === 404) {
            try {
              const definitionVersion = this.$store.getters['dataView/selectedDefinitionVersion']
              const allTables = cloneDeep(this.$store.getters['dataView/table'])
              const allKeys = cloneDeep(this.$store.getters['dataView/key'])

              const filteredKeys = env => {
                if (definitionVersion === env) return allKeys
                return {
                  models: [],
                  items: [],
                  ruleItems: [],
                  sampleBlocks: [],
                  notInUseItems: [],
                  lookupItems: [],
                  cell_range_permission: '',
                }
              }

              const fallbackPayload = {
                vendor: this.selectedDocument.vendor,
                definition_id: this.selectedDefinition?.definition_id || batch?.definitionId,
                layout_id: this.raJsonDocumentData.pages[0]?.layout_id || this.selectedDocument.layoutId,
                data: {
                  uat: { key: filteredKeys('uat'), table: allTables },
                  prod: { key: filteredKeys('prod'), table: allTables },
                  draft: { key: filteredKeys('draft'), table: allTables },
                },
              }

              const response = await axios.post('/definitions/', fallbackPayload)
              if (response) {
                this.$toast({
                  component: ToastificationContent,
                  props: {
                    title: 'Definition Added Successfully.',
                    icon: 'InfoIcon',
                    variant: 'info',
                  },
                })
                await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
              }
            } catch (fallbackErr) {
              const fallbackMsg = fallbackErr?.response?.data?.detail || 'Unable to Add Definition'
              this.$toast({
                component: ToastificationContent,
                props: {
                  title: fallbackMsg,
                  icon: 'AlertTriangleIcon',
                  variant: 'danger',
                },
              })
            }
          } else {
            const message = error?.response?.data?.detail || 'Something went wrong'
            this.$toast({
              component: ToastificationContent,
              props: {
                title: message,
                icon: 'AlertTriangleIcon',
                variant: 'danger',
              },
            })
          }
        } finally {
          this.savingKeys = false
        }
      }
    },
    addKeys(count) {
      // Emit an event to add a specified number of keys
      // Pass the current mode so components know which array to update
      bus.$emit('dataView/addKeys', { count, mode: this.mode })
    },
    addKeyModel() {
      // Emit an event to add a single key model
      bus.$emit('dataView/addKeyModels', 1)
    },
    testModels() {
      // Trigger the testing of models
      this.submittingModelsTestRequst = true // Indicate that a model test request is being submitted

      // Get batch and definition details from the store
      const batch = this.$store.getters['batch/batch']
      const definition = this.$store.getters['dataView/selectedDefinition']
      const selectedDocumentId = this.$store.getters['batch/selectedDocumentId']

      // Send a request to test the models
      axios.post('/pipeline/test_models/', {
        batch_id: batch.id,
        definition,
      })
        .then(res => {
          // Check if table boundaries were found in the response
          const tableBoundaryFound = res.data.data[selectedDocumentId]?.table_boundary_found
          if (tableBoundaryFound) {
            // Display success toast notification
            this.$toast({
              component: ToastificationContent,
              props: {
                title: 'Table Boundary Found',
                icon: 'CheckIcon',
                variant: 'success',
              },
            })
          } else {
            // Display failure toast notification
            this.$toast({
              component: ToastificationContent,
              props: {
                title: 'Table Boundary Not Found',
                icon: 'AlertTriangleIcon',
                variant: 'danger',
              },
            })
          }
          this.submittingModelsTestRequst = false // Reset submission state
        })
        .catch(error => {
          // Handle errors and display a toast notification
          const message = error?.response?.data?.detail || 'Error running model test'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.submittingModelsTestRequst = false // Reset submission state
        })
    },
    closeKeyRules() {
      // Switch the mode to 'key-rule-items'
      this.$store.dispatch('dataView/setMode', 'key-rule-items')
    },
    closeKeyLookups() {
      // Switch the mode to 'key-lookup-items'
      this.$store.dispatch('dataView/setMode', 'key-lookup-items')
    },
    closeTableLookups() {
      // Switch the mode to 'table-lookup-items'
      this.$store.dispatch('dataView/setMode', 'table-lookup-items')
    },
    closeTableRules() {
      // Switch the mode to 'table-rule-items'
      this.$store.dispatch('dataView/setMode', 'table-rule-items')
    },
    switchToKeyView() {
      // Set the current view to 'key'
      this.$store.commit('batch/SET_VIEW', 'key')
    },
    addKeyRules(count) {
      // Emit an event to add a specified number of key rules
      bus.$emit('dataView/addKeyRules', count)
    },
    addQueries(count) {
      // Emit an event to add a specified number of queries
      bus.$emit('dataView/addQueries', count)
    },
    addTableRules(count) {
      // Emit an event to add a specified number of table rules
      bus.$emit('dataView/addTableRules', count)
    },
    activeAddRow() {
      // Toggle the add row functionality in the store
      this.$store.commit('batch/TOGGLE_ADD_ROW', !this.isAddRow)
    },
    activeDeleteRow() {
      // Toggle the delete row functionality in the store
      this.$store.commit('batch/TOGGLE_DELETE_ROW', !this.isDeleteRow)
    },
    confirmRowDelete() {
      // Emit an event to confirm row deletion
      bus.$emit('dataView/confirmRowDelete')
    },
    cancleRowDelete() {
      // Emit an event to cancel row deletion
      bus.$emit('dataView/cancleRowDelete')
    },
    toggleRowDeleteOption(val) {
      // Toggle the visibility of the row delete option
      this.isRowDeleteOption = val
    },
    selectOption(value) {
      // Handle different actions based on the selected option
      if (value === 'rules') {
        // Set a table rule item and switch to 'table-rules' mode
        this.$store.dispatch('dataView/setTableRuleItem', {
          label: this.label,
        })
        this.$store.dispatch('dataView/setMode', 'table-rules')
      }
    },
  },
}
</script>

<style scoped>
.btn {
  padding: 0.75rem !important;
  font-size: 12px;
}
.definitions-toolbar {
    column-gap: 1rem;
}
.verification-toolbar-wrapper {
    column-gap: 1rem;
}
.document-selector-wrapper {
  width: 250px;
}
.table-selector-wrapper {
  width: 220px;
}
.add-table {
  width: 280px;
}
.add-columns {
  width: 180px;
  display: inline-block;
}
.add-keys {
  width: 180px;
  display: inline-block;
}
.add-table-responsive {
  width: 230px;
}

@media (max-width: 1080px) {
  .add-table-responsive {
    width: 300px;
  }
}

@media (max-width: 992px) {
  .add-table-responsive {
    width: 330px;
  }
}

.b-dropdown .b-form-radio-group {
  margin: 0;
  padding: 10px;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style lang="scss" scoped>
.pb_1px {
  margin-bottom: 1px;
}
</style>
