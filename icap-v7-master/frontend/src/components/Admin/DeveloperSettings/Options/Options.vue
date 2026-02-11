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
    <!-- Header section with a title and save button -->
    <div class="d-flex align-items-center justify-content-center mb-1">
      <h2 class="my-0 flex-grow-1">
        Options <!-- Title of the section -->
      </h2>
      <div>
        <!-- Save button component to trigger save action -->
        <save-button action="developerSettings/saveData" />
      </div>
    </div>

    <!-- Dynamic rendering of Option components -->
    <div>
      <Option
        v-for="(key, index) in editableSettings"
        :key="index"
        v-model="key.items"
        :title="key.title"
        :value-key="key.valueKey"
        :fields="key.fields"
        @input="handleInput(key.title, key.items)"
      />
    </div>
  </div>
</template>

<script>
import SaveButton from '@/components/UI/SaveButton.vue' // Importing custom SaveButton component
import Option from './Option.vue' // Importing Option component

export default {
  components: {
    SaveButton, // Registering SaveButton component
    Option, // Registering Option component
  },
  computed: {
    // Transforming the settings dynamically based on Vuex getters
    editableSettings() {
      const backendSettings = this.$store.getters['developerSettings/backend_settings']
      const frontendSettings = this.$store.getters['developerSettings/frontend_settings']

      return [
        {
          items: backendSettings,
          title: 'backend_settings',
          fields: [
            { key: 'name', type: 'text' },
            { key: 'description', type: 'text' },
            { key: 'value', type: 'checkbox' },
          ],
          lableKey: 'name',
          valueKey: 'value',
        },
        {
          items: frontendSettings,
          title: 'frontend_settings',
          fields: [
            { key: 'name', type: 'text' },
            { key: 'description', type: 'text' },
            { key: 'value', type: 'checkbox' },
          ],
          lableKey: 'name',
          valueKey: 'value',
        },
      ]
    },
  },
  methods: {
    /**
     * Handles input changes from v-model and commits the updated value to the store
     * @param {string} title - The section title (e.g., 'backend_settings' or 'frontend_settings')
     * @param {Array} items - The updated array of items
     */
    handleInput(title, items) {
      if (title === 'backend_settings') {
        this.$store.commit('developerSettings/SET_BACKEND', items)
      } else if (title === 'frontend_settings') {
        this.$store.commit('developerSettings/SET_FRONTEND', items)
      }
    },
  },
}
</script>
