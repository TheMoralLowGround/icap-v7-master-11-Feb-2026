<template>
  <div>
    <!-- Header section with a title and save button -->
    <div class="d-flex align-items-center justify-content-center mb-1">
      <h2 class="my-0 flex-grow-1">
        Options <!-- Title of the section -->
      </h2>
      <div>
        <!-- Save button component to trigger save action -->
        <save-button action="definitionSettings/saveData" />
      </div>
    </div>

    <!-- Dynamic rendering of Option components -->
    <div>
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
import SaveButton from '@/components/UI/SaveButton.vue' // Importing custom SaveButton component
import Option from './Option.vue' // Importing Option component

export default {
  components: {
    SaveButton, // Registering SaveButton component
    Option, // Registering Option component
  },
  computed: {
    // Computed property for options, connected to the Vuex store
    options: {
      get() {
        return this.$store.getters['definitionSettings/options'] // Retrieve options from Vuex store
      },
      set(value) {
        this.$store.commit('definitionSettings/SET_OPTIONS', value) // Update options in Vuex store
      },
    },
    // Computed property for editable keys, retrieves editable option keys from Vuex store
    editableKeys() {
      return this.$store.getters['definitionSettings/editableOptions']
    },
  },
}
</script>
