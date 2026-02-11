<!--
 Organization: AIDocbuilder Inc.
 File: tableRules.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component represents a dynamic table for managing rules with draggable rows and the ability
   to add, delete, and validate items. Each row contains rule types and their associated inputs.
   The component supports drag-and-drop reordering of rows and updates the parent component through
   a two-way data binding.

 Main Features:
   - Drag-and-drop reordering of rows using `vuedraggable`
   - Adding new rule items with default values
   - Deleting individual rule items
   - Table scrolls to specific rows when required
   - Table rules validation with `vee-validate`
   - Synchronization with the parent component through `v-model`

 Dependencies:
   - vuedraggable: For drag-and-drop row reordering
   - Bootstrap Vue: For table and UI components
   - Feather Icons: For action icons
   - lodash: For deep comparison and cloning
   - vee-validate: For form validation

 Notes:
   - The component listens to events emitted on a bus to add new rules, validate the table, and
     scroll to specific rows.
   - Uses Vuex to retrieve available rule types and default settings.
-->

<template>
  <validation-observer
    ref="tableRulesForm"
    mode="eager"
  >
    <!-- Simplified Bootstrap Vue table with sticky headers -->
    <b-table-simple
      ref="table"
      class="custom-table h-100"
      sticky-header="100%"
    >
      <colgroup>
        <col style="width: 30%">
        <col style="width: 65%">
        <col style="width: 5%">
      </colgroup>

      <!-- Table header defining the columns for Type and Inputs -->
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

      <!-- Draggable component allows rows in the table to be reordered -->
      <draggable
        v-model="items"
        tag="tbody"
        handle=".handle"
        v-bind="dragOptions"
      >
        <!-- Loop through each item in the '' array and render a table row -->
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
} from 'bootstrap-vue'
import draggable from 'vuedraggable'
import { isEqual, cloneDeep } from 'lodash'
import { ValidationObserver } from 'vee-validate'

import bus from '@/bus'
import Rule from '@/components/UI/Rule.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
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
    // The 'value' prop is passed from the parent component, representing the initial list of items
    value: {
      type: Array, // Must be an array
      required: true, // This prop is required
    },
  },
  data() {
    return {
      // Local state to hold the items being displayed and managed in the table
      items: [],
      // Configuration for drag-and-drop behavior
      dragOptions: {
        animation: 0, // No animation during dragging
        ghostClass: 'draggable-ghost', // Class applied to the dragged item
      },
    }
  },
  computed: {
    // Retrieves the default type for rules from the Vuex store
    defaultType() {
      return this.$store.getters['applicationSettings/tableRuleSettings'].defaultType
    },
    // Retrieves the available rule types from the Vuex store
    ruleTypes() {
      return this.$store.getters['applicationSettings/tableRuleSettings'].types
    },
    // Returns a deep clone of the current 'items' array for comparison and updates
    out() {
      return cloneDeep(this.items)
    },
  },
  watch: {
    // Watches the computed 'out' property and emits an 'input' event if it differs from 'value'
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val) // Emits the updated value to the parent component
        }
      },
      deep: true, // Ensures deep watching of nested objects or arrays
    },
    // Watches the 'value' prop for changes and updates the local state accordingly
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState() // Synchronizes the internal state with the updated value
        }
      },
      deep: true, // Ensures deep watching
    },
  },
  created() {
    // Initialize the internal state with the initial value
    this.setInternalState()

    // Register event listeners on the event bus
    bus.$on('dataView/addTableRules', this.addItems) // Adds new rules
    bus.$on('validateTableRules', this.validateTableRules) // Validates table rules
    bus.$on('dataView/tableRules/scrollToIndex', this.scrollToIndex) // Scrolls to a specific row
  },
  destroyed() {
    // Remove event listeners when the component is destroyed
    bus.$off('dataView/addTableRules', this.addItems)
    bus.$off('validateTableRules', this.validateTableRules)
    bus.$off('dataView/tableRules/scrollToIndex', this.scrollToIndex)
  },
  methods: {
    // Synchronizes the local 'items' state with the prop 'value'
    setInternalState() {
      this.items = cloneDeep(this.value)
    },
    // Adds a specified number of new rules to the table
    addItems(count) {
      const lastRowIndex = this.items.length - 1 // Last index before adding new items
      const newItems = []
      for (let i = 0; i < count; i += 1) {
        // Finds the default rule type from available rule types
        const newRuleType = this.ruleTypes.find(ruleType => ruleType.key === this.defaultType)
        // Pushes a new rule with the default type and inputs
        newItems.push({
          type: this.defaultType,
          inputs: cloneDeep(newRuleType.defaultValue),
        })
      }

      // Appends new items to the existing list
      this.items = this.items.concat(newItems)

      // Scroll to the newly added row
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },
    // Scrolls to a specific row in the table
    scrollToIndex(index) {
      const table = this.$refs.table.$el // Access the table element via a reference
      const tbody = table.querySelector('tbody') // Get the table body
      const row = tbody.querySelectorAll('tr')[index] // Get the specified row
      const thead = table.querySelector('thead') // Get the table header
      // Adjust scroll position to make the row visible
      table.scrollTop = row.offsetTop - (thead.offsetHeight + 10)
    },
    // Deletes an item from the 'items' array at the specified index
    deleteItem(index) {
      this.items.splice(index, 1) // Removes the item at the given index
    },
    // Validates the table rules using a validation observer and invokes a callback with the result
    validateTableRules(callback) {
      this.$refs.tableRulesForm.validate().then(success => {
        callback(success) // Passes the validation result to the callback
      })
    },
  },
}
</script>
