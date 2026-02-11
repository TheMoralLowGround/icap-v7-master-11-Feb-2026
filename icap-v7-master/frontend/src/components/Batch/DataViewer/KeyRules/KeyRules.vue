<!--
 Organization: AIDocbuilder Inc.
 File: KeyRulesItems.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component displays a draggable list of key rule items in a table format, allowing users to
   reorder, edit, and delete rule items. The table uses a `draggable` component to handle reordering
   of items and integrates with Vuex for state management.

 Features:
   - Displays a table with columns for `Id`, `Key Id`, and `Actions`.
   - Allows users to drag and reorder the items in the list.
   - Provides edit and delete functionality for each rule item.
   - Uses Vuex to manage the state of the `keyRuleItems` list.
   - Tooltip support for the action icons (Edit and Delete).

 Dependencies:
   - `BootstrapVue` for table layout and other UI components like `BTableSimple`, `BThead`, `BTr`, `BTh`, `BTd`.
   - `Feather Icons` for the action icons.
   - `vuedraggable` for implementing drag-and-drop functionality.

 Notes:
   - The component listens for changes in the `keyRuleItems` from the Vuex store and updates accordingly.
   - The `draggable` component provides a user-friendly interface for reordering the list items.
   - Tooltips provide extra information for each action icon (Edit, Delete).
-->

<template>
  <validation-observer
    ref="keyRulesForm"
    mode="eager"
  >
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

      <draggable
        v-model="items"
        tag="tbody"
        handle=".handle"
        v-bind="dragOptions"
      >
        <rule
          v-for="(item, itemIndex) of items"
          :key="itemIndex"
          v-model="items[itemIndex]"
          :rule-types="ruleTypes"
          :rule-index="itemIndex"
          @deleteItem="deleteItem(itemIndex)"
          @dropdownOpen="scrollToIndex(itemIndex)"
        >
          <template
            v-slot:default="{ rule }"
          >
            <validation-provider
              v-slot="{ errors }"
              name="Value"
              rules="required"
            >
              <b-form-input v-model="rule.value" />
              <b-form-invalid-feedback
                :state="false"
              >
                {{ errors[0] }}
              </b-form-invalid-feedback>
            </validation-provider>
          </template>
        </rule>
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
import { ValidationObserver, extend } from 'vee-validate'

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
    // The `value` prop is an array passed from the parent component
    value: {
      type: Array,
      required: true, // Ensures the parent must provide this prop
    },
  },
  data() {
    return {
      items: [], // Internal state to hold a copy of the `value` array
      dragOptions: {
        animation: 0, // No animation for drag-and-drop
        ghostClass: 'draggable-ghost', // Class applied to the item being dragged
      },
    }
  },
  computed: {
    // Retrieves the default type for key rules from Vuex store
    defaultType() {
      return this.$store.getters['applicationSettings/keyRuleSettings'].defaultType
    },
    // Retrieves all available rule types from Vuex store
    ruleTypes() {
      return this.$store.getters['applicationSettings/keyRuleSettings'].types
    },
    // Creates a deep copy of the `items` array for output
    out() {
      return cloneDeep(this.items)
    },
  },
  watch: {
    // Watches the computed `out` property and emits an event if it changes
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) { // Checks if `out` differs from `value`
          this.$emit('input', val) // Emits the updated value to the parent
        }
      },
      deep: true, // Deep watch for nested object changes
    },
    // Watches the `value` prop for changes and updates internal state
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState() // Synchronizes internal state with `value`
        }
      },
      deep: true, // Deep watch for nested changes
    },
  },
  created() {
    this.setInternalState() // Initializes the internal `items` state with `value`

    // Event listeners for handling external actions
    bus.$on('dataView/addKeyRules', this.addItems) // Adds new items
    bus.$on('validateKeyRules', this.validateKeyRules) // Validates the key rules
    bus.$on('dataView/keyRules/scrollToIndex', this.scrollToIndex) // Scrolls to a specific index

    // Validation rule for the "required" field using Vee-Validate
    extend('required', {
      validate(value) {
        // Ensures the field is not an empty string but allows whitespace
        return value !== ''
      },
      message: 'The Value field is required', // Error message for validation
    })
  },
  destroyed() {
    // Removes event listeners when the component is destroyed
    bus.$off('dataView/addKeyRules', this.addItems)
    bus.$off('validateKeyRules', this.validateKeyRules)
    bus.$off('dataView/keyRules/scrollToIndex', this.scrollToIndex)
  },
  methods: {
    // Synchronizes internal `items` state with the `value` prop
    setInternalState() {
      this.items = cloneDeep(this.value)
    },
    // Adds a specified number of new items to the `items` array
    addItems(count) {
      const lastRowIndex = this.items.length - 1 // Index of the last item in `items`
      const newItems = [] // Array to hold the new items

      for (let i = 0; i < count; i += 1) {
        // Find the default rule type from the Vuex store
        const newRuleType = this.ruleTypes.find(ruleType => ruleType.key === this.defaultType)
        newItems.push({
          type: this.defaultType, // Set the type to the default
          inputs: cloneDeep(newRuleType.defaultValue), // Copy the default inputs
        })
      }

      // Concatenate new items to the existing `items` array
      this.items = this.items.concat(newItems)

      // Scroll to the first newly added item
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },
    // Scrolls to the table row at the specified index
    scrollToIndex(index) {
      const table = this.$refs.table.$el // Reference to the table element
      const tbody = table.querySelector('tbody') // Table body
      const row = tbody.querySelectorAll('tr')[index] // Row at the specified index
      const thead = table.querySelector('thead') // Table header
      table.scrollTop = row.offsetTop - (thead.offsetHeight + 10) // Scroll to the row
    },
    // Deletes an item from the `items` array at the specified index
    deleteItem(index) {
      this.items.splice(index, 1) // Removes the item from the array
    },
    // Validates the key rules form and invokes a callback with the result
    validateKeyRules(callback) {
      this.$refs.keyRulesForm.validate().then(success => {
        callback(success) // Passes the validation result to the callback
      })
    },
  },
}
</script>
