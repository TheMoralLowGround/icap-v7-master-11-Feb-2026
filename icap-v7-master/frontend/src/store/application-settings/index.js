/**
 * Organization: AIDocbuilder Inc.
 * File: application-settings/index.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Enhanced and refined state management for application settings
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   This Vuex store module manages the application settings, including:
 *     - General options and configurations for tables, keys, and rules.
 *     - Definition versions and default version handling.
 *     - Persistent storage of settings through API integration.
 *
 * Dependencies:
 *   - `axios`: For performing HTTP requests to fetch and save settings.
 *
 * Main Features:
 *   - **State Management**:
 *       - Holds application settings such as `options`, `tableSettings`, `keySettings`, and others.
 *       - Tracks definition versions and manages their default selection.
 *   - **Mutations**:
 *       - Directly modify specific parts of the state, including rules, table settings, and key configurations.
 *   - **Actions**:
 *       - Fetch settings from the server and update the state.
 *       - Save current settings back to the server.
 *       - Reset settings to their default state.
 *   - **Getters**:
 *       - Provide access to individual settings and computed outputs, such as aggregated settings for saving.
 *       - Additional utilities, like checking if lookups are enabled.
 *
 * Notes:
 *   - The module is namespaced for modularity.
 *   - Error handling is implemented for API requests, ensuring meaningful error messages.
 *   - State changes are synchronized with API responses for consistency.
 */

// Import Axios for making HTTP requests
import axios from 'axios'

export default {
  // Enable Vuex module namespacing for modular state management
  namespaced: true,

  // Define the state to hold various application settings
  state: {
    options: {}, // General application options
    tableSettings: null, // Settings specific to table configurations
    editableOptions: [], // List of editable options
    keySettings: null, // Settings related to key configurations
    otherSettings: null, // Miscellaneous application settings
    keyRuleSettings: null, // Rules specific to key configurations
    tableRuleSettings: null, // Rules specific to table configurations
    tableNormalizerSettings: null, // Settings for normalizing table data
    profileSettings: null, // Settings for profiles
    projectSettings: null, // Settings for project
    definitionVersions: [], // List of available definition versions
    defaultDefinitionVersion: null, // Default definition version
  },

  // Define mutations for directly modifying the state
  mutations: {
    SET_OPTIONS(state, data) {
      state.options = data
    },
    SET_TABLE_SETTINGS(state, data) {
      state.tableSettings = data
    },
    SET_EDITABLE_OPTIONS(state, data) {
      state.editableOptions = data
    },
    SET_KEY_SETTINGS(state, data) {
      state.keySettings = data
    },
    SET_OTHER_SETTINGS(state, data) {
      state.otherSettings = data
    },
    SET_KEY_RULE_SETTINGS(state, data) {
      state.keyRuleSettings = data
    },
    SET_TABLE_RULE_SETTINGS(state, data) {
      state.tableRuleSettings = data
    },
    SET_TABLE_NORMALIZER_SETTINGS(state, data) {
      state.tableNormalizerSettings = data
    },
    SET_DEFINITION_VERSIONS(state, data) {
      state.definitionVersions = data
    },
    SET_DEFAULT_DEFINITION_VERSION(state, data) {
      state.defaultDefinitionVersion = data
    },
    SET_PROFILE_SETTINGS(state, data) {
      state.profileSettings = data
    },
    SET_PROJECT_SETTINGS(state, data) {
      state.projectSettings = data
    },
  },

  // Define actions for asynchronous or complex state modifications
  actions: {
    // Fetch application settings from the server
    async fetchApplicationSettings({ dispatch, commit, state }) {
      try {
        // Fetch the data
        await dispatch('fetchData')

        // Commit additional settings to other modules
        commit('dataView/SET_SELECTED_DEFINITION_VERSION', state.defaultDefinitionVersion, { root: true })
        commit('atm/SET_ATM_CONFIG', state.tableSettings.automatedTableModelConfig, { root: true })
      } catch (error) {
        // Handle and throw errors if fetching fails
        const err = error?.response?.data?.detail || 'Fetching Application Settings'
        throw new Error(err)
      }
    },

    // Fetch data for all application settings
    async fetchData({ commit }) {
      const res = await axios.get('/application-settings/')

      // Commit the fetched data to the state
      commit('SET_OPTIONS', res.data.data.options)
      commit('SET_TABLE_SETTINGS', res.data.data.tableSettings)
      commit('SET_EDITABLE_OPTIONS', res.data.data.editableOptions)
      commit('SET_KEY_SETTINGS', res.data.data.keySettings)
      commit('SET_OTHER_SETTINGS', res.data.data.otherSettings)
      commit('SET_KEY_RULE_SETTINGS', res.data.data.keyRuleSettings)
      commit('SET_TABLE_RULE_SETTINGS', res.data.data.tableRuleSettings)
      commit('SET_TABLE_NORMALIZER_SETTINGS', res.data.data.tableNormalizerSettings)
      commit('SET_PROFILE_SETTINGS', res.data.data.profileSettings)
      commit('SET_PROJECT_SETTINGS', res.data.data.projectSettings)

      commit('SET_DEFINITION_VERSIONS', res.data.definition_versions)
      commit('SET_DEFAULT_DEFINITION_VERSION', res.data.default_definition_version)

      return res
    },

    // Save the application settings to the server
    async saveData({ commit, getters }) {
      const applicationSettings = getters.outputData // Gather current settings

      const res = await axios.post('/application-settings/', { data: applicationSettings })

      // Update the state with the saved data
      commit('SET_OPTIONS', res.data.data.options)
      commit('SET_TABLE_SETTINGS', res.data.data.tableSettings)
      commit('SET_EDITABLE_OPTIONS', res.data.data.editableOptions)
      commit('SET_KEY_SETTINGS', res.data.data.keySettings)
      commit('SET_OTHER_SETTINGS', res.data.data.otherSettings)
      commit('SET_KEY_RULE_SETTINGS', res.data.data.keyRuleSettings)
      commit('SET_TABLE_RULE_SETTINGS', res.data.data.tableRuleSettings)
      commit('SET_TABLE_NORMALIZER_SETTINGS', res.data.data.tableNormalizerSettings)
      commit('SET_PROFILE_SETTINGS', res.data.data.profileSettings)
      commit('SET_PROJECT_SETTINGS', res.data.data.projectSettings)

      res.data.detail = 'Definition settings saved successfully'

      return res
    },

    // Reset all application settings to their default state
    reset({ commit }) {
      commit('SET_OPTIONS', {})
      commit('SET_TABLE_SETTINGS', null)
      commit('SET_EDITABLE_OPTIONS', [])
      commit('SET_KEY_SETTINGS', null)
      commit('SET_OTHER_SETTINGS', null)
      commit('SET_KEY_RULE_SETTINGS', null)
      commit('SET_TABLE_RULE_SETTINGS', null)
      commit('SET_TABLE_NORMALIZER_SETTINGS', null)
      commit('SET_PROFILE_SETTINGS', null)
      commit('SET_PROJECT_SETTINGS', null)
      commit('SET_DEFINITION_VERSIONS', [])
      commit('SET_DEFAULT_DEFINITION_VERSION', null)
    },
  },

  // Define getters to access specific parts of the state
  getters: {
    options(state) {
      return state.options
    },
    tableSettings(state) {
      return state.tableSettings
    },
    keySettings(state) {
      return state.keySettings
    },
    editableOptions(state) {
      return state.editableOptions
    },
    otherSettings(state) {
      return state.otherSettings
    },
    keyRuleSettings(state) {
      return state.keyRuleSettings
    },
    tableRuleSettings(state) {
      return state.tableRuleSettings
    },
    tableNormalizerSettings(state) {
      return state.tableNormalizerSettings
    },

    // Gather all settings into a single object for saving or further processing
    outputData(state) {
      const {
        options,
        tableSettings,
        keySettings,
        editableOptions,
        otherSettings,
        keyRuleSettings,
        tableRuleSettings,
        tableNormalizerSettings,
        profileSettings,
        projectSettings,
      } = state
      return {
        options,
        tableSettings,
        editableOptions,
        keySettings,
        otherSettings,
        keyRuleSettings,
        tableRuleSettings,
        tableNormalizerSettings,
        profileSettings,
        projectSettings,
      }
    },

    // Check if lookups are enabled in other settings
    enableLookups(state) {
      return state.otherSettings?.enableLookups || false
    },

    // Get the list of definition versions
    definitionVersions(state) {
      return state.definitionVersions
    },

    // Get the default definition version
    defaultDefinitionVersion(state) {
      return state.defaultDefinitionVersion
    },
  },
}
