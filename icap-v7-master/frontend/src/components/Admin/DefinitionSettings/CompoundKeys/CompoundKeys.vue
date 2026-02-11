<template>
  <div>
    <!-- Header section with title and action buttons -->
    <div class="d-flex align-items-center justify-content-center mb-1">
      <h2 class="my-0 flex-grow-1">
        Compound Keys
      </h2>
      <div>
        <!-- Button to add a new compound key -->
        <b-button
          class="mx-1"
          variant="outline-primary"
          @click="addCompoundKey"
        >
          Add Compound Key
        </b-button>
        <!-- Save button to save the data -->
        <save-button action="definitionSettings/saveData" />
      </div>
    </div>

    <!-- Render a list of CompoundKey components dynamically -->
    <div>
      <compound-key
        v-for="(compoundKey, index) of compoundKeys"
        :id="index + 1"
        :key="index"
        v-model="compoundKeys[index]"
        :expanded="expands[index]"
        @delete="deleteCompoundKey(index)"
        @toggle-expand="toggleExpand(index)"
      />
    </div>
  </div>
</template>

<script>
import { BButton } from 'bootstrap-vue'
import SaveButton from '@/components/UI/SaveButton.vue'
import CompoundKey from './CompoundKey.vue'

export default {
  components: {
    BButton,
    CompoundKey, // Child component for managing individual compound keys
    SaveButton, // Reusable save button component
  },
  data() {
    return {
      expands: [], // Tracks the expand/collapse state for each compound key
    }
  },
  computed: {
    // Computed property for compound keys from the Vuex store
    compoundKeys: {
      get() {
        return this.$store.getters['definitionSettings/compoundKeys'] // Retrieves compound keys from the store
      },
      set(value) {
        this.$store.commit('definitionSettings/SET_COMPOUND_KEYS', value) // Updates compound keys in the store
      },
    },
  },
  created() {
    this.setInitialExpandStatus() // Initialize expand status for all compound keys
  },
  methods: {
    // Initializes the expand/collapse state for all compound keys
    setInitialExpandStatus() {
      this.expands = this.compoundKeys.map(() => false) // Default to all collapsed
    },

    // Toggles the expand/collapse state for a specific compound key
    toggleExpand(index) {
      this.$set(this.expands, index, !this.expands[index]) // Updates the state reactively
    },

    // Adds a new compound key with default values and sets its expand state to collapsed
    addCompoundKey() {
      this.compoundKeys.push({
        name: '', // Default name is empty
        keyItems: [], // Default keyItems is an empty array
      })
      this.expands.push(false) // Adds a new collapsed state
    },

    // Deletes a compound key and its corresponding expand state
    deleteCompoundKey(index) {
      this.compoundKeys.splice(index, 1) // Removes the compound key
      this.expands.splice(index, 1) // Removes the associated expand state
    },
  },
}
</script>
