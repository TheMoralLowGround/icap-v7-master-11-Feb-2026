<!--
  Organization: AIDocbuilder Inc.
  File: TrainBatches.vue
  Version: 6.0

  Authors:
    - Vinay - Initial implementation
    - Ali - Code optimization

  Last Updated By: Ali
  Last Updated At: 2024-12-02

  Description:
    This component renders a dynamic, interactive table using BootstrapVue's `<b-table-simple>` component. It displays data rows based on a selected table, allowing for user interactions such as row selection, editing, and configuring columns. The table is responsive, and each row can be edited in-place when in 'verification' mode. It includes custom interactions for adding, updating, or deleting rows. The table headers are configurable and display options for column settings if not in 'verification' mode.

  Key Features:
    - Conditional rendering based on the presence of data (`items` and `table`).
    - Allows column configuration through the `<TableColumnConfig>` component.
    - Supports in-place editing of cells in 'verification' mode.
    - Handles dynamic row actions with custom hover and click behaviors.
    - Dynamically adjusts table columns based on field usage and sorting preferences.

  Dependencies:
    - BootstrapVue (`b-table-simple`, `b-th`, `b-tr`, `b-td`, `b-button-group`, `b-button`).
    - Custom components: `FormInput`, `TableColumnConfig`.
    - Lodash (`cloneDeep`).

  Stores and Getters Used:
    - Vuex: `dataView`, `batch`.

  Notes:
    - Handles the 'verification' mode for cell editing and validation.
    - Filters out empty rows before rendering.
    - Customizes cell styling and interaction based on the table data and mode.

-->

<template>
  <div>
    <b-table-simple
      v-if="table && items && items.length"
      hover
      striped
      :sticky-header="topPaneSize"
      class="test-result-table"
    >
      <b-thead>
        <b-tr>
          <b-th
            v-for="(tableField, indexField) of tableFields"
            :key="indexField+'field'"
            :class="{
              'bg-success text-white': tableField.is_profile_key_found && tableField.status !== -2 && !tableField.is_column_mapped_to_key,
              'custom-danger': tableField.status === -2,
              'bg-info text-white': tableField.is_column_mapped_to_key && tableField.status !== -2

            }"
          >
            <!-- <span class="table-column-config"> -->
            <table-column-config
              v-if="mainMode !== 'verification'"
              class="table-column-config"
              :label="tableField.label"
              :is-column-mapped-to-key="tableField.is_column_mapped_to_key"
              :table-fields="tableFields"
            >
              <span
                class="text-bold w-full"
                :class=" tableField.is_profile_key_found || tableField.status === -2 || tableField.is_column_mapped_to_key ? 'text-white': 'text-secondary' "
              >{{ tableField.label.toUpperCase() }}
              </span>
            </table-column-config>
            <span
              v-else
              class="table-column-config"
            >
              <span
                class="text-bold w-full"
                :class=" tableField.is_profile_key_found || tableField.status === -2 || tableField.is_column_mapped_to_key ? 'text-white': 'text-secondary' "
              >{{ tableField.label.toUpperCase() }}
              </span>
            </span>
            <!-- </span> -->
          </b-th>
        </b-tr>
      </b-thead>
      <b-tbody>
        <b-tr
          v-for="(item, itemIndex) of items"
          :key="itemIndex"
          :class="[{'hover-background-add': isAddRow}, {'hover-background-delete': isDeleteRow}, {'selected-background-delete': selectedIndexForDelete === itemIndex}]"
          @click="rowAction(itemIndex)"
        >
          <template v-for="(tableField, indexed) of tableFields">
            <b-td
              v-if="item[tableField.label] && item[tableField.label] !== undefined && item[tableField.label].v"
              :key="indexed + 'row-with-value'"
              :class="[
                customVariantClass(item[tableField.label]),
                customHoverClass(item[tableField.label])
              ]"
              @click="onCellClick(item[tableField.label])"
              @dblclick="onCellDbClick(item[tableField.label])"
            >
              <div
                :class="{
                  'highlight-node': mainMode === 'verification' && editableNode && item[tableField.label] && item[tableField.label].id === editableNode.id
                }"
              >
                <span v-if="item[tableField.label] && item[tableField.label].v">
                  <!-- Display the first value if it's an array -->
                  {{ Array.isArray(item[tableField.label].v) ? item[tableField.label].v[0] : item[tableField.label].v }}
                </span>

                <!-- Show "See More" button if the value is an array with more than one element -->
                <button
                  v-if="Array.isArray(item[tableField.label].v) && item[tableField.label].v.length > 1"
                  class="btn btn-link p-0 m-0 text-decoration-none"
                  @click="openModal(item[tableField.label].v, tableField.label)"
                >
                  See More
                </button>
              </div>
            </b-td>
            <b-td
              v-else
              :key="indexed + 'row-without-value'"
            >
              <div
                v-if="mainMode === 'verification'"
                class="d-flex"
              >
                <template v-if="itemIndexG === itemIndex && fieldIndex === indexed">
                  <form-input
                    id="cell-field"
                    ref="AddRowInput"
                    :class="{'highlight-node':foucued}"
                    style="max-width: 300px;"
                    type="text"
                    :value="newCell.text"
                    :placeholder="title"
                    @input="onInput"
                    @selection-input="onSelectionInput"
                    @focus="foucued=true"
                  />
                  <b-button-group
                    v-if="newCell.pos"
                    size="sm"
                    style="padding: 4px;"
                  >
                    <b-button
                      variant="outline-primary"
                      @click="saveCell(item, tableField.label, itemIndex)"
                    >
                      <feather-icon
                        icon="CheckIcon"
                        size="16"
                      />
                    </b-button>
                    <b-button
                      variant="outline-secondary"
                      @click="closeCell"
                    >
                      <feather-icon
                        icon="XIcon"
                        size="16"
                      />
                    </b-button>
                  </b-button-group>
                </template>
                <p
                  v-else
                  class="text-danger flex-grow-1"
                  @click="showAddField(itemIndex, indexed)"
                >NULL
                </p>
              </div>
            </b-td>
          </template>
        </b-tr>
      </b-tbody>
    </b-table-simple>
    <!-- Modal to display the rest of the values -->
    <b-modal
      ref="arrayValuesModal"
      centered
      :title="modalTitle"
    >
      <div style="max-height: 300px; overflow-y: auto; white-space: pre-wrap;">
        <ul>
          <li
            v-for="(value, index) in modalValues"
            :key="index"
          >
            {{ value }}
          </li>
        </ul>
      </div>
    </b-modal>
  </div>
</template>
<script>
import bus from '@/bus'
import {
  BTableSimple, BThead, BTbody, BTh, BTr, BTd, BButtonGroup, BButton, BModal,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'

import FormInput from '@/components/UI/FormInput.vue'
import TableColumnConfig from './TableColumnConfig.vue'

const defaultValue = {
  text: null,
  pos: null,
  pageIndex: null,
  documentIndex: null,
  threshold: null,
}

export default {
  components: {
    BTableSimple,
    BThead,
    BTbody,
    BTh,
    BTr,
    BTd,
    TableColumnConfig,
    FormInput,
    BButtonGroup,
    BButton,
    BModal,
  },
  data() {
    return {
      newCell: {
        text: '',
      },
      title: '',
      trigger: 0,
      foucued: false,
      itemIndexG: -1,
      fieldIndex: '',
      selectedIndexForDelete: -1,
      modalValues: [], // To store the array values for the modal
      modalTitle: '',
    }
  },
  computed: {
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    tables() {
      // eslint-disable-next-line no-unused-expressions
      this.trigger
      return this.$store.getters['batch/selectedDocument']?.tables || []
    },

    displayNotInUseFields() {
      return this.$store.getters['dataView/displayNotInUseFields']
    },
    selectedTableId() {
      return this.$store.getters['dataView/selectedTableId']
    },
    selectedTableName() {
      return this.$store.getters['dataView/selectedTableName']
    },
    table() {
      // Find document table that matches the selected table name
      // Only show data if there's a matching document table with extracted data
      if (this.selectedTableName) {
        const match = this.tables.find(
          i => i.table_name === this.selectedTableName,
        )
        if (match) return match
      }

      // No matching document table found - return null (no data to show)
      return null
    },

    items() {
      const { table } = this
      const tableFields = this.tableFields || []

      let items = table?.rows || []
      items = items.filter(item => {
        let hasValueInVisibleColumns = false

        // Check if the item has values in any of the visible table fields
        for (let index = 0; index < tableFields.length; index += 1) {
          const fieldName = tableFields[index]?.label || tableFields[index]
          if (item[fieldName]
          && item[fieldName] !== undefined
          && item[fieldName].v !== undefined
          && item[fieldName].v !== null
          && item[fieldName].v !== '') {
            hasValueInVisibleColumns = true
            break
          }
        }

        return hasValueInVisibleColumns
      })

      this.$store.commit('batch/CHECK_DELETE_ROW', items.length > 1)

      return items
    },

    definitionTableColumns() {
      const tableColumns = this.$store.getters['dataView/tableColumns']

      if (!tableColumns) { return [] }
      return tableColumns
    },

    tableFields() {
      if (!this.table) return []

      // Collect all unique column keys
      let keys = []
      this.table.rows.forEach(item => {
        keys = keys.concat(Object.keys(item))
      })
      keys = [...new Set(keys)]

      // No filtering here - we'll filter after computing colors
      // if (!this.displayNotInUseFields) {
      //   keys = keys.filter(key => this.isInUse(key))
      // }

      // Build map of column definitions for quick lookup
      const columnMap = {}
      this.definitionTableColumns.forEach(col => {
        if (col && col.colLabel) {
          columnMap[col.colLabel] = col
        }
      })

      // Sort keys based on definition order
      const sortedKeys = []
      this.definitionTableColumns.forEach(definitionTableColumn => {
        const colLabel = definitionTableColumn?.colLabel
        if (colLabel && keys.includes(colLabel) && !sortedKeys.includes(colLabel)) {
          sortedKeys.push(colLabel)
        }
      })

      if (this.mainMode === 'verification') {
        keys.forEach(key => {
          if (!sortedKeys.includes(key) && this.isInUse(key)) {
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

      // Initialize maps for status, is_profile_key_found, and is_column_mapped_to_key
      const statusMap = {}
      const profileKeyFoundMap = {}
      const isLabelMappedMap = {}
      const originalKeyMap = {}
      const columnMappedToKeyMap = {}
      sortedKeys.forEach(key => {
        statusMap[key] = columnMap[key]?.status || 0 // Default to column definition status or 0
        profileKeyFoundMap[key] = false // Default to false
        isLabelMappedMap[key] = false // Default to false
        originalKeyMap[key] = null // Default to null
        columnMappedToKeyMap[key] = false // Default to false
      })

      // Iterate through rows to determine status, is_profile_key_found, isLabelMapped, and originalKey
      this.table.rows.forEach(row => {
        sortedKeys.forEach(key => {
          if (
            row[key]
        && row[key] !== undefined
        && row[key].v !== undefined
        && row[key].v !== null
        && row[key].v !== ''
          ) {
            // Set is_profile_key_found if not already true
            if (profileKeyFoundMap[key] === false && row[key].is_profile_key_found !== undefined) {
              profileKeyFoundMap[key] = row[key].is_profile_key_found
            }
            // Set isLabelMapped if not already true
            if (isLabelMappedMap[key] === false && row[key].is_label_mapped !== undefined) {
              isLabelMappedMap[key] = row[key].is_label_mapped
            }
            // Set originalKey if not already set
            if (originalKeyMap[key] === null && row[key].original_key_label !== undefined) {
              originalKeyMap[key] = row[key].original_key_label
            }
            // Set is_column_mapped_to_key if not already true
            if (columnMappedToKeyMap[key] === false && row[key].is_column_mapped_to_key !== undefined) {
              columnMappedToKeyMap[key] = row[key].is_column_mapped_to_key
            }
            // Update status if STATUS is -2 (takes precedence)
            if (row[key].STATUS === -2) {
              statusMap[key] = -2
            }
          }
        })
      })

      // Create array of header objects
      const tableFieldsArray = sortedKeys.map(key => ({
        label: key,
        status: statusMap[key],
        is_profile_key_found: profileKeyFoundMap[key],
        isLabelMapped: isLabelMappedMap[key],
        originalKey: originalKeyMap[key],
        is_column_mapped_to_key: columnMappedToKeyMap[key],
      }))

      // Filter based on displayNotInUseFields
      if (!this.displayNotInUseFields) {
        // Only show columns with green (is_profile_key_found === true), red (status === -2), or info (is_column_mapped_to_key === true) background
        return tableFieldsArray.filter(field => field.is_profile_key_found === true || field.status === -2 || field.is_column_mapped_to_key === true)
      }

      return tableFieldsArray
    },

    // optimize version
    // tableFields() {
    //   if (!this.table) return []

    //   const rows = this.table.rows || []
    //   const displayNotInUse = this.displayNotInUseFields
    //   const definitionCols = this.definitionTableColumns || []
    //   const isVerification = this.mainMode === 'verification'

    //   //  Collect unique keys efficiently
    //   const keySet = new Set()
    //   rows.forEach(row => {
    //     Object.keys(row).forEach(key => keySet.add(key))
    //   })

    //   //  Filter if needed
    //   let keys = Array.from(keySet)
    //   if (!displayNotInUse) {
    //     keys = keys.filter(k => this.isInUse(k))
    //   }

    //   //  Map definitions
    //   const columnMap = {}
    //   definitionCols.forEach(col => {
    //     if (col && col.colLabel) columnMap[col.colLabel] = col
    //   })

    //   //  Sort keys by definition order
    //   const sortedKeys = []
    //   const definitionLabels = definitionCols.map(c => c.colLabel)

    //   definitionLabels.forEach(label => {
    //     if (keys.includes(label)) sortedKeys.push(label)
    //   })

    //   keys.filter(key => !sortedKeys.includes(key)
    //   && (isVerification ? this.isInUse(key) : true)).forEach(key => sortedKeys.push(key))

    //   //  Initialize maps
    //   const statusMap = {}
    //   const profileMap = {}
    //   sortedKeys.forEach(key => {
    //     statusMap[key] = columnMap[key]?.status || 0
    //     profileMap[key] = false
    //   })

    //   // Compute values
    //   rows.forEach(row => {
    //     sortedKeys.forEach(key => {
    //       const cell = row[key]
    //       if (cell && cell.v != null && cell.v !== '') {
    //         if (!profileMap[key] && cell.is_profile_key_found !== undefined) {
    //           profileMap[key] = cell.is_profile_key_found
    //         }
    //         if (cell.STATUS === -2) {
    //           statusMap[key] = -2
    //         }
    //       }
    //     })
    //   })

    //   // 7 Return final data
    //   return sortedKeys.map(k => ({
    //     label: k,
    //     status: statusMap[k],
    //     is_profile_key_found: profileMap[k],
    //   }))
    // },
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    editableNode() {
      return this.$store.getters['batch/editableNode']
    },
    manualValidation() {
      return this.$store.getters['batch/manualValidation']
    },
    verificationStatus() {
      return this.$store.getters['batch/verificationStatus']
    },
    isAddRow() {
      return this.$store.getters['batch/getIsAddRow']
    },
    isDeleteRow() {
      return this.$store.getters['batch/getIsDeleteRow']
    },
    topPaneSize() {
      const totalHeight = window.innerHeight || 800
      const header = document.querySelector('.header-navbar')
      const headerHeight = header ? header.offsetHeight : 0
      const availableHeight = totalHeight - headerHeight

      // Parse stored size and ensure it's a valid number
      const storedSize = parseFloat(this.$store.getters['batch/getTopPaneSize']) || 50
      const baseHeight = storedSize - 20

      // Reverse the stored size calculation
      const finalHeight = (availableHeight - 300) - (baseHeight / 100) * availableHeight

      return `${finalHeight}px`
    },
  },
  watch: {
    selectedTableId() {
      this.trigger += 1
    },
    selectedIndexForDelete(value) {
      if (value > -1) {
        bus.$emit('dataView/toggleRowDeleteOption', true)
      } else {
        bus.$emit('dataView/toggleRowDeleteOption', false)
        this.$store.commit('batch/TOGGLE_DELETE_ROW', false)
      }
    },
  },
  created() {
    bus.$on('dataView/confirmRowDelete', this.removeExistingRow)
    bus.$on('dataView/cancleRowDelete', this.cancleRowDelete)
  },
  destroyed() {
    this.resetTopPaneSize()
    bus.$off('dataView/confirmRowDelete', this.removeExistingRow)
    bus.$off('dataView/cancleRowDelete', this.cancleRowDelete)
  },
  methods: {
    resetTopPaneSize() {
      this.$store.commit('batch/SET_TOP_PANESIZE', 50) // Reset to default value
    },
    openModal(arrayValues, tableField) {
      // Set the modal values (excluding the first value since it's already shown)
      this.modalTitle = tableField
      this.modalValues = arrayValues

      // Show the modal
      this.$refs.arrayValuesModal.show()
    },
    async showAddField(index, fieldIndex) {
      this.itemIndexG = index
      this.fieldIndex = fieldIndex
      this.newCell = {
        text: '',
      }
    },
    async onCellClick(cellData) {
      if (this.isExcelBatch) {
        bus.$emit('excelViewer/goToCell', {
          sheetName: cellData.worksheet_name,
          cellRange: cellData.cellRange,
        })
      } else {
        bus.$emit('scrollToPos', {
          pos: cellData.pos,
          pageId: cellData.pageId,
        })
      }
      await this.showAddField(-1, -1)
    },
    async onCellDbClick(cellData) {
      if (this.mainMode !== 'verification' || this.verificationStatus !== 'ready' || !this.manualValidation) {
        return
      }

      if (this.editableNode && this.editableNode.id === cellData.id) {
        await this.$store.dispatch('batch/setEditableNode', null)

        return
      }

      await this.$store.dispatch('batch/setEditableNode', cellData)
    },
    customVariantClass(cellData) {
      if (cellData.STATUS === -2) {
        return 'custom-danger'
      // eslint-disable-next-line no-else-return
      }
      // else if (cellData.STATUS === -1) {
      //   return 'custom-warning'
      // }
      return null
    },
    customHoverClass(cellData) {
      if (cellData.STATUS === -2) {
        return 'hover-danger'
      // eslint-disable-next-line no-else-return
      } else if (cellData.STATUS === -1) {
        return 'hover-warning'
      }
      return null
    },
    onInput(data) {
      if (data) {
        this.newCell.text = data
      } else {
        this.newCell = cloneDeep(defaultValue)
      }
    },
    onSelectionInput(data) {
      this.newCell.pos = `${data.startPos},${data.topPos},${data.endPos},${data.bottomPos}`
    },
    async saveCell(rowItem, selectedLabel, itemIndex) {
      const incrementLastPartOfId = id => {
        const parts = id.split('.')
        const last = parts.length - 1
        parts[last] = (parseInt(parts[last], 10) + 1).toString().padStart(3, '0')
        return parts.join('.')
      }
      let currentRowLastCell
      for (let i = Object.keys(rowItem).length - 1; i >= 0; i -= 1) {
        currentRowLastCell = Object.values(rowItem)[i]
        if (currentRowLastCell !== undefined) {
          break
        }
      }

      if (currentRowLastCell === undefined) {
        return
      }

      const newCell = {
        id: '',
        v: '',
        pos: '',
        label: '',
      }
      newCell.id = incrementLastPartOfId(currentRowLastCell.id)
      newCell.pos = this.newCell.pos
      newCell.v = this.newCell.text
      newCell.label = selectedLabel

      await this.$store.dispatch('batch/addNodeWithValue', newCell)
      await this.$store.dispatch('batch/setEditableNode', newCell)
      this.items[itemIndex][selectedLabel] = newCell
      this.closeCell()
    },
    closeCell() {
      this.newCell = {
        text: '',
        pos: '',
      }
      this.$store.dispatch('batch/setEditableNode', null)
      const inputCell = document.getElementById('cell-field')
      this.itemIndexG = -1
      if (inputCell) {
        document.getElementById('cell-field').autofocus = false
      }
    },
    async insertNewRow(rowIndex) {
      await this.$store.dispatch('batch/setEditableNode', this.items[rowIndex])
      this.items.forEach((item, index) => {
        if (index > rowIndex) {
          Object.keys(item).forEach(key => {
            const parts = item[key]?.id?.split('.')
            if (parts?.length === 6) {
              let secondLast = parseInt(parts[4], 10)
              // eslint-disable-next-line no-restricted-globals
              if (!isNaN(secondLast)) {
                secondLast += 1
                parts[4] = secondLast.toString().padStart(3, '0')
                // eslint-disable-next-line no-param-reassign
                item[key].id = parts.join('.')
              }
            }
          })
        }
      })
      function updateObject(obj) {
        const copyObj = JSON.parse(JSON.stringify(obj))
        Object.keys(copyObj).forEach(key => {
          const idParts = copyObj[key].id.split('.')
          idParts[idParts.length - 2] = (parseInt(idParts[idParts.length - 2], 10) + 1).toString().padStart(3, '0')
          // eslint-disable-next-line no-param-reassign
          copyObj[key].id = idParts.join('.')
          // eslint-disable-next-line no-param-reassign
          copyObj[key].v = ''
          // eslint-disable-next-line no-param-reassign
          copyObj[key].pos = ''
          // eslint-disable-next-line no-param-reassign
        })
        return copyObj
      }
      this.items.splice((rowIndex + 1), 0, updateObject(this.items[rowIndex]))
      await this.$store.dispatch('batch/addRow', this.items[rowIndex][Object.keys(this.items[rowIndex])[0]])
      await this.$store.commit('batch/TOGGLE_ADD_ROW', false)
      this.$store.commit('batch/CHECK_DELETE_ROW', true)
    },
    async removeExistingRow() {
      await this.$store.dispatch('batch/setEditableNode', this.items[this.selectedIndexForDelete])
      if (this.selectedIndexForDelete > -1 && this.isDeleteRow) {
        await this.$store.dispatch('batch/deleteRow', this.items[this.selectedIndexForDelete][Object.keys(this.items[this.selectedIndexForDelete])[0]])
        this.items.splice(this.selectedIndexForDelete, 1)
        await this.$store.commit('batch/TOGGLE_DELETE_ROW', false)
        if (this.items.length > 1) {
          this.$store.commit('batch/CHECK_DELETE_ROW', true)
        } else {
          this.$store.commit('batch/CHECK_DELETE_ROW', false)
        }
        this.selectedIndexForDelete = -1
      }
    },
    cancleRowDelete() {
      this.selectedIndexForDelete = -1
      if (this.items.length > 1) {
        this.$store.commit('batch/CHECK_DELETE_ROW', true)
      } else {
        this.$store.commit('batch/CHECK_DELETE_ROW', false)
      }
    },
    async rowAction(rowIndex) {
      if (this.isAddRow) {
        await this.showAddField(-1, -1)
        await this.insertNewRow(rowIndex)
      }
      if (this.isDeleteRow) {
        await this.showAddField(-1, -1)
        // await this.removeExistingRow(rowIndex)
        this.selectForDelete(rowIndex)
      }
    },
    selectForDelete(rowIndex) {
      this.selectedIndexForDelete = rowIndex
    },
    isInUse(key) {
      return (
        !key.startsWith('None')
        && !key.startsWith('notInUse')
        && !key.endsWith('_1')
        && !key.endsWith('_2')
        && !key.toLowerCase().startsWith('temp')
        && !key.toLowerCase().endsWith('temp')
      )
    },
  },
}
</script>
<!-- worksheet_name -->
<style scoped lang="scss">
.test-result-table {

    ::v-deep th, ::v-deep td {
        padding: 0.5rem;
    }
}
.b-table-sticky-header {
  overflow-y: visible;
}
.table-column-config {
  text-transform: none;
   padding: 0.35rem 0.25rem 0.25rem 0!important;
}
.highlight-node {
  border: 1px solid red;
}
.hover-background-add {
  &:hover {
    background-color: rgba(115, 103, 240, 0.15)
  }
}
.hover-background-delete {
  &:hover {
    background-color: rgba(234, 84, 85, 0.15)
  }
}
.selected-background-delete {
    background-color: rgba(234, 84, 85, 0.15) !important
}
.custom-danger {
  background-color: #f1b0b7 !important; /* color for danger */
  color: #fff !important;           /* text color */
}

.custom-warning {
  background-color: #ffeeba !important; /* color for warning */
  color: #856404 !important;            /* text color */
}
/* Add hover styles */
.hover-danger:hover {
  background-color: #f1b0b7 !important;    /* Slightly darker shade for danger hover */
  color: #fff !important;               /* Text color for hover */
}

.hover-warning:hover {
  background-color: #ffdf9e !important; /* Slightly darker shade for warning hover */
  color: #634200 !important;            /* Text color for hover */
}
</style>
