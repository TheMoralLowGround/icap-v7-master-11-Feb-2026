<!--
 Organization: AIDocbuilder Inc.
 File: CopyRules.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component is used to copy rules from an existing rule item (either from a key or table rule)
   into the current set of rules. It presents a modal with a dropdown to select a rule item, and upon
   submission, it appends the selected rule's associated rules to the current rules. The component
   provides support for both key rules and table rules, with validation for rule selection.

 Main Features:
   - Modal dialog for copying rules from a selected rule item
   - Dynamic rule options depending on the mode (key or table rule)
   - Validates and enables the submit button based on selection
   - Appends rules to the current rule set
   - Emits event to scroll to the newly added rule
   - Vuex integration to manage rule data and state

 Dependencies:
   - VueSelect: For the dropdown selection of rule items
   - Bootstrap Vue: For modal and form components
   - Bus: For event communication between components
   - Vuex: For state management of rule items and associated rules

 Notes:
   - This component can be used in both key and table rule modes, switching behavior based on the
     `mode` prop passed from the parent.
-->

<template>
  <!-- Binds modal visibility to `showModal` data property -->
  <b-modal
    v-model="showModal"
    title="Copy Rules"
    @ok="onSubmit"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
      <b-form-group
        label="From rule item:"
      >
        <v-select
          v-model="fromRuleItemIndex"
          transition=""
          :clearable="false"
          :options="ruleItemOptions"
          :reduce="option => option.value"
        />
      </b-form-group>
    </b-card-text>

    <!-- Modal footer with Cancel and Submit buttons -->
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="!enableSubmit"
        @click="ok()"
      >
        Submit
      </b-button>
    </template>
  </b-modal>
</template>

<script>
// Import required components from BootstrapVue and VueSelect
import {
  BButton, BModal, BCardText, BFormGroup,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

import bus from '@/bus'

export default {
  components: {
    BButton,
    BModal,
    BCardText,
    vSelect,
    BFormGroup,
  },
  // mode prop to determine whether it's a key or table rule
  props: {
    mode: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showModal: true, // Controls visibility of the modal
      fromRuleItemIndex: null, // Stores the index of the selected rule item
    }
  },
  computed: {
    // Retrieves selected definition from Vuex store
    definition() {
      return this.$store.getters['dataView/selectedDefinition']
    },
    // Extracts key rule items from the selected definition
    keyRuleItems() {
      return this.definition.key.ruleItems
    },
    // Extracts table rule items
    tableRuleItems() {
      return this.definition.table.flatMap(table => table?.table_definition_data.ruleItems)
    },
    ruleItemOptions() {
      let options = [] // Initializes options array
      let editIndex
      // Retrieves the edit index for key rules from Vuex
      if (this.mode === 'key') {
        editIndex = this.$store.getters['dataView/keyRuleItemEditIndex']

        options = this.keyRuleItems.map(((ruleItem, index) => ({
          value: index,
          label: ruleItem.keyId ? `${ruleItem.id} - ${ruleItem.keyId}` : ruleItem.id,
        })))
      } else {
        editIndex = this.$store.getters['dataView/tableRuleItemEditIndex'] // Retrieves the edit index for table rules from Vuex
        options = this.tableRuleItems.map((ruleItem, index) => ({
          value: index, // Sets index as value
          label: ruleItem.label, // Sets label to rule item label
        }))
      }

      // If there are options and an edit index is found, remove the option at that index
      if (options.length > 0 && editIndex !== -1) {
        options.splice(editIndex, 1) // Removes the rule item at the edit index
      }
      return options // Returns the computed list of rule item options
    },
    enableSubmit() {
      return this.fromRuleItemIndex !== null // Enables the submit button if an option is selected
    },
    keyRuleItemRules: {
      get() {
        return this.$store.getters['dataView/keyRuleItemRules'] // Retrieves key rule item rules from Vuex store
      },
      set(value) {
        this.$store.commit('dataView/SET_KEY_RULE_ITEM_RULES', value) // Commits new value to store
      },
    },
    tableRuleItemRules: {
      get() {
        return this.$store.getters['dataView/tableRuleItemRules'] // Retrieves table rule item rules from Vuex store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_RULE_ITEM_RULES', value) // Commits new value to store
      },
    },
  },
  methods: {
    onSubmit(event) {
      event.preventDefault() // Prevents the default form submission behavior

      if (this.mode === 'key') {
        const lastRowIndex = this.keyRuleItemRules.length - 1 // Gets the last index of the key rule items
        const newRules = this.keyRuleItems[this.fromRuleItemIndex].rules // Gets rules from the selected rule item
        if (newRules.length > 0) {
          this.keyRuleItemRules = this.keyRuleItemRules.concat(newRules) // Adds the new rules to the existing key rules

          this.$nextTick(() => {
            bus.$emit('dataView/keyRules/scrollToIndex', lastRowIndex + 1) // Emits event to scroll to the last added rule
          })
        }
      } else {
        const lastRowIndex = this.tableRuleItemRules.length - 1 // Gets the last index of the table rule items
        const newRules = this.tableRuleItems[this.fromRuleItemIndex].rules // Gets rules from the selected table rule item
        if (newRules.length > 0) {
          this.tableRuleItemRules = this.tableRuleItemRules.concat(newRules) // Adds the new rules to the existing table rules

          this.$nextTick(() => {
            bus.$emit('dataView/tableRules/scrollToIndex', lastRowIndex + 1) // Emits event to scroll to the last added rule
          })
        }
      }

      this.showModal = false // Hides the modal after submission
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss'; // Imports the necessary styles for VueSelect
</style>
