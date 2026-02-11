<!--
 Organization: AIDocbuilder Inc.
 File: options.vue
 Version: 1.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   This component provides a centralized interface for managing multiple option
   groups dynamically. Each option group is rendered as a child component (`Option`),
   allowing for modularity and reusability. The `options.vue` component integrates with
   Vuex for seamless state management, enabling real-time updates and saving changes
   to the application's settings.

 Dependencies:
   - SaveButton: Custom component for saving application settings.
   - Option: Child component that encapsulates individual option groups.
   - Vuex Store: Retrieves and updates options and editable keys from the store.

 Main Features:
   - Dynamically renders multiple option groups using the `Option` component.
   - Allows editing, sorting, and validating items within each option group.
   - Save button triggers an action to persist changes to the backend.
   - Two-way binding with Vuex for reactivity and state synchronization.

 Core Components:
   - `<SaveButton>`: A button to persist changes to application settings.
   - `<Option>`: A child component responsible for rendering and managing a single
     option group with fields such as text, checkbox, and dropdown.

 Computed Properties:
   - `options`: Retrieves and updates the application settings options from Vuex.
   - `editableKeys`: Provides a list of keys corresponding to editable option groups.

 Notes:
   - The `options` and `editableKeys` data are fetched and managed via Vuex getters
     and mutations.
   - Each `Option` component instance is passed necessary props such as `items`,
     `fields`, and `sortBy` for dynamic rendering.
   - The SaveButton component executes the `applicationSettings/saveData` action to
     persist all changes.
-->

<template>
  <div>
    <!-- Header Section -->
    <div class="d-flex align-items-center justify-content-center mb-1">
      <h2 class="my-0 flex-grow-1">
        Options
        <!-- Displays a header for the Options section -->
      </h2>
      <div>
        <!-- Save Button Component -->
        <!-- Triggers the save action for application settings -->
        <save-button action="applicationSettings/saveData" />
      </div>
    </div>

    <!-- Options Section -->
    <div>
      <!-- Loops through editableKeys and renders Option components dynamically
        - Binds items array for the specific option
        - Passes the title of the option
        - Specifies the key field to identify option items
        - Provides the configuration for fields in the option
        - Specifies the field for sorting items
      -->
      <Option
        v-for="key of editableKeys"
        :key="key"
        v-model="options[key].items"
        :title="options[key].title"
        :value-key="options[key].valueKey"
        :fields="options[key].fields"
        :sort-by="options[key].sortBy"
      />
    </div>
  </div>
</template>

<script>
import SaveButton from '@/components/UI/SaveButton.vue'
import Option from './Option.vue'

export default {
  components: {
    SaveButton, // Imports the SaveButton component for saving settings
    Option, // Imports the Option component to render individual settings groups
  },
  computed: {
    options: {
      get() {
        // Retrieves the current options from the Vuex store
        return this.$store.getters['applicationSettings/options']
      },
      set(value) {
        // Updates the options in the Vuex store
        this.$store.commit('applicationSettings/SET_OPTIONS', value)
      },
    },
    editableKeys() {
      // Retrieves the keys for editable options from the Vuex store
      return this.$store.getters['applicationSettings/editableOptions']
    },
  },
}
</script>
