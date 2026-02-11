<!--
 Organization: AIDocbuilder Inc.
 File: DataViewer.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   - A Vue component for rendering and managing dynamic data views based on various modes.
   - It handles multiple modes such as table settings, key settings, chunk data, and test modes.
   - Features error handling with alerts and a loading spinner while data is being fetched.
   - Includes components for managing table models, columns, keys, rules, and chunk data.

 Features:
   - Conditional rendering of different content based on the current mode and state.
   - Dynamic updates to the store data such as table models, columns, and key items.
   - Error handling and loading spinner support during data fetching.
   - Integrates several child components for specific data views (e.g., table models, key models, chunk data).
   - Uses Vuex store for managing and accessing state related to data viewing.

 Dependencies:
   - bootstrap-vue - For alert and spinner components.
   - bus - For event bus handling.
   - Vuex - For state management and accessing the data store.
   - Vue Router - For route handling and accessing the current route name.

 Notes:
   - Ensure proper handling of store getters and setters to maintain state across different modes.
   - This component dynamically renders various sub-components depending on the selected mode, and interacts with the Vuex store to update state as needed.
-->

<template>
  <!-- Main container with a flex-column layout -->
  <div class="d-flex flex-column definitions-container">

    <!-- Alert box for displaying error messages if loading fails -->
    <b-alert
      variant="danger"
      :show="!loading && loadingError !== null ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }} <!-- Displays the error message -->
        </p>
      </div>
    </b-alert>

    <!-- Loading spinner displayed while data is being loaded -->
    <div
      v-if="loading && mode !== 'automated-table-model'"
      class="text-center"
    >
      <b-spinner variant="primary" />
    </div>

    <!-- Scrollable content wrapper -->
    <div
      class="flex-grow-1 definitions-content-wrapper"
      @scroll="onScroll"
    >
      <div class="definitions-content-box">
        <div class="definitions-content">

          <!-- Conditional rendering of content based on loading and error states -->
          <template v-if="!loading && !loadingError">

            <!-- Content for 'tableSettings' mode -->
            <template v-if="mainMode === 'tableSettings' && mode !== 'test'">
              <!-- Component for table models -->

              <table-models
                v-show="mode === 'table-models'"
                v-model="tableModels"
              />
              <!-- Component for table columns -->
              <table-columns
                v-show="mode === 'table-columns'"
                v-model="tableColumns"
              />
              <!-- Component for table keys -->
              <key-items
                v-show="mode === 'table-keys'"
                v-model="tableKeyItems"
                source="tableKeyItems"
              />
              <!-- Component for table column prompts -->
              <key-items
                v-show="mode === 'table-column-prompts'"
                v-model="tableColumnPrompts"
                source="tableColumnPrompts"
              />
              <!-- Component for table rule items -->
              <table-rule-items
                v-show="mode === 'table-rule-items'"
              />
              <!-- Component for key lookup items -->
              <table-lookup-items
                v-show="mode === 'table-lookup-items'"
              />
              <!-- Component for key lookups -->
              <table-lookup
                v-if="mode === 'table-lookup'"
                v-model="tableLookupItemQueries"
              />
              <!-- Component for table rules -->
              <table-rules
                v-if="mode === 'table-rules'"
                v-model="tableRuleItemRules"
              />
              <!-- Component for table normalizer items -->
              <table-normalizer-items
                v-show="mode === 'table-normalizer'"
                v-model="tableNormalizerItems"
              />
            </template>

            <!-- Content for test or verification modes -->
            <table-test v-if="['test', 'verification'].includes(mode)" />

            <!-- Content for 'keySettings' mode -->
            <template v-if="mainMode === 'keySettings'">
              <!-- Component for key models -->
              <key-models
                v-show="mode === 'key-models'"
                v-model="keyModels"
              />
              <!-- Component for key items -->
              <key-items
                v-show="mode === 'key-items'"
                v-model="keyItems"
                source="keyItems"
              />
              <!-- Component for key rule items -->
              <key-rule-items
                v-show="mode === 'key-rule-items'"
              />
              <!-- Component for key rules -->
              <key-rules
                v-if="mode === 'key-rules'"
                v-model="keyRuleItemRules"
              />
              <!-- Component for items not in use -->
              <key-not-in-use-items
                v-show="mode === 'key-not-in-use-items'"
              />
              <!-- Component for key lookup items -->
              <key-lookup-items
                v-show="mode === 'key-lookup-items'"
              />
              <!-- Component for key lookups -->
              <key-lookup
                v-if="mode === 'key-lookup'"
                v-model="keyLookupItemQueries"
              />
            </template>

            <template v-if="mode === 'chunk-data'">
              <div>
                <!-- Tabs Navigation -->
                <b-tabs
                  v-model="activeTab"
                  content-class="mt-3"
                >
                  <b-tab
                    title="Chunk Data"
                    active
                  >
                    <chunk-data
                      v-if="mode === 'chunk-data'"
                      :error="loadChunkDataError"
                    />
                  </b-tab>
                  <b-tab title="Plain Text">
                    <chunk-data-with-plain-text
                      v-if="mode === 'chunk-data'"
                      :error="loadChunkDataWithPlainTextError"
                    />
                  </b-tab>
                </b-tabs>
              </div>
            </template>

            <!-- Component for explore-lookup batch view -->
            <key-lookup
              v-if="batchView === 'explore-lookup'"
              :value="[]"
            />
          </template>

          <!-- Component for defined keys -->
          <defined-keys v-if="mode === 'defined-keys'" />

          <!-- Component for automated table model -->
          <atm v-if="mode === 'automated-table-model'" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  BSpinner, BAlert, BTabs, BTab,
} from 'bootstrap-vue'
import bus from '@/bus'
import TableModels from './TableModels/TableModels.vue'
import TableColumns from './TableColumns/TableColumns.vue'
import TableTest from './TableTest/TableTest.vue'
import TableRules from './TableRules/TableRules.vue'
import TableRuleItems from './TableRuleItems/TableRuleItems.vue'
import TableNormalizerItems from './TableNormalizerItems/TableNormalizerItems.vue'

import KeyModels from './KeyModels/KeyModels.vue'
import KeyItems from './KeyItems/KeyItems.vue'
import KeyRuleItems from './KeyRuleItems/KeyRuleItems.vue'
import KeyRules from './KeyRules/KeyRules.vue'
import KeyNotInUseItems from './KeyNotInUseItems/KeyNotInUseItems.vue'
import KeyLookupItems from './KeyLookupItems/KeyLookupItems.vue'
import KeyLookup from './KeyLookup/KeyLookup.vue'
import TableLookupItems from './TableLookupItems/TableLookupItems.vue'
import TableLookup from './TableLookup/TableLookup.vue'

import ChunkData from './ChunkData/ChunkData.vue'
import ChunkDataWithPlainText from './ChunkData/ChunkDataWithPlainText.vue'
import DefinedKeys from './DefinedKeys/DefinedKeys.vue'
import Atm from './Atm/Atm.vue'

export default {
  components: {
    TableModels,
    TableColumns,
    TableTest,
    KeyModels,
    KeyItems,
    BSpinner,
    BAlert,
    KeyRuleItems,
    KeyRules,
    ChunkData,
    ChunkDataWithPlainText,
    DefinedKeys,
    Atm,
    KeyNotInUseItems,
    TableRules,
    TableRuleItems,
    TableNormalizerItems,
    KeyLookup,
    KeyLookupItems,
    TableLookupItems,
    TableLookup,
    BTabs,
    BTab,
  },
  data() {
    return {
      initialized: false, // Flag to track whether the component has been initialized
      activeTab: 0,
      loadChunkDataWithPlainTextError: null,
      loadChunkDataError: null,
    }
  },
  computed: {
    // Getters to access store state, allowing reactive updates when the store changes
    mainMode() {
      return this.$store.getters['dataView/mainMode'] // Returns the current main mode from the store
    },
    mode() {
      return this.$store.getters['dataView/mode'] // Returns the current mode from the store
    },
    selectedDefinitionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion'] // Selected definition version from the store
    },
    batchView() {
      return this.$store.getters['batch/view'] // Batch view status from the store
    },
    selectedTableId() {
      return this.$store.getters['batch/selectedTableId'] // Batch view status from the store
    },
    dataRefreshKey() {
      // Constructs a unique key based on batchView, mainMode, and selectedDefinitionVersion
      return `${this.batchView}+${this.mainMode}+${this.selectedDefinitionVersion}`
    },
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition'] // Selected definition from the store
    },
    currentRouteName() {
      return this.$route.name // Returns the current route name from Vue Router
    },

    // Getter and Setter for each piece of data managed in Vuex (data store)
    tableModels: {
      get() {
        return this.$store.getters['dataView/tableModels'] // Returns tableModels from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_MODELS', value) // Commits new value to store
      },
    },
    tableColumns: {
      get() {
        return this.$store.getters['dataView/tableColumns'] // Returns tableColumns from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_COLUMNS', value) // Commits new value to store
      },
    },
    tableKeyItems: {
      get() {
        return this.$store.getters['dataView/tableKeyItems'] // Returns tableKeyItems from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_KEY_ITEMS', value) // Commits new value to store
      },
    },
    tableColumnPrompts: {
      get() {
        // Simply return stored column prompts from definition
        // Works the same way as tableKeyItems - shows what's stored in the definition
        return this.$store.getters['dataView/tableColumnPrompts'] || []
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_COLUMN_PROMPTS', value) // Commits new value to store
      },
    },
    // profileDefinitionKeys() {
    //   return this.$store.getters['batch/profileDefinitionKeys'] || []
    // },
    definitionKeys() {
      return this.$store.getters['dataView/selectedDefinition']?.key?.items || []
    },
    keyItems: {
      get() {
        // Return keys directly from store - they're already merged by mergePromptKeysIntoDefinition action
        // No need to merge again here (that was causing duplicates!)
        const allKeys = this.definitionKeys || []

        // Sort alphabetically by keyLabel or label (using slice to avoid mutating original array)
        return [...allKeys].sort((a, b) => {
          const labelA = (a.keyLabel || a.label || '').toLowerCase()
          const labelB = (b.keyLabel || b.label || '').toLowerCase()
          return labelA.localeCompare(labelB)
        })
      },
      set(value) {
        // Just pass through - filtering happens during save, not here
        // This prevents performance issues during drag/drop and editing
        this.$store.commit('dataView/SET_KEY_ITEMS', value)
      },
    },
    keyModels: {
      get() {
        return this.$store.getters['dataView/keyModels'] // Returns keyModels from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_KEY_MODELS', value) // Commits new value to store
      },
    },
    keyRuleItemRules: {
      get() {
        return this.$store.getters['dataView/keyRuleItemRules'] // Returns keyRuleItemRules from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_KEY_RULE_ITEM_RULES', value) // Commits new value to store
      },
    },
    tableRuleItemRules: {
      get() {
        return this.$store.getters['dataView/tableRuleItemRules'] // Returns tableRuleItemRules from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_RULE_ITEM_RULES', value) // Commits new value to store
      },
    },
    tableNormalizerItems: {
      get() {
        return this.$store.getters['dataView/tableNormalizerItems'] // Returns tableNormalizerItems from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_NORMALIZER_ITEMS', value) // Commits new value to store
      },
    },
    keyLookupItemQueries: {
      get() {
        return this.$store.getters['dataView/keyLookupItemQueries'] // Returns keyLookupItemQueries from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_KEY_LOOKUP_ITEM_QUERIES', value) // Commits new value to store
      },
    },
    tableLookupItemQueries: {
      get() {
        return this.$store.getters['dataView/tableLookupItemQueries'] // Returns tableLookupItemQueries from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_TABLE_LOOKUP_ITEM_QUERIES', value) // Commits new value to store
      },
    },
    loading: {
      get() {
        return this.$store.getters['dataView/loading'] // Returns loading state from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_LOADING', value) // Commits loading state to store
      },
    },
    loadingError: {
      get() {
        return this.$store.getters['dataView/loadingError'] // Returns loading error from the store
      },
      set(value) {
        this.$store.commit('dataView/SET_LOADING_ERROR', value) // Commits loading error to store
      },
    },
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
  },
  watch: {
    // Watch for changes to dataRefreshKey and trigger fetchData
    dataRefreshKey() {
      if (this.initialized) {
        this.fetchData() // Fetch new data when the dataRefreshKey changes
      }
    },
    // Watch for changes to selectedTableUniqueId and reset chunk line records if necessary
    selectedTableUniqueId() {
      if (this.mode !== 'automated-table-model') {
        this.$store.dispatch('atm/resetChunkLineRecords') // Resets chunk data if the mode isn't 'automated-table-model'
      }
    },
  },
  created() {
    // Register event listener to fetch data on custom 'dataView/refreshData' event
    bus.$on('dataView/refreshData', this.fetchData)
    this.fetchData() // Trigger the initial data fetch when the component is created
  },
  destroyed() {
    // Unregister the event listener when the component is destroyed
    bus.$off('dataView/refreshData', this.fetchData)
  },
  methods: {
    onScroll(e) {
      // Emit a scroll event to notify other parts of the app about the scroll action
      bus.$emit('dataView/onScroll', e)
    },
    async fetchData() {
      this.loading = true // Set loading state to true while fetching data

      // Determine which data to fetch based on the main mode
      if (['keySettings', 'tableSettings', 'automatedTableModel'].includes(this.mainMode)) {
        // Close any currently active rule or lookup screens before fetching data
        if (this.$store.getters['dataView/mode'] === 'key-rules') {
          this.$store.dispatch('dataView/setMode', 'key-rule-items') // Switch mode to key rule items
        } else if (this.$store.getters['dataView/mode'] === 'table-rules') {
          this.$store.dispatch('dataView/setMode', 'table-rule-items') // Switch mode to table rule items
        } else if (this.$store.getters['dataView/mode'] === 'key-lookup') {
          this.$store.dispatch('dataView/setMode', 'key-lookup-items') // Switch mode to key lookup items
        } else if (this.$store.getters['dataView/mode'] === 'table-lookup') {
          this.$store.dispatch('dataView/setMode', 'table-lookup-items') // Switch mode to key lookup items
        }

        // Fetch the data for the definition
        try {
          await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
          await this.$store.dispatch('batch/fetchProfileKeys')
        } catch (error) {
          this.loadingError = error // Set the error if the fetch fails
          this.loading = false // Set loading to false

          if (!this.initialized) {
            this.initialized = true // Mark the component as initialized
          }

          return
        }
      } else if (this.mainMode === 'chunkData') {
        // Fetch chunk data if in chunkData mode
        this.loadChunkDataError = null
        this.loadChunkDataWithPlainTextError = null

        try {
          // First action with separate error handling
          try {
            await this.$store.dispatch('batch/loadChunkData')
            this.loadChunkDataError = null // Clear error if successful
          } catch (error) {
            this.loadChunkDataError = error.message || 'Error loading chunk data'
            // Don't return here as we want to try the second action
          }

          // Second action with separate error handling
          try {
            await this.$store.dispatch('batch/loadChunkDataWithPlainText')
            this.loadChunkDataWithPlainTextError = null // Clear error if successful
          } catch (error) {
            this.loadChunkDataWithPlainTextError = error.message || 'Error loading chunk data with plain text'
          }
        } catch (error) {
          this.loading = false // Set loading to false
          if (!this.initialized) {
            this.initialized = true // Mark as initialized
          }
          return
        }
      }

      // If no errors, reset loading and error states
      this.loadingError = null
      this.loading = false
      if (!this.initialized) {
        this.initialized = true // Mark as initialized after successful data load
      }
    },
  },
}
</script>

<style scoped>
.definitions-container {
  height: 100%;
  row-gap: 0.5rem;
}
.definitions-content-wrapper {
  overflow: auto;
}
.definitions-content-box {
  position: relative;
  height: 100%;
}
.definitions-content {
  position: absolute;
  top: 0px;
  left: 0px;
  width: 100%;
  height: 100%;
}
</style>
