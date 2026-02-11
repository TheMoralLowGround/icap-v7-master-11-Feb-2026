<!--
 Organization: AIDocbuilder Inc.
 File: TableColumns.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component displays a customizable table where users can reorder, edit, and delete columns
   dynamically. The columns are bound to Vuex for state management, and different types of input fields
   are rendered within each column based on its configuration. It supports drag-and-drop functionality
   for column reordering, tooltips for actions, and dynamic form inputs for each field type (text,
   select, qualifier, and more).

 Features:
   - Displays a table with configurable columns based on the `columnFields` retrieved from Vuex.
   - Supports drag-and-drop reordering of columns using `vuedraggable`.
   - Renders various input types (e.g., text fields, dropdowns, pipe-separated inputs, capture inputs).
   - Allows column deletion with a delete button for each column.
   - Integrates with Vuex for managing the list of columns and field values.
   - Provides tooltips for action buttons (Edit, Delete) using `v-b-tooltip`.

 Dependencies:
   - `BootstrapVue` for table layout and UI components like `BTableSimple`, `BThead`, `BTr`, `BTh`, `BTd`.
   - `Vue Select` for select dropdowns.
   - `vuedraggable` for implementing drag-and-drop functionality.
   - Various custom components like `PipeSeparatedInput`, `FormInput`, `QualifierSelect`, `CaptureTextInput`, and `CellRangeSelector` for specialized input types.
   - `lodash` for deep comparison and cloning of objects.
   - `bus` for event handling between components.

 Notes:
   - The table columns are dynamically generated based on the `columnFields` configuration in Vuex.
   - Supports multiple types of form inputs based on the column type (`text`, `keySelect`, `select`, etc.).
   - The `dragOptions` property configures the drag-and-drop behavior for column reordering.
-->

<template>
  <div class="h-100">
    <b-table-simple
      ref="table"
      sticky-header="100%"
      class="custom-table h-100"
    >
      <colgroup>
        <col
          v-for="(tableColumn) of tableColumns"
          :key="tableColumn.key"
          :style="{ width: tableColumn.width + '%' }"
        >
      </colgroup>

      <b-thead>
        <b-tr>
          <b-th
            v-for="(tableColumn) of tableColumns"
            :key="tableColumn.key"
          >
            <span
              v-b-tooltip.hover
              class="text-capitalize"
              :title="tableColumn.tooltip"
            >
              {{ tableColumn.label }}
            </span>
          </b-th>
          <b-th />
        </b-tr>
      </b-thead>
      <draggable
        v-model="columns"
        tag="tbody"
        handle=".handle"
        v-bind="dragOptions"
      >
        <b-tr
          v-for="(column, columnIndex) of columns"
          :key="columnIndex"
        >
          <b-td
            v-for="(columnField) of columnFields"
            :key="columnField.key"
          >
            <form-input
              v-if="columnField.type === 'text'"
              v-model="columns[columnIndex][columnField.key]"
              type="text"
              :placeholder="columnField.key"
            />
            <v-select
              v-if="columnField.type === 'keySelect'"
              :ref="`vSelect_${columnIndex}`"
              v-model="columns[columnIndex][columnField.key]"
              label="label"
              :options="profileTableKeys"
              :reduce="profileTableKeys => profileTableKeys.keyValue"
              @open="handleDropdownOpen(columnIndex)"
              @input="(e) => onColumnFieldNameChange(e, columnIndex)"
            />

            <v-select
              v-if="columnField.type === 'select'"
              v-model="columns[columnIndex][columnField.key]"
              :label="sortedOptions[columnField.optionsId].lableKey"
              :options="sortedOptions[columnField.optionsId].items"
              :reduce="option => option[sortedOptions[columnField.optionsId].valueKey]"
              @open="onDropdownOpen(columnIndex)"
            />

            <qualifier-select
              v-if="columnField.type === 'qualifierSelect'"
              v-model="columns[columnIndex][columnField.key]"
              :label="columnField.label"
              :key-value="columns[columnIndex][columnField.selectionField]"
              :key-options="keySelectOptions"
              :field-name="columnField.key"
              @dropdownOpen="onDropdownOpen(columnIndex)"
            />

            <pipe-separated-input
              v-if="columnField.type === 'pipeSeparatedInput' && columnField.key === 'shape'"
              v-model="columns[columnIndex][columnField.key]"
              :label="columnField.label"
              selection-value-attr="text"
              listenable-input
              :hide-form-group-label="true"
              @selection-input="shapeSelectionInputHandler(columnIndex,$event)"
              @item-deleted="shapeSelectionItemDeleteHandler(columnIndex, $event)"
            />

            <pipe-separated-input
              v-if="columnField.type === 'pipeSeparatedInput' && columnField.key !== 'shape'"
              v-model="columns[columnIndex][columnField.key]"
              :label="columnField.label"
              :selection-value-attr="columnField.key === 'startPos' ? 'startPos' : columnField.key === 'endPos' ? 'endPos': 'text'"
              listenable-input
              :hide-form-group-label="true"
            />

            <capture-text-input
              v-if="columnField.type === 'captureStartPos'"
              v-model="columns[columnIndex][columnField.key]"
              :label="columnField.label"
              :validation-key="`${columnField.key}_${columnIndex}`"
              type="startPos"
            />

            <capture-text-input
              v-if="columnField.type === 'captureEndPos'"
              v-model="columns[columnIndex][columnField.key]"
              :label="columnField.label"
              :validation-key="`${columnField.key}_${columnIndex}`"
              type="endPos"
            />

            <cell-range-selector
              v-if="columnField.type === 'cellRangeSelectorMultiple'"
              v-model="columns[columnIndex][columnField.key]"
              :label="columnField.label"
              :validation-key="`${columnField.key}_${columnIndex}`"
              :initialize-expanded="false"
              multiple
            />
          </b-td>
          <b-td>
            <div class="action-column-content d-flex">
              <b-dropdown
                right
                variant="link"
                no-caret
                toggle-class="p-0"
                :visible="activeDropdownIndex === columnIndex"
                @hide="resetDropdown"
              >
                <template #button-content>
                  <feather-icon
                    icon="MoreVerticalIcon"
                    size="20"
                    class="align-middle text-body"
                    @click="toggleDropdown(columnIndex)"
                  />
                </template>
                <b-dropdown-form
                  class="advance-settings-dropdown-form"
                >
                  <p class="font-weight-bold">
                    Advanced Settings
                  </p>
                  <template>
                    <b-form-group>
                      <b-form-checkbox
                        v-model="columns[columnIndex].advanceSettings.mergeValue"
                      >
                        Merge Value
                      </b-form-checkbox>
                    </b-form-group>
                    <b-form-group
                      v-if="columns[columnIndex].advanceSettings.mergeValue"
                      label="Merge Value Separator"
                    >
                      <b-form-input
                        v-model="columns[columnIndex].advanceSettings.mergeValueSeparator"
                        @keydown.enter.prevent
                      />
                    </b-form-group>
                  </template>
                </b-dropdown-form>
              </b-dropdown>
              <feather-icon
                icon="AlignJustifyIcon"
                class="cursor-move handle mr-1"
                size="20"
              />
              <feather-icon
                v-b-tooltip.hover
                title="Delete Column"
                icon="Trash2Icon"
                class="cursor-pointer delete-column-btn"
                size="20"
                @click.stop="deleteColumn(columnIndex)"
              />
            </div>
          </b-td>
        </b-tr>
      </draggable>

    </b-table-simple>
  </div>
</template>

<script>
import {
  VBTooltip, BTableSimple, BThead, BTr, BTh, BTd, BFormGroup, BDropdown, BDropdownForm, BFormInput, BFormCheckbox,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'
import draggable from 'vuedraggable'
import PipeSeparatedInput from '@/components/UI/PipeSeparatedInput.vue'
import bus from '@/bus'
import FormInput from '@/components/UI/FormInput.vue'
import QualifierSelect from '@/components/UI/QualifierSelect.vue'
import CaptureTextInput from '@/components/UI/CaptureTextInput/CaptureTextInput.vue'
import CellRangeSelector from '@/components/UI/CellRangeSelector/CellRangeSelector.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
    PipeSeparatedInput,
    FormInput,
    QualifierSelect,
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTd,
    draggable,
    CaptureTextInput,
    CellRangeSelector,
    BFormGroup,
    BDropdown,
    BDropdownForm,
    BFormInput,
    BFormCheckbox,
  },
  props: {
    value: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      columns: [],
      posFields: ['startPos', 'endPos'],
      activeDropdownIndex: null,
    }
  },

  /**
   * Computed Properties:
    * `tableColumns`: Generates the columns array based on the configuration from Vuex.
    * `columnFields`: Filters column fields based on the batch file type (Excel/PDF).
    * `sortedOptions`: Merges options from Vuex to generate sorted options for dropdowns.
    * `keySelectOptions`: Retrieves the applicable key options for table columns.
    * `dragOptions`: Provides options for the `vuedraggable` component (dragging columns).
  */
  computed: {
    optionsKeyItems() {
      return this.$store.getters['definitionSettings/options']['options-keys'].items
    },
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    columnFields() {
      const columnFields = this.$store.getters['applicationSettings/tableSettings'].column.fields
      const batchFileType = this.isExcelBatch ? 'excel' : 'pdf'
      return columnFields.filter(columnField => columnField.applicableFor.includes(batchFileType))
    },
    sortedOptions() {
      return {
        ...this.$store.getters['applicationSettings/options'],
        ...this.$store.getters['definitionSettings/sortedOptions'],
      }
    },
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition']
    },
    keySelectOptions() {
      // Check if the type is 'multishipment'
      if (this.selectedDefinition?.table[0]?.table_definition_data?.models?.type === 'multishipment') {
        // Combine and deduplicate the key options
        const combinedOptions = [
          ...this.$store.getters['definitionSettings/keyOptionsApplicableForTable'],
          ...this.$store.getters['definitionSettings/keyOptionsApplicableForKeys'],
        ]
        // Remove duplicates based on the unique `keyValue`
        const uniqueOptions = Array.from(
          new Map(combinedOptions.map(item => [item.keyValue, item])).values(),
        )

        // Return the combined list of key options
        return uniqueOptions.filter(option => option.type !== 'compound')
      }
      return this.$store.getters['definitionSettings/keyOptionsApplicableForTable']
    },
    profileTableKeys() {
      const keys = this.$store.getters['batch/profileTableKeys']
      return Array.isArray(keys) && keys.length ? keys : []
    },

    out() {
      return cloneDeep(this.columns)
    },
    tableColumns() {
      const columns = this.columnFields.map(columnField => ({
        ...columnField,
        key: columnField.key,
        label: columnField.label,
      }))
      columns.push({
        key: 'actions', label: '',
      })
      return columns
    },
    dragOptions() {
      return {
        animation: 0,
        ghostClass: 'draggable-ghost',
      }
    },
    getProfileDetails() {
      return this.$store.getters['batch/profileDetails']
    },
  },
  watch: {
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
  },

  created() {
    this.setInternalState()
    bus.$on('dataView/addColumns', this.addColumns)
    this.$store.dispatch('batch/fetchProfileTableKeys')
  },
  destroyed() {
    bus.$off('dataView/addColumns', this.addColumns)
  },
  methods: {
    toggleDropdown(index) {
      // Toggle dropdown open/close
      this.activeDropdownIndex = this.activeDropdownIndex === index ? null : index
    },
    resetDropdown() {
      // Reset on close
      this.activeDropdownIndex = null
    },
    // Handles changes to a column's field name
    onColumnFieldNameChange(keyValue, index) {
      // Finds the corresponding option for the keyValue from optionsKeyItems
      const optionsKeyItem = this.profileTableKeys.find(e => e.keyValue === keyValue)

      // Updates the export property of the column at the given index
      this.columns[index].export = optionsKeyItem.export
    },

    // Initializes or resets the internal `columns` state from the `value` prop
    setInternalState() {
      const items = this.value.map(record => {
        const item = {}

        // Maps each column field to the respective value in the record
        this.columnFields.forEach(columnField => {
          const value = record[columnField.key] !== undefined ? record[columnField.key] : (columnField.defaultValue || '')
          item[columnField.key] = value
        })

        // Checks if the record has a column label and matches it with optionsKeyItems
        if (record?.colLabel) {
          const optionsKeyItem = this.optionsKeyItems.find(e => e.keyValue === record.colLabel)

          // Updates the export property if a match is found
          if (optionsKeyItem) {
            item.export = optionsKeyItem.export
          }
        }

        // ✅ Set default advanceSettings if missing
        item.advanceSettings = {
          mergeValue: record.advanceSettings?.mergeValue ?? false,
          mergeValueSeparator: record.advanceSettings?.mergeValueSeparator ?? ',',
        }

        return item
      })

      // Sets the processed items as the columns state
      this.columns = items
    },

    // Adds a specified number of new columns to the `columns` array
    addColumns(count) {
      const lastRowIndex = this.columns.length - 1 // Gets the last row index
      const expandStatus = [] // Placeholder for expand status (not used here)
      const cols = [] // Array to hold the new columns

      for (let i = 0; i < count; i += 1) {
        const col = {}

        // Initializes each column field with its default value or an empty string
        this.columnFields.forEach(columnField => {
          col[columnField.key] = columnField.defaultValue || ''
        })

        // ✅ Add default advanceSettings
        col.advanceSettings = {
          mergeValue: false,
          mergeValueSeparator: ',',
        }

        cols.push(col) // Adds the new column to the array
        expandStatus.push(false) // Adds a default expand status (not used)
      }

      // Concatenates the new columns to the existing `columns` array
      this.columns = this.columns.concat(cols)

      // Scrolls to the first newly added row
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },

    // Scrolls the table to the row at the specified index
    scrollToIndex(index) {
      const table = this.$refs.table.$el // Gets the table element
      const tbody = table.querySelector('tbody') // Selects the table body
      const row = tbody.querySelectorAll('tr')[index] // Gets the row at the given index
      const thead = table.querySelector('thead') // Gets the table header

      // Scrolls the table to make the row visible, accounting for header height
      table.scrollTop = row.offsetTop - (thead.offsetHeight + 10)
    },

    // Deletes a column at the specified index
    deleteColumn(index) {
      this.columns.splice(index, 1) // Removes the column from the array
    },

    // Handles input changes in a shape selection and updates the column data
    shapeSelectionInputHandler(colIndex, data) {
      this.posFields.forEach(posField => {
        let newValue

        // If no specific index is selected, replace the whole field value
        if (data.index === -1) {
          newValue = data.selectionData[posField]
        } else {
          // Updates the specific index within a pipe-separated string
          const currentValue = this.columns[colIndex][posField]
          const newValueArray = currentValue.split('|') // Splits the value into an array
          newValueArray[data.index] = data.selectionData[posField] // Updates the specific index
          newValue = newValueArray.join('|') // Joins the array back into a string
        }

        // Updates the column data with the new value
        this.columns[colIndex][posField] = newValue
      })
    },

    // Handles deletion of a specific item in a shape selection for a column
    shapeSelectionItemDeleteHandler(colIndex, itemIndex) {
      this.posFields.forEach(posField => {
        const currentValue = this.columns[colIndex][posField]
        const newValueArray = currentValue.split('|') // Splits the value into an array
        newValueArray.splice(itemIndex, 1) // Removes the item at the specified index
        const newValue = newValueArray.join('|') // Joins the array back into a string

        // Updates the column data with the new value
        this.columns[colIndex][posField] = newValue
      })
    },

    // Handles actions when a dropdown is opened and ensures the dropdown's visibility
    onDropdownOpen(index) {
      this.$nextTick(() => {
        this.scrollToIndex(index) // Scrolls to the relevant index
      })
    },
    handleDropdownOpen(columnIndex) {
      this.onDropdownOpen(columnIndex)
      this.scrollToSelected(columnIndex)
    },

    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected(columnIndex) {
      this.$nextTick(() => {
        const dropdownMenu = document.querySelector('.vs__dropdown-menu') // Vue Select dropdown
        if (!dropdownMenu) return // Ensure the dropdown exists before proceeding

        const columnField = this.columns[columnIndex] // Get column field dynamically
        const selectedIndex = this.keySelectOptions.findIndex(option => option.keyValue === columnField.colLabel)

        if (selectedIndex >= 0) {
          const itemHeight = dropdownMenu.scrollHeight / this.keySelectOptions.length
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenu.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style lang="scss" scoped>

.action-column-content {
 column-gap: 10px;
}

.advance-settings-dropdown-form {
  width: 250px;

  ::v-deep .form-group:last-child {
    margin-bottom: 0.3rem !important
  }
}
</style>
