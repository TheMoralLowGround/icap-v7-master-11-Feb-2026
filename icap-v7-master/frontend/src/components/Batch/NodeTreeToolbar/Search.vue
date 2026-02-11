<template>
  <!-- Search form using Bootstrap Vue's b-form component -->
  <b-form
    class="d-lg-flex flex-lg-row align-items-baseline"
    @submit.prevent="searchSubmitHandler"
  >
    <div class="mr-md-1 flex-lg-fill">
      <!-- Input field for search query, bound to the 'search' data property -->
      <b-form-input
        v-model="search"
        type="text"
        placeholder="Search"
      />
      <!-- Display the count of matched nodes when a search is submitted -->
      <p
        v-if="submittedSearch"
        class="mb-0 mt-25"
      >
        Found {{ matchedNodesCount }} matching nodes
      </p>
    </div>
    <!-- Submit button with spinner indicating ongoing search -->
    <b-button
      variant="primary"
      :disabled="searching"
      type="submit"
    >
      Search
      <!-- Spinner displayed while the search is in progress -->
      <b-spinner
        v-if="searching"
        small
        label="Small Spinner"
      />
    </b-button>
  </b-form>
</template>

<script>
// Importing required Bootstrap Vue components
import {
  BForm, BFormInput, BSpinner, BButton,
} from 'bootstrap-vue'

export default {
  // component register
  components: {
    BForm,
    BFormInput,
    BSpinner,
    BButton,
  },
  data() {
    return {
      // The search query is initialized with the value from the Vuex store
      search: this.$store.getters['batch/search'],
      // Boolean to track the loading state during a search
      searching: false,
    }
  },
  computed: {
    // Computed property to retrieve the current search term from the Vuex store
    submittedSearch() {
      return this.$store.getters['batch/search']
    },
    // Computed property to get the count of matched nodes from the Vuex store
    matchedNodesCount() {
      return this.$store.getters['batch/matchedNodes'].length
    },
  },
  methods: {
    // Handles the form submission to perform a search
    searchSubmitHandler() {
      this.searching = true // Set searching state to true

      // Use $forceNextTick to ensure reactive updates before dispatching the search action
      this.$forceNextTick(() => {
        // Dispatch the search action to update the store with the new search query
        this.$store.dispatch('batch/setSearch', this.search)

        // Reset the searching state after the store update
        this.$forceNextTick(() => {
          this.searching = false
        })
      })
    },
  },
}
</script>
