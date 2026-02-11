<!--
 Organization: AIDocbuilder Inc.
 File: QueryItem.vue
 Version: 6.0

 Authors:
   - Ali - Initial implementation

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component represents a single query rule item in the query builder interface. It allows the user to define
   query conditions based on selected columns, operators, and values. The component dynamically updates available
   operators and value options based on the column type and chosen value type (key, input, or query result). It supports
   deleting the rule from the query and reactivity through Vue's two-way data binding.

 Features:
   - Allows dynamic selection of table columns and operators.
   - Supports multiple value types: Key, Input, and Query Result.
   - Reacts to changes in input and updates the parent component accordingly.
   - Provides a delete button to remove the query rule.

 Dependencies:
   - `vSelect`: A Vue Select component used for dropdowns.
   - `BootstrapVue` for the form input and tooltip.
   - `Lodash` for deep cloning and data comparison.
   - Vuex for retrieving document keys for lookup.

 Notes:
   - The available operators are dynamically set based on the column type (`NUMBER`, `VARCHAR2`, etc.).
   - The component relies on Vuex store for document keys when the `key` value type is selected.
-->

<template>
  <div
    class="d-flex align-items-center my-50"
    style="column-gap: 10px;"
  >
    <div style="flex-basis:300px;">
      <v-select
        ref="columnOptions"
        v-model="item.column"
        :options="columnOptions"
        :clearable="false"
        @open="scrollToSelected(columnOptions, item.column)"
      />
    </div>
    <div style="flex-basis:170px;">
      <v-select
        v-model="item.operator"
        :options="operatorOptions"
        :clearable="false"
      />
    </div>
    <div style="flex-basis:500px;">
      <div class="d-flex">
        <div>
          <v-select
            v-model="item.valueType"
            style="width: 160px;"
            :options="valueTypeOptions"
            label="label"
            :reduce="option => option.value"
            :clearable="false"
            @input="onValueTypeInput"
          />
        </div>
        <div class="flex-grow-1">
          <b-form-input
            v-if="item.valueType === 'input'"
            v-model="item.value"
          />
          <v-select
            v-if="item.valueType === 'queryResult'"
            v-model="item.value"
            :options="queryResultOptions"
            :clearable="false"
            label="label"
            :reduce="option => option.value"
          />
          <v-select
            v-if="item.valueType === 'column'"
            ref="tableFields"
            v-model="item.value"
            :options="tableFieldOptions"
            :clearable="false"
            label="label"
            :reduce="option => option.value"
            @open="scrollToSelected(tableFieldOptions, item.value)"
          />
        </div>
      </div>
    </div>
    <div>
      <feather-icon
        v-b-tooltip.hover
        title="Delete Rule"
        icon="Trash2Icon"
        class="cursor-pointer mx-auto"
        size="20"
        @click.stop="$emit('delete')"
      />
    </div>
  </div>
</template>

<script>
import { BFormInput, VBTooltip } from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
    BFormInput,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    tableColumns: {
      type: Array,
      required: true,
    },
    queryResultOptions: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      item: {},
      valueTypeOptions: [
        {
          label: 'Column',
          value: 'column',
        },
        {
          label: 'Input',
          value: 'input',
        },
        {
          label: 'Query Result',
          value: 'queryResult',
        },
      ],
    }
  },
  computed: {
    out() {
      return cloneDeep(this.item)
    },
    columnOptions() {
      return this.tableColumns.map(tableColumn => tableColumn.name)
    },
    operatorOptions() {
      let operators = []

      if (!this.item.column) {
        return operators
      }

      const tableColumn = this.tableColumns.find(tableCol => tableCol.name === this.item.column)
      if (!tableColumn) {
        return operators
      }

      if (['NUMBER'].includes(tableColumn.type)) {
        operators = ['=', '>', '>=', '<', '<=']
      } else if (['VARCHAR2'].includes(tableColumn.type)) {
        operators = ['FUZZY MATCH', '=', 'LIKE', 'ILIKE']
      } else {
        operators = ['FUZZY MATCH', '=', 'LIKE', 'ILIKE']
      }

      return operators
    },
    keyOptions() {
      const keys = this.$store.getters['batch/selectedDocumentKeysForLookup']
      return keys.map(key => ({
        label: key.label,
        value: `<K>${key.label}</K>`,
      }))
    },
    selectedTableName() {
      return this.$store.getters['dataView/selectedTableName']
    },
    displayNotInUseFields() {
      return this.$store.getters['dataView/displayNotInUseFields']
    },
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    tables() {
      return this.$store.getters['batch/selectedDocument']?.tables || []
    },
    table() {
      const definitionTables = this.$store.getters['dataView/table']
      if (!definitionTables.length) return null

      const { table_unique_id } = definitionTables.find(table => table.table_name)
      // eslint-disable-next-line camelcase
      return this.tables.find(table => table.table_unique_id === table_unique_id)
    },
    definitionTableColumns() {
      const tableColumns = this.$store.getters['dataView/tableColumns']
      return tableColumns ? tableColumns.map(column => column.colLabel) : []
    },
    tableFieldsOpt() {
      if (!this.table) return []

      let keys = this.table.rows.flatMap(row => Object.keys(row))
      keys = [...new Set(keys)] // Ensure unique keys

      if (!this.displayNotInUseFields) {
        keys = keys.filter(key => this.isInUse(key))
      }

      const sortedKeys = []
      this.definitionTableColumns.forEach(column => {
        if (keys.includes(column) && !sortedKeys.includes(column)) {
          sortedKeys.push(column)
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

      return sortedKeys
    },
    tableFieldOptions() {
      const tableFields = this.$store.getters['dataView/getTableFields']
      const fields = tableFields.length ? tableFields : this.tableFieldsOpt

      // Map each key in tableFields to an object with `label` and `value`
      return fields.map(field => {
        // Handle both string and object format for backward compatibility
        const fieldLabel = field?.label || field
        return {
          label: fieldLabel, // Use the field name as the label
          value: `<C>${fieldLabel}</C>`, // Wrap the field name with <C> tags for the value
        }
      })
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
  },
  methods: {
    setInternalState() {
      this.item = cloneDeep(this.value)
    },
    onValueTypeInput() {
      this.item.value = null
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected(options, selectedValue) {
      this.$nextTick(() => {
        // Helper function to scroll a dropdown menu to the selected item
        const scrollDropdownToSelected = (dropdownMenu, selectedIndex) => {
          if (dropdownMenu && selectedIndex >= 0) {
            // Calculate scroll position by assuming each item has a uniform height
            const itemHeight = dropdownMenu.scrollHeight / options.length

            // Adjust scrollTop to bring the selected item closer to the top
            const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
            // eslint-disable-next-line no-param-reassign
            dropdownMenu.scrollTop = scrollPosition
          }
        }

        // Get references to dropdown menus
        const columnOptionsItems = this.$refs.columnOptions?.$refs.dropdownMenu
        const tableFieldsItems = this.$refs.tableFields?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options?.indexOf(selectedValue)
        const findSelectedIndex = options?.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(columnOptionsItems, selectedIndex)
        scrollDropdownToSelected(tableFieldsItems, findSelectedIndex)
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
