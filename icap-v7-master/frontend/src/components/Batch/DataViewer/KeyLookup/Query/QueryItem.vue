<!--
 Organization: AIDocbuilder Inc.
 File: QueryItem.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation

 Last Updated By: Vinay
 Last Updated At: 2023-11-01

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
            v-if="item.valueType === 'key'"
            ref="keyOptions"
            v-model="item.value"
            :options="keyOptions"
            :clearable="false"
            label="label"
            :reduce="option => option.value"
            @open="scrollToSelected(keyOptions, item.value)"
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
          label: 'Key',
          value: 'key',
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
    // Initializes the item state based on the parent component's `value` prop.
    setInternalState() {
      this.item = cloneDeep(this.value)
    },
    // Resets the value when the value type changes to force re-selection of the value.
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
        const keyOptionsItems = this.$refs.keyOptions?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options?.indexOf(selectedValue)
        const findSelectedIndex = options?.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(columnOptionsItems, selectedIndex)
        scrollDropdownToSelected(keyOptionsItems, findSelectedIndex)
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
