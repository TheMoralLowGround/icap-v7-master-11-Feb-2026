<!--
 Organization: AIDocbuilder Inc.
 File: KeyNotInUseItems.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component manages a table that displays a list of "key items" that are not currently in use.
   The table provides options to delete items from the list. It supports dynamically adding items to
   the table using an event bus and can scroll to the newly added item.

 Features:
   - Displays a table with columns for `Nested Label`, `Key ID`, and `Actions`.
   - Allows users to delete items from the table with a delete icon.
   - Dynamically adds new items to the table, ensuring smooth scrolling to the newly added item.
   - Utilizes the Vuex store to manage the state of the items list.
   - Custom events using `bus` (an event bus) to trigger item additions.

 Dependencies:
   - `BootstrapVue` for the table layout and `BTable` component.
   - `Feather Icons` for the delete action icon.
   - `bus` (an event bus) for managing global event communication.

 Notes:
   - The `items` list is reactive and managed via Vuex, which allows the component to update automatically when the data changes.
   - The component listens for an `addNotInUseItem` event to dynamically add new items to the list.
   - The table allows for smooth scrolling to newly added items.
-->

<template>
  <div class="h-100">
    <b-table
      ref="table"
      sticky-header="100%"
      :items="items"
      :fields="tableColumns"
      class="h-100 mb-0"
    >
      <template #cell(actions)="data">
        <feather-icon
          v-b-tooltip.hover
          title="Delete Item"
          icon="Trash2Icon"
          class="cursor-pointer mx-auto"
          size="20"
          @click.stop="deleteItem(data.index)"
        />
      </template>
    </b-table>
  </div>
</template>

<script>
import { VBTooltip, BTable } from 'bootstrap-vue'
import bus from '@/bus'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BTable,
  },
  data() {
    return {
      tableColumns: [
        { key: 'nestedLabel', label: 'Nested Label' },
        { key: 'keyId', label: 'Key ID' },
        { key: 'actions', label: 'Actions' },
      ],
    }
  },
  computed: {
    items: {
      get() {
        return this.$store.getters['dataView/keyNotInUseItems']
      },
      set(value) {
        this.$store.commit('dataView/SET_KEY_NOT_IN_USE_ITEMS', value)
      },
    },
  },
  created() {
    bus.$on('addNotInUseItem', this.additem)
  },
  destroyed() {
    bus.$off('addNotInUseItem', this.additem)
  },
  methods: {
    // Adds a new item to the list if it doesn't already exist; scrolls to the added item.
    additem(newItem) {
      let index
      const itemIndex = this.items.findIndex(item => item.nestedLabel === newItem.nestedLabel && item.keyId === newItem.keyId)
      if (itemIndex === -1) {
        this.items.push(newItem)
        index = this.items.length - 1
      } else {
        index = itemIndex
      }
      this.$nextTick(() => {
        this.scrollToIndex(index)
      })
    },
    // Deletes an item from the list at the specified index.
    deleteItem(index) {
      this.items.splice(index, 1)
    },
    // Scrolls the table to bring the newly added or updated item into view.
    scrollToIndex(index) {
      const table = this.$refs.table.$el
      const tbody = table.querySelector('tbody')
      const row = tbody.querySelectorAll('tr')[index]
      const thead = table.querySelector('thead')
      table.scrollTop = row.offsetTop - (thead.offsetHeight + 10)
    },
  },
}
</script>
