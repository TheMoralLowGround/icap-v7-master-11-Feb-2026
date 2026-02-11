<!--
 Organization: AIDocbuilder Inc.
 File: TableRuleItems.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-11

 Description:
   This component manages a draggable table of rule items, where each row represents a rule with a label
   and actions for editing or deleting the rule.

 Main Features:
   - Drag-and-drop reordering of table rows
   - Edit and delete functionality for each row
   - Uses Bootstrap Vue components for table layout and styling

 Dependencies:
   - vuedraggable: For drag-and-drop row reordering
   - Bootstrap Vue: For table and UI components
   - Feather Icons: For action icons

 Notes:
   - The table rows are bound to Vuex state, allowing for dynamic updates.
   - The table allows direct interaction for editing and deleting individual items.
-->

<template>
  <!-- Main container for the table, occupying full height -->
  <div class="h-100">
    <!-- Simplified Bootstrap Vue table with sticky headers -->
    <b-table-simple
      ref="table"
      class="h-100 mb-0"
      sticky-header="100%"
    >
      <!-- Table header defining the columns for Label and Actions -->
      <b-thead>
        <b-tr>
          <b-th>Label</b-th>
          <b-th>Actions</b-th>
        </b-tr>
      </b-thead>
      <!-- Draggable component allows rows in the table to be reordered -->
      <draggable
        v-model="records"
        tag="tbody"
        handle=".handle"
        v-bind="dragOptions"
      >
        <!-- Loop through each record in the 'records' array and render a table row -->
        <b-tr
          v-for="(record, recordIndex) of records"
          :key="recordIndex"
        >
          <!-- Display the 'label' property of each record -->
          <b-td>{{ record.label }}</b-td>
          <b-td>
            <!-- Handle icon for drag-and-drop functionality -->
            <feather-icon
              icon="AlignJustifyIcon"
              class="cursor-move handle mr-1"
              size="20"
            />

            <!-- Edit icon: triggers the editRecord method -->
            <feather-icon
              v-b-tooltip.hover
              icon="EditIcon"
              size="20"
              class="mr-1 cursor-pointer"
              title="Edit Rule Item"
              @click.stop="editRecord(recordIndex)"
            />

            <!-- Delete icon: triggers the deleteRecord method -->
            <feather-icon
              v-b-tooltip.hover
              title="Delete Rule Item"
              icon="Trash2Icon"
              class="cursor-pointer mx-auto"
              size="20"
              @click.stop="deleteRecord(recordIndex)"
            />
          </b-td>
        </b-tr>
      </draggable>
    </b-table-simple>
  </div>
</template>

<script>
import {
  VBTooltip, BTableSimple, BThead, BTr, BTh, BTd,
} from 'bootstrap-vue' // Importing Bootstrap Vue components for table layout
import draggable from 'vuedraggable' // Importing draggable for drag-and-drop functionality

export default {
  directives: {
    'b-tooltip': VBTooltip, // Registering the tooltip directive from Bootstrap Vue
  },
  components: {
    BTableSimple,
    BThead,
    BTr,
    BTh,
    draggable,
    BTd,
  },
  computed: {
    // Computed property to bind 'records' to a Vuex getter and setter
    records: {
      get() {
        return this.$store.getters['dataView/tableRuleItems'] // Retrieve the records from the Vuex store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_RULE_ITEMS', value) // Update the records in the Vuex store
      },
    },
    // Options for the draggable component
    dragOptions() {
      return {
        animation: 0,
        ghostClass: 'draggable-ghost', // Class for the item being dragged
      }
    },
  },
  methods: {
    // Triggered when the edit icon is clicked
    editRecord(index) {
      // Dispatch actions to update the selected record and switch to the edit mode
      this.$store.dispatch('dataView/setTableRuleItemByIndex', index)
      this.$store.dispatch('dataView/setMode', 'table-rules')
    },
    // Triggered when the delete icon is clicked
    deleteRecord(index) {
      // Remove the record at the specified index from the 'records' array
      this.records.splice(index, 1)
    },
  },
}
</script>
