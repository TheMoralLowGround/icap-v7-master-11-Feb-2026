<!--
 Organization: AIDocbuilder Inc.
 File: TableLookupItems.vue
 Version: 6.0

 Authors:
   - Ali - Initial implementation

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component displays a list of key lookup items in a draggable table. Each record has a "Nested Label",
   "Key Id", and actions to edit or delete the lookup item. The component allows users to reorder records
   via drag-and-drop, edit a selected record, or delete a record from the list.

 Features:
   - Displays a table of key lookup items with nested label and key ID.
   - Supports drag-and-drop functionality for reordering the table rows.
   - Includes action buttons to edit and delete individual records.
   - Uses Vuex for managing the state of the records and modifying the list.

 Dependencies:
   - `BootstrapVue` for the table and tooltip components.
   - `vuedraggable` for drag-and-drop functionality.
   - `Feather Icons` for the action icons (Edit, Delete, and Drag Handle).
   - Vuex for storing and modifying the list of key lookup items.

 Notes:
   - The `records` computed property retrieves and updates the key lookup items from the Vuex store.
   - The `dragOptions` computed property defines the configuration for the draggable table (e.g., disabling animation and defining the ghost class).
-->

<template>
  <div class="h-100">
    <b-table-simple
      ref="table"
      class="h-100 mb-0"
      sticky-header="100%"
    >
      <b-thead>
        <b-tr>
          <b-th>Nested Label</b-th>
          <b-th>Actions</b-th>
        </b-tr>
      </b-thead>
      <draggable
        v-model="records"
        tag="tbody"
        handle=".handle"
        v-bind="dragOptions"
      >
        <b-tr
          v-for="(record, recordIndex) of records"
          :key="recordIndex"
        >
          <b-td>{{ record.label }}</b-td>
          <b-td>
            <feather-icon
              icon="AlignJustifyIcon"
              class="cursor-move handle mr-1"
              size="20"
            />

            <feather-icon
              v-b-tooltip.hover
              icon="EditIcon"
              size="20"
              class="mr-1 cursor-pointer"
              title="Edit Lookup"
              @click.stop="editRecord(recordIndex)"
            />

            <feather-icon
              v-b-tooltip.hover
              title="Delete Lookup"
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
} from 'bootstrap-vue'
import draggable from 'vuedraggable'

export default {
  directives: {
    'b-tooltip': VBTooltip,
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
    records: {
      get() {
        return this.$store.getters['dataView/tableLookupItems']
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_LOOKUP_ITEMS', value)
      },
    },
    dragOptions() {
      return {
        animation: 0,
        ghostClass: 'draggable-ghost',
      }
    },
  },
  methods: {
    editRecord(index) {
      this.$store.dispatch('dataView/setTableLookupItemByIndex', index)
      this.$store.dispatch('dataView/setMode', 'table-lookup')
    },
    deleteRecord(index) {
      this.records.splice(index, 1)
    },
  },
}
</script>
