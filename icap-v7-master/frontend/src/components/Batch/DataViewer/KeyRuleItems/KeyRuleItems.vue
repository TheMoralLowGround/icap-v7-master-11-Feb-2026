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
  <div class="h-100">
    <b-table-simple
      ref="table"
      class="h-100 mb-0"
      sticky-header="100%"
    >
      <b-thead>
        <b-tr>
          <b-th>Id</b-th>
          <b-th>Key Id</b-th>
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
          <b-td>{{ record.id }}</b-td>
          <b-td>{{ record.keyId }}</b-td>
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
              title="Edit Rule Item"
              @click.stop="editRecord(recordIndex)"
            />

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
    // A computed property that interacts with the Vuex store to get and set the list of key rule items.
    records: {
      get() {
        return this.$store.getters['dataView/keyRuleItems']
      },
      set(value) {
        this.$store.commit('dataView/SET_KEY_RULE_ITEMS', value)
      },
    },
    // Provides options for the `vuedraggable` component, including animation settings and ghost class styling.
    dragOptions() {
      return {
        animation: 0,
        ghostClass: 'draggable-ghost',
      }
    },
  },
  methods: {
    // Dispatches an action to set the selected key rule item and switches the mode to 'key-rules'.
    editRecord(index) {
      this.$store.dispatch('dataView/setKeyRuleItemByIndex', index)
      this.$store.dispatch('dataView/setMode', 'key-rules')
    },
    // Deletes the record at the specified index from the `records` list.
    deleteRecord(index) {
      this.records.splice(index, 1)
    },
  },
}
</script>
