<!--
 Organization: AIDocbuilder Inc.
 File: AtmActions.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component provides action buttons for controlling the ATM wizard process. It dynamically displays
   different buttons based on the current tab of the ATM wizard (e.g., "Next", "Find Patterns", "Save",
   "Go to Model", and "Test"). It interacts with Vuex for state management and communicates via a global event bus
   for actions such as saving data, finding ATM patterns, and transitioning between tabs.

 Main Features:
   - Displays action buttons based on the active tab in the ATM wizard (Next, Find Patterns, Save, Go to Model, Test)
   - Provides spinner feedback while loading
   - Warns user to save before leaving the results tab
   - Allows for interaction with the ATM patterns and test functionality
   - Integrates with Vuex for managing state like ATM patterns, user selections, and batch status
   - Listens for and emits custom events for saving data, finding patterns, and transitioning between views

 Dependencies:
   - Bootstrap Vue: For button and spinner components
   - Event Bus: For communication between components
   - Vuex: For managing application state related to ATM patterns and user selections
   - Vue Router: For navigating between different views of the application

 Notes:
   - The component listens for and reacts to custom events like `findAtmPatterns` to trigger ATM pattern finding.
   - It ensures that the user is warned if attempting to leave the results tab without saving.
-->

<template>
  <!-- Main container for the action buttons -->
  <div
    class="d-flex align-items-center atm-actions"
  >
    <!-- "Next" button: visible only when tableRowSelection tab is active -->
    <b-button
      v-if="atmWizardTabs.tableRowSelection.active"
      :disabled="loading"
      variant="outline-primary"
      class="ml-auto cursor-pointer-not-allowed"
      @click="onChangeTab"
    >
      Next
    </b-button>

    <!-- "Find Patterns" button: visible only when results tab is active -->
    <b-button
      v-if="atmWizardTabs.results.active"
      :disabled="loading"
      variant="outline-primary"
      class="ml-auto cursor-pointer-not-allowed"
      @click="findAtmPatterns"
    >
      Find Patterns
    </b-button>

    <!-- "Save" button: visible when test tab is not active -->
    <b-button
      v-if="!atmWizardTabs.test.active"
      :disabled="loading"
      variant="outline-primary"
      class="ml-auto cursor-pointer-not-allowed"
      @click="save"
    >
      Save
      <!-- Small spinner displayed when loading -->
      <b-spinner
        v-if="loading"
        small
        label="Small Spinner"
      />
    </b-button>

    <!-- "Go to Model" button: visible only when test tab is active -->
    <b-button
      v-if="atmWizardTabs.test.active"
      :disabled="loading"
      variant="outline-primary"
      class="ml-auto cursor-pointer-not-allowed"
      @click="goToModel"
    >
      Go to Model
    </b-button>

    <!-- "Test" button: visible only when test tab is active -->
    <b-button
      v-if="atmWizardTabs.test.active"
      :disabled="loading"
      variant="outline-primary"
      class="ml-auto cursor-pointer-not-allowed"
      @click="test"
    >
      Test
    </b-button>
  </div>
</template>

<script>
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import {
  BButton, BSpinner,
} from 'bootstrap-vue'

export default {
  components: {
    BButton, BSpinner,
  },
  data() {
    return {
      warn: false, // Warning state flag
    }
  },
  computed: {
    // Getters to retrieve necessary state from Vuex store
    batchId() {
      return this.$store.getters['batch/batch'].id
    },
    selectedAtmPatterns() {
      return this.$store.getters['atm/selectedAtmPatterns']
    },
    atmPatterns() {
      return this.$store.getters['atm/atmPatterns']
    },
    atmWizardTabs() {
      return this.$store.getters['atm/atmWizardTabs']
    },
    userSelectedPatterns() {
      return this.$store.getters['atm/userSelectedPatterns']
    },
    extendedUserSelectedPatterns() {
      return this.$store.getters['atm/extendedUserSelectedPatterns']
    },
    modelUserSelectedPatterns() {
      return this.$store.getters['dataView/modelUserSelectedPatterns']
    },
    userSelectedOb() {
      return this.$store.getters['atm/userSelectedOb']
    },
    modelUserSelectedOb() {
      return this.$store.getters['dataView/modelUserSelectedOb']
    },
    status() {
      return this.$store.getters['batch/status']
    },
    loading: {
      // Getter and setter for the loading state
      get() {
        return this.$store.getters['dataView/loading']
      },
      set(value) {
        this.$store.commit('dataView/SET_LOADING', value)
      },
    },
  },
  watch: {
    // Watcher for changes in atmWizardTabs
    atmWizardTabs(newVal) {
      // Show a warning toast if leaving results tab without saving
      if (!newVal.results.active && this.warn) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Please save before leave',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },
  },
  created() {
    // Listen for custom event to find ATM patterns
    bus.$on('findAtmPatterns', this.findAtmPatterns)
  },
  destroyed() {
    // Remove event listener on component destruction
    bus.$off('findAtmPatterns', this.findAtmPatterns)
  },
  methods: {
    // Method to handle tab change
    onChangeTab() {
      // Clear ATM patterns in the store
      this.$store.commit('atm/SET_ATM_PATTERNS', [])
      // Emit event to switch to results tab
      bus.$emit('atm/onChangeTab', 'results')
    },
    save() {
      this.loading = true

      if (this.warn && this.atmWizardTabs.results.active) {
        this.warn = false
      }

      if (this.atmWizardTabs.results.active && this.atmPatterns.length) {
        this.$store.commit('dataView/SET_MODEL_AUTO_PATTERNS', this.selectedAtmPatterns)
        this.$store.commit('dataView/SET_MODEL_AUTO_TYPE', 'autoPattern')
      }

      // Set modelUserSelectedPatterns
      this.$store.commit('dataView/SET_MODEL_USER_SELECTED_PATTERNS', this.userSelectedPatterns)

      // Set modelExtendedUserSelectedPatterns
      this.$store.commit('dataView/SET_MODEL_EXTENDED_USER_SELECTED_PATTERNS', this.extendedUserSelectedPatterns.filter(e => e.length))

      // Set modelUserSelectedOb
      this.$store.commit('dataView/SET_MODEL_USER_SELECTED_OB', this.userSelectedOb)

      bus.$emit('dataView/saveTableData')

      setTimeout(() => {
        this.loading = false
      }, 100)
    },
    findAtmPatterns() {
      if (!this.warn) {
        this.warn = true
      }

      this.$store.commit('atm/SET_ATM_PATTERNS', [])

      bus.$emit('dataView/saveTableData')

      this.$store.dispatch('atm/findAtmPatterns')
    },
    goToModel() {
      this.$store.commit('dataView/SET_MODEL_AUTO_TYPE', 'autoPattern')

      bus.$emit('dataView/saveTableData')

      setTimeout(() => {
        this.$store.commit('batch/SET_VIEW', 'table')

        this.$router.push({
          name: 'batch',
          params: {
            id: this.$route.params.id,
          },
          query: this.$route.query,
        })
      }, 200)
    },
    test() {
      this.$store.commit('dataView/SET_MODEL_AUTO_TYPE', 'autoPattern')

      this.$store.dispatch('atm/runTest')
    },
  },
}
</script>

<style scoped>
.atm-actions {
  column-gap: 1rem;
  margin-left: auto;
}
</style>
