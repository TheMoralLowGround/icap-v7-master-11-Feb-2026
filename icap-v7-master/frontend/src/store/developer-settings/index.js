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
import getEnv from '@/utils/env'

export default {
  // Enable Vuex module namespacing for modular state management
  namespaced: true,

  // Define the state to hold various application settings
  state: {
    frontend_settings: [], // General application options
    backend_settings: [], // General application options
  },

  // Define mutations for directly modifying the state
  mutations: {
    SET_FRONTEND(state, data) {
      state.frontend_settings = data
    },
    SET_BACKEND(state, data) {
      state.backend_settings = data
    },
  },

  // Define actions for asynchronous or complex state modifications
  actions: {
    // Fetch application settings from the server
    async fetchDeveloperSettings({ dispatch }) {
      try {
        // Fetch the data
        await dispatch('fetchData')
      } catch (error) {
        // console.error('Error fetching developer settings:', error?.response?.data?.detail || error)
      }
    },

    // Fetch data for all application settings
    async fetchData({ commit }) {
      const res = await axios.get('dashboard/developer-settings/')
      // Commit the fetched data to the state
      commit('SET_FRONTEND', res.data.data.frontend_settings)
      commit('SET_BACKEND', res.data.data.backend_settings)
      return res
    },

    // Save the application settings to the server
    async saveData({ commit, getters }) {
      const developerSettings = getters.outputData // Gather current settings

      const res = await axios.post('dashboard/developer-settings/', { data: developerSettings })

      // Update the state with the saved data
      commit('SET_FRONTEND', res.data.data.frontend_settings)
      commit('SET_BACKEND', res.data.data.backend_settings)

      res.data.detail = 'Developer settings saved successfully'

      return res
    },

    // Reset all application settings to their default state
    reset({ commit }) {
      commit('SET_FRONTEND', [])
      commit('SET_BACKEND', [])
    },
  },

  // Define getters to access specific parts of the state
  getters: {
    frontend_settings(state) {
      return state.frontend_settings
    },
    isDeveloper() {
      // Ensure user is developer
      const displayDeveloperSettings = getEnv('VUE_APP_DISPLAY_DEVELOPER_SETTINGS') || 0
      return displayDeveloperSettings === '1'
    },
    showProfileTraining(state) {
      // Ensure frontend_settings is defined and not empty
      const displayDeveloperSettings = getEnv('VUE_APP_DISPLAY_DEVELOPER_SETTINGS') || 0

      if (displayDeveloperSettings !== '1' || !state.frontend_settings.length) {
        return false
      }
      // Retrieve the "Profile Training" setting from frontend_settings
      const profileTraining = state.frontend_settings.find(
        setting => setting.name === 'Profile Training',
      )

      // Check the environment variable and the value of "Profile Training"
      return displayDeveloperSettings === '1' && profileTraining?.value === true
    },
    allowUploadBatch(state) {
      // Ensure frontend_settings is defined and not empty
      const displayDeveloperSettings = getEnv('VUE_APP_DISPLAY_DEVELOPER_SETTINGS') || 0

      if (displayDeveloperSettings !== '1' || !state.frontend_settings.length) {
        return false
      }
      // Retrieve the "Allow Batch Upload" setting from frontend_settings
      const allowBatchUpload = state.frontend_settings.find(
        setting => setting.name === 'Batch Upload',
      )

      // Check the environment variable and the value of "Allow Batch Upload"
      return displayDeveloperSettings === '1' && allowBatchUpload?.value === true
      // return true
    },
    backend_settings(state) {
      return state.backend_settings
    },

    // Gather all settings into a single object for saving or further processing
    outputData(state) {
      const {
        frontend_settings,
        backend_settings,
      } = state
      return {
        frontend_settings,
        backend_settings,
      }
    },
  },
}
