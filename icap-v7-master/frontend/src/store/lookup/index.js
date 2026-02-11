/**
 * Organization: AIDocbuilder Inc.
 * File: lookup/index.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Code optimization and enhancement
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 * Vuex module for managing lookup functionality.
 * This file defines a Vuex store module, handling state, mutations, actions,
 * and getters for managing table field metadata, options, and result data.
 * It communicates with the rules backend API for initialization and data fetching.
 *
 * Dependencies:
 *   - `@/rules-backend-axios`: A custom axios instance for interacting with the rules backend API.
 *
 * Main Features:
 * - Tracks initialization and definition version.
 * - Fetches and structures table field metadata.
 * - Manages result data, search queries, and configurations.
 * - Provides state management for UI actions like enabling submit functionality.
 *
 * Notes:
 *   - This module is namespaced to maintain scope isolation within Vuex.
 *   - Includes logic to ensure compatibility with both keys and table options.
 */

// Importing a custom axios instance configured for the rules backend
// import axios from '@/rules-backend-axios'
import axios from 'axios'

export default {
  // Defining the Vuex module as namespaced
  namespaced: true,

  // Vuex state: stores the data for this module
  state: {
    initialized: false, // Tracks if the module is initialized
    initializedDefinitionVersion: null, // Tracks the definition version used during initialization
    enableSubmit: false, // Enables or disables a submit action
    results: [], // Stores result data
    resultIndex: null, // Index of the selected result
    search: null, // Stores the search query
    executing: false, // Tracks if an operation is in progress
    tableFields: {}, // Holds the table field metadata
    options: {}, // Stores configuration options
    selectedTable: null,
    isLookupEnable: false,
  },

  // Vuex mutations: synchronous methods to update the state
  mutations: {
    SET_TABLE_DATA(state, data) {
      state.results = data
    },
    SET_LOOKUP_ENABLED(state, value) {
      state.isLookupEnable = value
    },
    SET_TOTAL_RECORDS(state, total) {
      state.totalRecords = total
    },
    SET_LOADING(state, isLoading) {
      state.executing = isLoading
    },
    SET_SELECTED_TABLE_NAME(state, value) {
      state.selectedTable = value // Sets the results array
    },
    SET_RESULTS(state, value) {
      state.results = value // Sets the results array
    },
    SET_RESULT_INDEX(state, value) {
      state.resultIndex = value // Sets the index of the selected result
    },
    SET_SEARCH(state, value) {
      state.search = value // Updates the search query
    },
    SET_TABLE_FIELDS(state, value) {
      state.tableFields = value // Sets metadata for table fields
    },
    SET_INITIALIZED(state, value) {
      state.initialized = value // Marks the module as initialized or not
    },
    SET_INITIALIZED_DEFINITION_VERSION(state, value) {
      state.initializedDefinitionVersion = value // Updates the definition version
    },
    SET_ENABlE_SUBMIT(state, value) {
      state.enableSubmit = value // Toggles the enableSubmit flag
    },
    SET_EXECUTING(state, value) {
      state.executing = value // Tracks whether an action is executing
    },
    SET_OPTIONS(state, value) {
      state.options = value // Updates configuration options
    },
  },

  // Vuex actions: asynchronous methods for business logic
  actions: {
    async fetchTableData({ commit }, {
      tableName, processName, page, perPage, sortBy, sortDesc, queries, lookupData, silent = false,
    }) {
      if (!silent) commit('SET_LOADING', true)

      try {
        const requestBody = {
          table: tableName,
          process_name: processName,
          page: String(page || 1),
          page_size: String(perPage || 10),
          sort_by: String(sortBy || ''),
          sort_desc: String(sortDesc || false),
          search_queries: queries || {},
          lookup_queries: lookupData || [],
        }

        const response = await axios.post('/lookup/fetch_records/', requestBody)
        commit('SET_RESULTS', response.data.results)
        return response

      // commit('SET_TABLE_DATA', records)
      // commit('SET_TOTAL_RECORDS', response.data.total_records || response.data.count || records.length || 0)
      } catch (error) {
        commit('SET_TABLE_DATA', [])
        commit('SET_TOTAL_RECORDS', 0)
        return {
          records: [],
          total: 0,
        }
      } finally {
        if (!silent) commit('SET_LOADING', false)
      }
    },
    // Initializes the module with table fields and options
    async initialize({ commit, rootGetters }, { processName }) {
      // const { initialized, initializedDefinitionVersion } = state
      const selectedDefinitionVersion = rootGetters['dataView/selectedDefinitionVersion']
      // const selectedProject = state.project || rootGetters['batch/batch']?.project

      // Skip initialization if already initialized with the same version
      // if (initialized && initializedDefinitionVersion === selectedDefinitionVersion) {
      //   return
      // }

      let tableFieldsResponse
      // let optionsResponse
      try {
        // Fetch table field metadata with process_name parameter
        tableFieldsResponse = await axios.get('/lookup/table_fields/', {
          params: {
            process_name: processName,
          },
        })
      } catch (error) {
        // Handle errors during table field fetch
        const loadingError = error?.response?.data?.detail || 'Error fetching lookup tables'
        throw new Error(loadingError)
      }

      // try {
      //   // Fetch options metadata
      //   optionsResponse = await axios.get('/options/')
      // } catch (error) {
      //   // Handle errors during options fetch
      //   const loadingError = error?.response?.data?.detail || 'Error fetching lookup options'
      //   throw new Error(loadingError)
      // }

      // Process the table field response into a structured format
      const tableFields = {}
      tableFieldsResponse.data.data.forEach(tableField => {
        if (!tableFields[tableField.TABLE_NAME]) {
          tableFields[tableField.TABLE_NAME] = {
            columns: [],
          }
        }

        tableFields[tableField.TABLE_NAME].columns.push({
          name: tableField.COLUMN_NAME,
          type: tableField.DATA_TYPE,
          semantic_match: tableField.SEMANTIC_MATCH || false,
          dynamic_column: tableField.DYNAMIC_COLUMN || false,
        })
      })

      // Process the options response
      // const optionsData = optionsResponse.data.data
      // const options = {
      //   useMultipleEnvWiseDbs: optionsData.use_multiple_env_wise_dbs,
      //   environmentOptions: optionsData.environment_options,
      // }

      // Commit changes to the state
      commit('SET_TABLE_FIELDS', tableFields)
      // commit('SET_OPTIONS', options)
      commit('SET_INITIALIZED_DEFINITION_VERSION', selectedDefinitionVersion)
      commit('SET_INITIALIZED', true)
    },

    // Resets all module state to defaults
    reset({ dispatch }) {
      dispatch('resetResultData') // Reset result-related data
      dispatch('resetConfig') // Reset configuration
    },

    // Resets result-related data
    resetResultData({ commit }) {
      commit('SET_RESULTS', [])
      commit('SET_RESULT_INDEX', null)
      commit('SET_SEARCH', null)
      commit('SET_ENABlE_SUBMIT', false)
      commit('SET_EXECUTING', false)
    },

    // Resets configuration data
    resetConfig({ commit }) {
      commit('SET_TABLE_FIELDS', {})
      commit('SET_OPTIONS', {})
      commit('SET_INITIALIZED', false)
      commit('SET_INITIALIZED_DEFINITION_VERSION', null)
    },
  },

  // Vuex getters: compute derived state
  getters: {
    isLookupEnabled(state) {
      return state.isLookupEnable // Returns the executing flag
    },
    executing(state) {
      return state.executing // Returns the executing flag
    },
    initialized(state) {
      return state.initialized // Returns the initialized flag
    },
    enableSubmit(state) {
      return state.enableSubmit // Returns the enableSubmit flag
    },
    search(state) {
      return state.search // Returns the search query
    },
    resultIndex(state) {
      return state.resultIndex // Returns the result index
    },
    results(state) {
      return state.results // Returns the results array
    },
    options(state) {
      return state.options // Returns configuration options
    },
    tables(state) {
      return Object.keys(state.tableFields) // Returns an array of table names
    },
    getSelectedTableName(state) {
      return state.selectedTable // Returns an array of table names
    },
    tableColumns(state) {
      // Returns columns for a given table name
      return tableName => {
        const fieldDetails = state.tableFields[tableName]
        if (!fieldDetails) {
          return []
        }
        return fieldDetails.columns
      }
    },
    totalRecords: state => state.totalRecords,
    isLoading: state => state.executing,
  },
}
