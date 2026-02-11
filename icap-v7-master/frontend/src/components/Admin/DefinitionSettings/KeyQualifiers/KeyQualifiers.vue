<template>
  <div>
    <!-- Header section with title and buttons -->
    <div class="d-flex align-items-center justify-content-center mb-1">
      <h2 class="my-0 flex-grow-1">
        Key Qualifiers <!-- Title of the section -->
      </h2>
      <div>
        <!-- Button to add a new qualifier -->
        <b-button
          class="mx-1"
          variant="outline-primary"
          @click="addQualifier"
        >
          Add Qualifier
        </b-button>
        <!-- Save button component for saving data -->
        <save-button action="definitionSettings/saveData" />
      </div>
    </div>

    <!-- Render a list of KeyQualifier components -->
    <div>
      <key-qualifier
        v-for="(qualifier, index) of qualifiers"
        :id="index + 1"
        :key="index"
        v-model="qualifiers[index]"
        :expanded="expands[index]"
        @delete="deleteQualifier(index)"
        @toggle-expand="toggleExpand(index)"
      />
    </div>
  </div>
</template>

<script>
import { BButton } from 'bootstrap-vue' // Importing BootstrapVue button
import SaveButton from '@/components/UI/SaveButton.vue' // Importing custom SaveButton component
import KeyQualifier from './KeyQualifier.vue' // Importing KeyQualifier component

export default {
  components: {
    BButton, // Registering Bootstrap button component
    KeyQualifier, // Registering KeyQualifier component
    SaveButton, // Registering SaveButton component
  },
  data() {
    return {
      expands: [], // Tracks the expanded state for each qualifier
    }
  },
  computed: {
    // Two-way binding for the qualifiers data using Vuex store
    qualifiers: {
      get() {
        return this.$store.getters['definitionSettings/keyQualifiers'] // Fetch qualifiers from Vuex
      },
      set(value) {
        this.$store.commit('definitionSettings/SET_KEY_QUALIFIERS', value) // Update qualifiers in Vuex
      },
    },
  },
  created() {
    this.setInitialExpandStatus() // Initialize the expanded state for qualifiers
  },
  methods: {
    // Sets initial expansion status for all qualifiers to false
    setInitialExpandStatus() {
      this.expands = this.qualifiers.map(() => false)
    },
    // Toggles the expanded state of a specific qualifier
    toggleExpand(index) {
      this.$set(this.expands, index, !this.expands[index])
    },
    // Adds a new qualifier to the list
    addQualifier() {
      this.qualifiers.push({
        name: '', // Default name
        options: [], // Default options
      })
      this.expands.push(false) // New qualifier is not expanded by default
    },
    // Deletes a qualifier from the list and removes its expansion state
    deleteQualifier(index) {
      this.qualifiers.splice(index, 1) // Remove qualifier from list
      this.expands.splice(index, 1) // Remove corresponding expansion state
    },
  },
}
</script>
