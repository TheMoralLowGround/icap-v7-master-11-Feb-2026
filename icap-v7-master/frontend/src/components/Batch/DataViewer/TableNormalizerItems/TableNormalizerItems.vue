<!--
  Organization: AIDocbuilder Inc.
  File: TableNormalizerItems.vue
  Version: 6.0

  Authors:
    - Vinay - Initial implementation
    - Ali - Component development, functionality enhancements, and design

  Last Updated By: Ali
  Last Updated At: 2024-12-27

  Description:
    This component displays a table of normalizer items, where each row can be reordered.
    It supports dynamic addition and deletion of items, drag-and-drop reordering,
    and integrates with form validation. The table tracks the order of items
    and allows scrolling to newly added rows.

  Main Features:
    - Dynamically renders a table with configurable row data.
    - Supports drag-and-drop functionality to reorder table rows.
    - Provides an option to add new rows and delete existing ones.
    - Integrates with `VeeValidate` for form validation.
    - Custom scroll behavior to bring newly added rows into view.

  Dependencies:
    - Bootstrap Vue for UI components.
    - `vuedraggable` for row reordering functionality.
    - Lodash for deep cloning and comparison of data.
    - VeeValidate for form validation.

  Notes:
    - Ensure the parent component provides the correct `value` prop to the component,
      which is an array of items to be rendered.
    - The `tableNormalizerSettings` getter from the store must provide `defaultType`
      and `types` for correct rule type initialization.
-->

<template>
  <!-- The ValidationObserver component ensures the validation state of the form is tracked. -->
  <validation-observer
    ref="tableNormalizerItemsForm"
    mode="eager"
  >
    <!-- The custom table component with sticky headers and a specific class. -->
    <b-table-simple
      ref="table"
      class="custom-table h-100"
      sticky-header="100%"
    >
      <!-- Table column definitions: the first column takes up 30%, the second 65%, and the last 5%. -->
      <colgroup>
        <col style="width: 30%">
        <col style="width: 65%">
        <col style="width: 5%">
      </colgroup>

      <!-- Table header with column titles. -->
      <b-thead>
        <b-tr>
          <b-th>
            Type
          </b-th>
          <b-th>
            Inputs
          </b-th>
          <b-th />
        </b-tr>
      </b-thead>

      <!-- Draggable wrapper that allows the table rows to be reordered. -->
      <draggable
        v-model="items"
        tag="tbody"
        handle=".handle"
        v-bind="dragOptions"
      >
        <!-- Loop through the 'items' array and create a 'Rule' component for each item. -->
        <rule
          v-for="(item, itemIndex) of items"
          :key="itemIndex"
          v-model="items[itemIndex]"
          :rule-types="ruleTypes"
          :rule-index="itemIndex"
          @deleteItem="deleteItem(itemIndex)"
          @dropdownOpen="scrollToIndex(itemIndex)"
        />
      </draggable>
    </b-table-simple>
  </validation-observer>
</template>

<script>
import {
  VBTooltip, BTableSimple, BThead, BTh, BTr,
} from 'bootstrap-vue' // Importing necessary Bootstrap Vue components
import draggable from 'vuedraggable' // Importing draggable for reordering table rows
import { isEqual, cloneDeep } from 'lodash' // Importing lodash methods for deep comparison and cloning
import { ValidationObserver } from 'vee-validate' // Importing VeeValidate's validation observer

import bus from '@/bus' // Importing event bus for custom events
import Rule from '@/components/UI/Rule.vue' // Importing the Rule component

export default {
  directives: {
    'b-tooltip': VBTooltip, // Registering the Bootstrap Vue tooltip directive
  },
  components: {
    BTableSimple,
    Rule,
    draggable,
    BThead,
    BTh,
    BTr,
    ValidationObserver,
  },
  props: {
    value: {
      type: Array,
      required: true, // The parent component passes an array of items as a prop
    },
  },
  data() {
    return {
      items: [], // Local data to hold the list of items
      dragOptions: {
        animation: 0, // Disable animation for the drag and drop
        ghostClass: 'draggable-ghost', // Class for the dragged item
      },
    }
  },
  computed: {
    // Getting the default type and rule types from the store
    defaultType() {
      return this.$store.getters['applicationSettings/tableNormalizerSettings'].defaultType
    },
    ruleTypes() {
      return this.$store.getters['applicationSettings/tableNormalizerSettings'].types
    },
    // Deep clone of items for emitting updates when necessary
    out() {
      return cloneDeep(this.items)
    },
  },
  watch: {
    // Watch for changes in the 'out' computed property and emit updates to the parent
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    // Watch for changes in the 'value' prop and synchronize internal state
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
    // Initialize state and register event listeners when the component is created
    this.setInternalState()
    bus.$on('dataView/addTableNormalizerItems', this.addItems) // Listening for adding new items
    bus.$on('validateTableNormalizerItems', this.validateTableNormalizerItems) // Listening for validation request
  },
  destroyed() {
    // Remove event listeners when the component is destroyed
    bus.$off('dataView/addTableNormalizerItems', this.addItems)
    bus.$off('validateTableNormalizerItems', this.validateTableNormalizerItems)
  },
  methods: {
    // Set the internal state by cloning the 'value' prop
    setInternalState() {
      this.items = cloneDeep(this.value)
    },
    // Add new rows to the table based on the 'count' passed as an argument
    addItems(count) {
      const lastRowIndex = this.items.length - 1
      const newItems = []
      for (let i = 0; i < count; i += 1) {
        const newRuleType = this.ruleTypes.find(ruleType => ruleType.key === this.defaultType)
        newItems.push({
          type: this.defaultType,
          inputs: cloneDeep(newRuleType.defaultValue),
        })
      }

      this.items = this.items.concat(newItems)
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1) // Scroll to the new row after adding
      })
    },
    // Scroll the table to bring the row at the given index into view
    scrollToIndex(index) {
      const table = this.$refs.table.$el
      const tbody = table.querySelector('tbody')
      const row = tbody.querySelectorAll('tr')[index]
      const thead = table.querySelector('thead')
      table.scrollTop = row.offsetTop - (thead.offsetHeight + 10) // Adjust scroll position
    },
    // Remove an item from the 'items' array at the specified index
    deleteItem(index) {
      this.items.splice(index, 1)
    },
    // Trigger validation of the form and invoke the callback with the result
    validateTableNormalizerItems(callback) {
      this.$refs.tableNormalizerItemsForm.validate().then(success => {
        callback(success)
      })
    },
  },
}
</script>
