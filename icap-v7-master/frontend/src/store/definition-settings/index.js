/**
 * Organization: AIDocbuilder Inc.
 * File: definition-settings/index.js
 * Version: 1.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Code optimization and enhancement: Ali
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   This Vuex store module manages the definition settings within the application.
 *   It provides state, mutations, actions, and getters to handle:
 *     - Options for definitions
 *     - Key qualifiers
 *     - Compound keys
 *     - Editable options
 *     - Project-related settings
 *
 * Dependencies:
 *   - axios: For making HTTP requests
 *   - lodash (cloneDeep): For deep cloning data structures
 *
 * Main Features:
 *   - **State Management**:
 *       - Store configuration data such as `options`, `keyQualifiers`, and `compoundKeys`.
 *   - **Mutations**:
 *       - Update state values based on server responses or user interactions.
 *   - **Actions**:
 *       - Fetch and save definition settings to the backend via API calls.
 *       - Process and organize key options and qualifiers for dynamic rules.
 *   - **Getters**:
 *       - Provide computed and filtered views of the state for efficient use.
 *   - **Utilities**:
 *       - Reset state to default values for improved modularity and reusability.
 *
 * Notes:
 *   - This module is namespaced to maintain scope isolation within Vuex.
 *   - Includes logic to ensure compatibility with both keys and table options.
 */

// Import necessary modules
import axios from 'axios' // Import axios for making HTTP requests
import { cloneDeep } from 'lodash' // Import cloneDeep function from lodash for deep cloning data

// Vuex module
export default {
  namespaced: true, // This module is namespaced, meaning its mutations, actions, and getters will be scoped to this module
  state: {
    // Initial state for storing various options and settings
    options: {}, // Stores general options for the definition settings
    keyOptionsForRules: [], // Stores options for keys in rules
    keyOptionsForTableLookups: [], // Stores options for table lookups
    editableOptions: [], // Stores options that are editable
    keyQualifiers: [], // Stores key qualifiers
    compoundKeys: [], // Stores compound keys
    projectOptions: [], // Stores options related to the project
    project: null, // Stores the current project selected
    aIAgents: [],
  },
  mutations: {
    // Mutations for setting the state values
    SET_OPTIONS(state, data) {
      state.options = data // Set options in the state
    },
    SET_KEY_OPTIONS_FOR_RULES(state, data) {
      state.keyOptionsForRules = data // Set key options for rules in the state
    },
    SET_KEY_OPTIONS_FOR_TABLE_LOOKUPS(state, data) {
      state.keyOptionsForTableLookups = data // Set key options for table lookups in the state
    },
    SET_EDITABLE_OPTIONS(state, data) {
      state.editableOptions = data // Set editable options in the state
    },
    SET_KEY_QUALIFIERS(state, data) {
      state.keyQualifiers = data // Set key qualifiers in the state
    },
    SET_AI_AGENTS(state, data) {
      state.aIAgents = data // Set aIagents
    },
    SET_COMPOUND_KEYS(state, data) {
      state.compoundKeys = data // Set compound keys in the state
    },
    SET_PROJECT_OPTIONS(state, data) {
      state.projectOptions = data // Set project options in the state
    },
    SET_PROJECT(state, data) {
      state.project = data // Set the current project in the state
    },
  },
  actions: {
    // Action to fetch definition settings
    async fetchDefinitionSettings({ dispatch }) {
      try {
        // Dispatch fetchData, setKeyOptionsForRules and setKeyOptionsForTableLookups actions sequentially
        await dispatch('fetchData')
        await dispatch('setKeyOptionsForRules')
        await dispatch('setKeyOptionsForTableLookups')
      } catch (error) {
        // If an error occurs, throw a new error with a specific message
        const err = error?.response?.data?.detail || 'Fetching Definition Settings'
        throw new Error(err)
      }
    },

    // Action to fetch data for definition settings from the server
    async fetchData({ rootGetters, commit, state }) {
      const params = {
        project: state.project || rootGetters['batch/selectedBatch']?.project, // Get the current project if available, otherwise use the root state
      }

      // Make an HTTP GET request to fetch definition settings
      const res = await axios.get('/get_definition_settings/', { params })

      // Commit the fetched data to the state via mutations
      commit('SET_OPTIONS', res.data.options)
      commit('SET_EDITABLE_OPTIONS', res.data.editableOptions)
      commit('SET_KEY_QUALIFIERS', res.data.keyQualifiers)
      commit('SET_AI_AGENTS', res.data.aIAgents)
      commit('SET_COMPOUND_KEYS', res.data.compoundKeys || [])

      return res // Return the response
    },

    // Action to save the data back to the server
    async saveData({
      rootGetters, state, commit, getters,
    }) {
      const definitionSettings = getters.outputData // Get the output data from getters

      const data = {
        project: state.project || rootGetters['batch/batch']?.project, // Get the current project if available
        definition_settings: definitionSettings, // Include the definition settings
      }

      // Make an HTTP POST request to save the definition settings
      const res = await axios.post('/update_definition_settings/', data)

      // Commit the updated data to the state via mutations
      commit('SET_OPTIONS', res.data.data.options)
      commit('SET_EDITABLE_OPTIONS', res.data.data.editableOptions)
      commit('SET_KEY_QUALIFIERS', res.data.data.keyQualifiers)
      commit('SET_AI_AGENTS', res.data.data.aIAgents)
      commit('SET_COMPOUND_KEYS', res.data.data.compoundKeys || [])

      res.data.detail = 'Definition settings saved successfully' // Add a success message to the response

      return res // Return the response
    },

    // Action to set key options for rules based on the current selection
    setKeyOptionsForRules({
      rootGetters, state, commit, getters,
    }) {
      const applicableFor = rootGetters['batch/view'] === 'key' ? 'keys' : 'table' // Determine if we're dealing with keys or tables
      const keyOptions = getters.keyOptions(applicableFor) // Get the applicable key options
      const keyOptionsForRules = [] // Initialize an array to store the options for rules

      // Iterate over key options to filter and process them for rules
      keyOptions.forEach(e => {
        // If the key has a qualifier or compound keys, skip it
        if (e.qualifier !== '' || e.compoundKeys !== '') {
          return
        }

        // Add the key option to the keyOptionsForRules array
        keyOptionsForRules.push({
          label: e.keyValue,
          value: {
            fieldInfo: e,
            parent: null,
          },
        })
      })

      // Iterate over key qualifiers to add their options to keyOptionsForRules
      state.keyQualifiers.forEach(item => {
        item.options.forEach(e => {
          keyOptionsForRules.push({
            label: `${item.name} - ${e.value}`,
            value: {
              fieldInfo: {
                keyValue: e.value,
                keyLabel: e.label,
              },
              parent: item.name,
            },
          })
        })
      })

      // If applicable for keys, process compound keys as well
      if (applicableFor === 'keys') {
        state.compoundKeys.forEach(item => {
          item.keyItems.forEach(e => {
            keyOptionsForRules.push({
              label: `${item.name} - ${e.keyValue}`,
              value: {
                fieldInfo: e,
                parent: item.name,
              },
            })
          })
        })
      }

      // Commit the processed key options for rules to the state
      commit('SET_KEY_OPTIONS_FOR_RULES', keyOptionsForRules)
    },

    // Action to set key options for rules based on the current selection
    setKeyOptionsForTableLookups({
      state, commit, getters,
    }) {
      let combinedOptions = [] // Array to store combined key and table options

      // Get key options
      const keyOptions = getters.keyOptions('keys')
      // Get table options
      const tableOptions = getters.keyOptions('table')

      // Combine key and table options into a single array
      combinedOptions = [...keyOptions, ...tableOptions]

      const keyOptionsForTableLookups = [] // Initialize an array to store the options for rules

      // Iterate over key options to filter and process them for rules
      combinedOptions.forEach(e => {
        // If the key has a qualifier or compound keys, skip it
        if (e.qualifier !== '' || e.compoundKeys !== '') {
          return
        }

        // Add the key option to the keyOptionsForTableLookups array
        keyOptionsForTableLookups.push({
          label: e.keyValue,
          value: {
            fieldInfo: e,
            parent: null,
          },
        })
      })

      // Iterate over key qualifiers to add their options to keyOptionsForTableLookups
      state.keyQualifiers.forEach(item => {
        item.options.forEach(e => {
          keyOptionsForTableLookups.push({
            label: `${item.name} - ${e.value}`,
            value: {
              fieldInfo: {
                keyValue: e.value,
                keyLabel: e.label,
              },
              parent: item.name,
            },
          })
        })
      })

      // keyOptionsForTableLookups.sort((a, b) => a.label.localeCompare(b.label))
      // Commit the processed key options for rules to the state
      commit('SET_KEY_OPTIONS_FOR_TABLE_LOOKUPS', keyOptionsForTableLookups)
    },

    // Action to reset all state values
    reset({ commit }) {
      commit('SET_OPTIONS', {}) // Reset options
      commit('SET_EDITABLE_OPTIONS', []) // Reset editable options
      commit('SET_KEY_QUALIFIERS', []) // Reset key qualifiers
      commit('SET_AI_AGENTS', []) // Reset agents
      commit('SET_COMPOUND_KEYS', []) // Reset compound keys
      commit('SET_PROJECT_OPTIONS', []) // Reset project options
      commit('SET_PROJECT', null) // Reset the project
    },
  },
  getters: {
    options(state) {
      return state.options
    },
    keyItems(state) {
      return state.options['options-keys']?.items || []
    },
    sortedOptions(state) {
      const options = cloneDeep(state.options)

      if (options['options-keys']) {
        options['options-keys'].items.sort((a, b) => {
          const valueA = a.keyLabel.toUpperCase()
          const valueB = b.keyLabel.toUpperCase()

          if (valueA < valueB) { return -1 }
          if (valueA > valueB) { return 1 }
          return 0
        })
      }

      return options
    },
    keyTypeAvailablity(state) {
      const availability = {}
      const colTypeOptions = state.options['options-col-type']

      if (!colTypeOptions) {
        return availability
      }

      colTypeOptions.items.forEach(colTypeOptionItem => {
        const key = colTypeOptionItem[colTypeOptions.valueKey]
        availability[key] = {
          applicableForKeys: colTypeOptionItem.applicableForKeys,
          applicableForTable: colTypeOptionItem.applicableForTable,
        }
      })

      return availability
    },
    keyOptions(state, getters) {
      return applicableFor => {
        const keyOptions = getters.sortedOptions['options-keys']
        const { keyTypeAvailablity } = getters
        const checkKey = applicableFor === 'keys' ? 'applicableForKeys' : 'applicableForTable'
        // const checkKey = applicableFor === 'keys' ? ['table'] : ['key', 'compound', 'addressBlock', 'addressBlockPartial']

        if (!keyOptions) {
          return []
        }

        return keyOptions.items.filter(keyOptionItem => {
          if (!keyOptionItem.type) {
            return true
          }
          // return !checkKey.includes(keyOptionItem.type)
          return keyTypeAvailablity[keyOptionItem.type]?.[checkKey]
        })
      }
    },
    keyOptionsForRules(state) {
      return state.keyOptionsForRules
    },
    keyOptionsForTableLookups(state) {
      return state.keyOptionsForTableLookups
    },
    keyOptionsApplicableForKeys(state, getters) {
      return getters.keyOptions('keys')
    },
    keyOptionsApplicableForTable(state, getters) {
      return getters.keyOptions('table')
    },
    keyQualifiers(state) {
      return state.keyQualifiers
    },
    getAiAgents(state) {
      return state.aIAgents
    },
    editableOptions(state) {
      return state.editableOptions
    },
    outputData(state) {
      const {
        options,
        keyQualifiers,
        editableOptions,
        compoundKeys,
      } = state

      return {
        options,
        editableOptions,
        keyQualifiers,
        compoundKeys,
      }
    },
    compoundKeys(state) {
      return state.compoundKeys
    },
    projectOptions(state) {
      return state.projectOptions
    },
    project(state) {
      return state.project
    },
  },
}
