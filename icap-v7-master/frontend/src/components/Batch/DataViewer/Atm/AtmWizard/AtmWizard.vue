<template>
  <div
    :class="{'h-100': loading}"
  >
    <!-- Tab Buttons -->
    <b-button-group
      style="margin: 0.5rem"
    >
      <b-button
        v-for="(key, index) in Object.keys(atmWizardTabs)"
        :key="index + key"
        :variant="atmWizardTabs[key].active ? 'primary' : 'outline-primary'"
        size="sm"
        @click="onChangeTab(key)"
      >
        {{ `${index + 1}. ${atmWizardTabs[key].label}` }}
      </b-button>
    </b-button-group>

    <div
      class="separator"
      style="margin: 0.5rem 0"
    />

    <!-- Table Row Selection Tab -->
    <table-row-selection-tab />

    <!-- Results Tab -->
    <slot
      v-if="atmWizardTabs.results.active"
      name="results"
    />

    <!-- Test Tab -->
    <table-test v-if="!loading && atmWizardTabs.test.active" />

    <!-- Loader -->
    <div
      v-if="loading"
      class="mx-1 h-80 d-flex flex-column justify-content-center align-items-center"
      style="height: 80%"
    >
      <spinner-progress-loader
        :max="multipleLineRecord ? totalPages * 1.5 : totalPages * 0.1"
        :status="status ? status.status : ''"
        loading
        class="mx-2"
      />
    </div>

    <!-- scrollToTop Button -->
    <scroll-to-top-button
      v-if="atmWizardTabs.results.active || atmWizardTabs.test.active"
    />
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BButtonGroup, BButton,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import SpinnerProgressLoader from '@/components/UI/SpinnerProgressLoader.vue'
import TableTest from '../../TableTest/TableTest.vue'

import TableRowSelectionTab from './AtmWizardTabs/TableRowSelectionTab.vue'
import ScrollToTopButton from '../ScrollToTopButton.vue'

export default {
  components: {
    BButtonGroup,
    BButton,
    SpinnerProgressLoader,
    TableTest,
    // eslint-disable-next-line vue/no-unused-components
    ToastificationContent,
    TableRowSelectionTab,
    ScrollToTopButton,
  },
  computed: {
    // Retrieves the unique ID of the currently selected table from the store.
    selectedTableUniqueId() {
      // Returns the unique ID of the selected table based on the store state
      const definitionTables = this.$store.getters['dataView/table']
      const selectedTableName = this.$store.getters['dataView/selectedTableName']

      if (definitionTables.length && selectedTableName) {
        const selectedTable = definitionTables.find(
          table => table.table_name === selectedTableName,
        )
        return selectedTable?.table_unique_id || null
      }

      return null
    },

    // Fetches the ATM wizard tabs configuration from the store.
    atmWizardTabs() {
      return this.$store.getters['atm/atmWizardTabs']
    },

    // Computed property to get and set the loading state via Vuex.
    loading: {
      get() {
        return this.$store.getters['dataView/loading']
      },
      set(value) {
        this.$store.commit('dataView/SET_LOADING', value)
      },
    },

    // Fetches the batch status from the store.
    status() {
      return this.$store.getters['batch/status']
    },

    // Retrieves the total number of pages from the store.
    totalPages() {
      return this.$store.getters['batch/totalPages']
    },

    // Fetches the selected definition version from the store.
    selectedDefintionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },

    // Retrieves the user-selected patterns from the store.
    userSelectedPatterns() {
      return this.$store.getters['atm/userSelectedPatterns']
    },

    // Gets the state of multiple line record mode from the store.
    multipleLineRecord() {
      return this.$store.getters['dataView/modelMultipleLineRecord']
    },
  },

  watch: {
    // Watches for changes to the selected table's unique ID and resets ATM data when it changes.
    selectedTableUniqueId() {
      this.onResetAtmData()
    },

    // Watches changes in the ATM wizard tabs configuration and updates selected patterns accordingly.
    atmWizardTabs() {
      if (this.atmWizardTabs.tableRowSelection.active) {
        if (this.multipleLineRecord) {
          this.$store.dispatch('atm/refreshExtendUserSelectedPatterns')
        } else {
          this.$store.dispatch('atm/refreshUserSelectedPatterns')
        }
      }
    },
  },

  created() {
    // Registers an event listener for tab change events using a bus.
    bus.$on('atm/onChangeTab', this.onChangeTab)
  },

  destroyed() {
    // Removes the event listener when the component is destroyed to avoid memory leaks.
    bus.$off('atm/onChangeTab', this.onChangeTab)
  },

  methods: {
    // Resets ATM data by clearing patterns, pattern records, and updating the store.
    onResetAtmData() {
      this.$store.commit('atm/SET_ATM_PATTERNS', [])
      this.$store.commit('atm/SET_ATM_PATTERN_RECORDS', [])
      this.$store.commit('atm/SET_SELECTED_ATM_PATTERNS', [])

      this.$store.dispatch('atm/resetChunkLineRecords')

      if (this.multipleLineRecord) {
        this.$store.dispatch('atm/refreshExtendUserSelectedPatterns')
      } else {
        this.$store.dispatch('atm/refreshUserSelectedPatterns')
      }

      this.$store.dispatch('atm/refreshUserSelectedOb')
    },

    // Handles switching active tabs in the ATM wizard.
    onChangeTab(key) {
      const atmWizardTabs = { ...this.atmWizardTabs }

      // If the tab is already active, do nothing.
      if (atmWizardTabs[key].active) {
        return
      }

      // Updates the active state for all tabs: sets the clicked tab to active and others to inactive.
      Object.keys(atmWizardTabs).forEach(keyItem => {
        if (key === keyItem) {
          atmWizardTabs[keyItem].active = true
        } else {
          atmWizardTabs[keyItem].active = false
        }
      })

      // Commits the updated ATM wizard tabs configuration to the store.
      this.$store.commit('atm/SET_ATM_WIZARD_TABS', atmWizardTabs)
    },
  },
}
</script>
