<!--
 Organization: AIDocbuilder Inc.
 File: DefinedKeyActions.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component provides the actions for adding and saving defined keys within the application. It includes
   an "Add Key" button for triggering the addition of keys and a "Save" button for saving the defined keys to
   the store. It utilizes a reusable `AddItem` component for adding keys and a `b-spinner` to indicate the
   saving process.

 Main Features:
   - Add Item functionality with a count of keys to be added
   - Save functionality with a loading spinner while saving
   - Emits custom events to interact with the event bus for adding and saving defined keys
   - Reusable AddItem component for key input

 Dependencies:
   - Bootstrap Vue: For button and spinner components
   - Event Bus: For communication between components
   - `AddItem` Component: For reusing the logic to add keys

 Notes:
   - The component listens for events to add defined keys and save them.
   - It tracks the saving state and shows a spinner while the save operation is in progress.
   - Custom events are emitted through the event bus to trigger actions in other parts of the application.
-->

<template>
  <div class="d-flex align-items-center defined-key-actions">
    <!-- Section for adding keys -->
    <div class="add-keys">
      <add-item
        label="Key"
        button-variant="outline-primary"
        @add="add"
      />
    </div>

    <!-- Save button -->
    <b-button
      variant="outline-primary"
      :disabled="saving"
      @click="save"
    >
      Save
      <!-- Spinner displayed while saving is true -->
      <b-spinner
        v-if="saving"
        small
        label="Small Spinner"
      />
    </b-button>
  </div>
</template>

<script>
import AddItem from '@/components/UI/AddItem.vue' // Importing reusable AddItem component
import bus from '@/bus' // Importing event bus for communication
import { BButton, BSpinner } from 'bootstrap-vue' // Importing BootstrapVue components

export default {
  components: {
    AddItem,
    BButton,
    BSpinner,
  },
  data() {
    return {
      saving: false, // Tracks the state of the save operation
    }
  },
  methods: {
    /**
     * Method to add defined keys.
     * Emits an event through the event bus with a specific count of keys to be added.
     * @param {number} count - Number of keys to add.
     */
    add(count) {
      bus.$emit('dataView/addDefinedKeys', count)
    },
    /**
     * Method to save defined keys.
     * Emits a save event through the event bus and updates the saving state.
     * Once the save operation completes (via callback), `saving` is set to false.
     */
    save() {
      this.saving = true // Set saving state to true
      bus.$emit('dataView/saveDefinedKeys', () => {
        this.saving = false // Reset saving state upon completion
      })
    },
  },
}
</script>

<style scoped>
.defined-key-actions {
  column-gap: 1rem;
}
.add-keys {
  width: 220px;
  display: inline-block;
}
</style>
