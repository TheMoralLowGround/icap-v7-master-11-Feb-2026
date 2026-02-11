<!--
 Organization: AIDocbuilder Inc.
 File: DefinedKeys.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component manages and displays a list of defined keys in a table format.
   It allows users to view, add, delete, and save defined key entries, with support for dynamic table row management and API interaction.

 Features:
   - Displays a table of defined keys with editable rows for key properties such as label, page index, position, and percentages.
   - Provides functionality to add new empty defined keys, which are appended to the list.
   - Supports deleting defined keys and tracking the deleted keys using the `deletedIds` array.
   - Includes a loading spinner and error handling for data fetching.
   - Allows saving changes to the backend API, with success and error toast notifications.
   - Handles dynamic scrolling to the last added row when new items are added.

 Dependencies:
   - BootstrapVue (for UI components like `b-table-simple`, `b-tr`, `b-td`, etc.)
   - Axios (for making API requests)
   - Vuex (for accessing `definitionId` and loading states)
   - Bus (for handling event-driven interactions across components)
   - Toastification (for displaying success and error notifications)

 Notes:
   - The component listens to custom events (`addDefinedKeys`, `saveDefinedKeys`) via the event bus to handle actions like adding new items and saving the defined keys.
   - Supports sticky headers for the table and implements automatic row scrolling when new items are added.
   - The `fetchDefinedKeys` method is used to fetch the list of defined keys from the backend, and the `save` method is responsible for saving any changes back to the server.
-->

<template>
  <div class="h-100">
    <b-table-simple
      v-if="!loading && !loadingError"
      ref="table"
      class="custom-table h-100"
      sticky-header="100%"
    >
      <colgroup>
        <col style="width: 20%">
        <col style="width: 7%">
        <col style="width: 7%">
        <col style="width: 7%">
        <col style="width: 8%">
        <col style="width: 7%">
        <col style="width: 40%">
        <col style="width: 4%">
      </colgroup>

      <b-thead>
        <b-tr>
          <b-th>Label</b-th>
          <b-th>Page Index</b-th>
          <b-th>Pos</b-th>
          <b-th>X Percentage</b-th>
          <b-th>Y Percentage</b-th>
          <b-th>Language</b-th>
          <b-th>Style</b-th>
          <b-th />
        </b-tr>
      </b-thead>
      <b-tbody>
        <defined-key
          v-for="(item, itemIndex) of items"
          :key="itemIndex"
          v-model="items[itemIndex]"
          @deleteItem="deleteItem(itemIndex, item)"
        />
      </b-tbody>
    </b-table-simple>
  </div>
</template>

<script>
import {
  VBTooltip, BTableSimple, BThead, BTbody, BTh, BTr,
} from 'bootstrap-vue'
import bus from '@/bus'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import DefinedKey from './DefinedKey.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BTableSimple,
    DefinedKey,
    BTbody,
    BThead,
    BTh,
    BTr,
  },
  data() {
    return {
      // 'items' will store the list of defined keys
      items: [],
      // 'deletedIds' will store IDs of items that are marked for deletion
      deletedIds: [],
    }
  },
  computed: {
    // 'definitionId' computes the ID of the selected definition from the Vuex store
    definitionId() {
      return this.$store.getters['dataView/selectedDefinition']?.id
    },
    // 'loading' is a computed property for the loading state, with a getter and setter
    loading: {
      get() {
        // Get the loading state from the Vuex store
        return this.$store.getters['dataView/loading']
      },
      set(value) {
        // Commit the new loading state to the Vuex store
        this.$store.commit('dataView/SET_LOADING', value)
      },
    },
    // 'loadingError' is a computed property for the error state related to loading
    loadingError: {
      get() {
        // Get the loading error state from the Vuex store
        return this.$store.getters['dataView/loadingError']
      },
      set(value) {
        // Commit the new loading error state to the Vuex store
        this.$store.commit('dataView/SET_LOADING_ERROR', value)
      },
    },
  },
  created() {
    // Register event listeners on the bus to listen for specific events
    bus.$on('dataView/addDefinedKeys', this.addItems)
    bus.$on('dataView/saveDefinedKeys', this.save)
    // Call the method to fetch the defined keys initially
    this.fetchDefinedKeys(true)
  },
  destroyed() {
    // Unregister event listeners to avoid memory leaks
    bus.$off('dataView/addDefinedKeys', this.addItems)
    bus.$off('dataView/saveDefinedKeys', this.save)
  },
  methods: {
    // Method to fetch defined keys from the backend API
    fetchDefinedKeys(showSpinner) {
      return new Promise(resolve => {
        // Show a loading spinner if 'showSpinner' is true
        if (showSpinner) {
          this.loading = true
        }
        // Make an API call to fetch defined keys
        axios.get('/defined_keys/', {
          params: {
            definition_id: this.definitionId, // Send the selected definition ID as a parameter
          },
        }).then(res => {
          // Update the 'items' with the fetched data
          this.items = res.data.items
          // Reset the 'deletedIds' array
          this.deletedIds = []
          // Clear any loading error
          this.loadingError = null
          // Set loading state to false
          this.loading = false
          resolve()
        }).catch(error => {
          // If an error occurs, set the error message and update loading state
          this.loadingError = error?.response?.data?.detail || 'Error fetching defined keys'
          this.loading = false
          resolve()
        })
      })
    },
    // Method to add a specific number of new empty items to 'items'
    addItems(count) {
      const lastRowIndex = this.items.length - 1
      const newItems = []
      // Create 'count' new empty items and push them to the 'newItems' array
      for (let i = 0; i < count; i += 1) {
        newItems.push({
          id: '',
          label: '',
          data: {
            pos: null,
            xPercentage: null,
            yPercentage: null,
            pageIndex: null,
            style: null,
          },
        })
      }

      // Add the new items to the 'items' array
      this.items = this.items.concat(newItems)
      // After adding items, scroll the table to the last row
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },
    // Method to scroll the table to a specific row by its index
    scrollToIndex(index) {
      const table = this.$refs.table.$el
      const tbody = table.querySelector('tbody')
      const row = tbody.querySelectorAll('tr')[index]
      const thead = table.querySelector('thead')
      // Scroll the table to the row, accounting for the table header height
      table.scrollTop = row.offsetTop - (thead.offsetHeight + 10)
    },
    // Method to delete an item from the 'items' array
    deleteItem(index, item) {
      // If the item has an ID, add it to the 'deletedIds' array
      if (item.id) {
        this.deletedIds.push(item.id)
      }
      // Remove the item from the 'items' array
      this.items.splice(index, 1)
    },
    // Method to save the defined keys to the backend
    save(callback) {
      axios.post('/defined_keys/', {
        definition_id: this.definitionId, // Send the selected definition ID
        items: this.items, // Send the current items
        deleted_items: this.deletedIds, // Send the deleted items' IDs
      }).then(res => {
        // Fetch the defined keys after saving
        this.fetchDefinedKeys(false)
          .then(() => {
            // Show a success toast notification
            this.$toast({
              component: ToastificationContent,
              props: {
                title: res.data.detail,
                icon: 'CheckIcon',
                variant: 'success',
              },
            })
            callback() // Call the callback function after saving
          })
      }).catch(error => {
        // Show an error toast notification if saving fails
        const message = error?.response?.data?.detail || 'Error saving defined keys'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        callback() // Call the callback function even after failure
      })
    },
  },
}
</script>
