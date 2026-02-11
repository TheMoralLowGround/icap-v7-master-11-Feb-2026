/**
 * Organization: AIDocbuilder Inc.
 * File: application-settings/index.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Enhanced and refined state management for atm
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   This Vuex store module manages the atm, including:
 *   This file contains the Vuex store module for managing the state and actions related to ATM pattern processing in the application.
 *   It handles various aspects of the ATM Wizard, including managing tabs, accordion options, and user-selected patterns.
 *
 * Dependencies:
 *   - `axios`: For performing HTTP requests to fetch and save settings.
 *
 * Main Features:
 *   - Modular state management with namespacing
 *   - Actions for fetching ATM chunk data, finding and loading ATM patterns, running tests, and refreshing selected patterns
 *   - State management for various ATM-related configurations and records
 *   - Asynchronous API requests using axios to interact with backend services
 *
 * Core Components:
 *   - atmWizardTabs: Manages tab configurations for the ATM wizard
 *   - atmAccordionOptions: Contains accordion options for pattern matching
 *   - atmConfig, atmPatterns, atmPatternRecords: Holds configurations and records related to ATM pattern processing
 *   - Actions like `fetchAtmChunkData`, `findAtmPatterns`, `loadAtmPatterns`, and `runTest` for handling asynchronous operations
 *   - Toast notifications for success and error feedback using Vue.$toast and ToastificationContent component
 *
 * Notes:
 *   - The module is namespaced for modularity.
 *   - Error handling is implemented for API requests, ensuring meaningful error messages.
 *   - State changes are synchronized with API responses for consistency.
 */
import Vue from 'vue'
import axios from 'axios'
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  // Enable Vuex module namespacing for modular state management
  namespaced: true,

  // Define the state to hold various application settings
  state: {
    atmWizardTabs: {
      tableRowSelection: {
        label: 'Table Row Selection',
        active: true,
      },
      results: {
        label: 'Results',
        active: false,
      },
      test: {
        label: 'Test',
        active: false,
      },
    },
    atmAccordionOptions: [
      { key: 'green', label: 'Fully Match', visible: false },
      { key: 'pink', label: 'Very Close Match', visible: false },
      { key: 'yellow', label: 'Close Match', visible: false },
      { key: 'blank', label: 'Not Match', visible: false },
    ],
    atmConfig: null,
    chunkLineRecords: [],
    userSelectedPatterns: [],
    extendedUserSelectedPatterns: [],
    userSelectedOb: [],
    atmPatterns: [],
    selectedAtmPatterns: [],
    atmPatternRecords: [],
    atmPatternTableRows: {},
  },

  // Define mutations for directly modifying the state
  mutations: {
    SET_ATM_WIZARD_TABS(state, value) {
      state.atmWizardTabs = value
    },
    SET_ATM_ACCORDION_OPTIONS(state, value) {
      state.atmAccordionOptions = value
    },
    SET_ATM_CONFIG(state, value) {
      state.atmConfig = value
    },
    SET_CHUNK_LINE_RECORDS(state, value) {
      state.chunkLineRecords = value
    },
    SET_USER_SELECTED_PATTERNS(state, value) {
      state.userSelectedPatterns = value
    },
    SET_EXTENDED_USER_SELECTED_PATTERNS(state, value) {
      state.extendedUserSelectedPatterns = value
    },
    SET_USER_SELECTED_OB(state, value) {
      state.userSelectedOb = value
    },
    SET_ATM_PATTERNS(state, value) {
      state.atmPatterns = value
    },
    SET_SELECTED_ATM_PATTERNS(state, value) {
      state.selectedAtmPatterns = value
    },
    SET_ATM_PATTERN_RECORDS(state, value) {
      state.atmPatternRecords = value
    },
    SET_ATM_PATTERN_TABLE_ROWS(state, value) {
      state.atmPatternTableRows = value
    },
  },

  // Define actions for asynchronous or complex state modifications
  actions: {
    async fetchAtmChunkData({ rootGetters, commit }) {
      try {
        // Fetch ATM chunk data from the server using batch ID and selected definition version
        const res = await axios.post('/pipeline/atm_chunk_data/', {
          batch_id: rootGetters['batch/batch'].id, // Batch ID from root getter
          definition_version: rootGetters['dataView/selectedDefinitionVersion'], // Selected definition version from root getter
        })

        // Commit the fetched chunk line records to the state
        commit('SET_CHUNK_LINE_RECORDS', res?.data?.data || [])
      } catch (error) {
        // Handle and throw errors if the request fails
        const message = error?.response?.data?.detail || 'Error fetching atm chunk data'
        throw new Error(message)
      }
    },

    findAtmPatterns({ rootGetters, commit, state }) {
      // Set the loading state to true before processing
      commit('dataView/SET_LOADING', true, { root: true })

      // Reset ATM patterns, pattern records, and selected patterns
      commit('SET_ATM_PATTERNS', [])
      commit('SET_ATM_PATTERN_RECORDS', [])
      commit('SET_SELECTED_ATM_PATTERNS', [])

      // Get the required data from root getters and state
      const selectedDefinition = rootGetters['dataView/selectedDefinition']
      const selectedTableName = rootGetters['dataView/selectedTableName']
      const multipleLineRecord = rootGetters['dataView/modelMultipleLineRecord']
      const { table_unique_id } = rootGetters['dataView/table'].find(table => table.table_name === selectedTableName)
      const selectedBatchId = rootGetters['batch/batch'].id
      const extendedUserSelectedPatterns = state.extendedUserSelectedPatterns.filter(e => e.length)

      // Prepare the payload with all necessary data
      const payload = {
        definition_id: selectedDefinition.definition_id,
        definition_type: selectedDefinition.type,
        name_matching_text: selectedDefinition.name_matching_text,
        batch_id: selectedBatchId,
        table_unique_id,
        record_line: state.atmConfig.record_line.value,
        digit_threshold: state.atmConfig.digit_threshold.value,
        text_threshold: state.atmConfig.text_threshold.value,
        user_selected_patterns: state.userSelectedPatterns.map(e => e.pattern),
        extended_user_selected_patterns: extendedUserSelectedPatterns.map(e => e.map(i => i.pattern)),
        multiple_line_record: multipleLineRecord,
        user_selected_ob: state.userSelectedOb,
        definition_version: rootGetters['dataView/selectedDefinitionVersion'],
      }

      // Send the data to the server for ATM pattern processing
      axios.post('/pipeline/process_atm_data/', payload).catch(() => {
        // Reset the loading state if the request fails
        commit('dataView/SET_LOADING', false, { root: true })
      })
    },

    loadAtmPatterns({ state, commit }, data) {
      // Check if data exists, otherwise stop loading
      if (!data) {
        commit('dataView/SET_LOADING', false, { root: true })
        return
      }

      // If patterns and pattern records exist, update the state
      if (data.atm_patterns && data.atm_pattern_records && state.atmWizardTabs.results.active) {
        commit('SET_ATM_PATTERNS', data.atm_patterns)
        commit('SET_ATM_PATTERN_RECORDS', data.atm_pattern_records)

        // Stop the loading state
        commit('dataView/SET_LOADING', false, { root: true })
      }
    },

    async runTest({ rootGetters, commit }) {
      // Set the loading state to true before processing
      commit('dataView/SET_LOADING', true, { root: true })

      // Gather necessary parameters for the test
      const batch = rootGetters['batch/batch']
      const selectedDefinitionVersion = rootGetters['dataView/selectedDefinitionVersion']

      const params = {
        batch_id: batch.id,
        skip_post_processor: false,
        skip_key_processing: true,
        skip_table_processing: false,
        definition_version: selectedDefinitionVersion,
      }

      const currentRouteName = rootGetters['app/currentRouteName']

      // If the current route is 'template-batch', add template parameter
      if (currentRouteName === 'template-batch') {
        params.template = batch.definitionId
      }

      await axios.post('/pipeline/process_batch/', null, {
        params,
      }).then(res => {
        // Display a success message upon completion
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
      }).catch(error => {
        const message = error?.response?.data?.detail || 'Something went wrong'
        // Display an error message if the request fails
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      })

      // commit('dataView/SET_LOADING', false, { root: true })
    },

    async refreshUserSelectedPatterns({ rootGetters, dispatch, commit }) {
      // Retrieve user-selected patterns from root getters
      const userSelectedPatterns = rootGetters['dataView/modelUserSelectedPatterns']

      // Update chunk line records for each selected pattern
      userSelectedPatterns.forEach(async e => {
        const pos = e.pos.split(',')

        pos[8] = 'blank' // Modify position data

        await dispatch('updateChunkLineRecords', pos.join(','))
      })

      // Update the state with the refreshed patterns
      commit('SET_USER_SELECTED_PATTERNS', userSelectedPatterns)
    },

    async refreshExtendUserSelectedPatterns({ rootGetters, dispatch, commit }) {
      // Retrieve extended user-selected patterns from root getters
      const extendedUserSelectedPatterns = rootGetters['dataView/modelExtendedUserSelectedPatterns']

      // Update chunk line records for each pattern in the extended patterns
      extendedUserSelectedPatterns.forEach(item => {
        item.forEach(async e => {
          const pos = e.pos.split(',')

          pos[8] = 'blank' // Modify position data

          await dispatch('updateChunkLineRecords', pos.join(','))
        })
      })

      // Update the state with the refreshed extended patterns
      commit('SET_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
    },
    async refreshUserSelectedOb({ rootGetters, commit }) {
      // Fetch the user-selected object from root getters
      const modelUserSelectedOb = rootGetters['dataView/modelUserSelectedOb']

      // Commit the fetched user-selected object to the state
      commit('SET_USER_SELECTED_OB', modelUserSelectedOb)
    },

    async resetChunkLineRecords({ state, commit }) {
      // Initialize a new array for resetting chunk line records
      const chunkLineRecords = []

      // Loop through each record in the current state
      state.chunkLineRecords.forEach(e => {
        const pos = e.split(',')

        // Reset the specific position in the record to 'blank'
        pos[8] = 'blank'

        // Rebuild the record and add it to the new array
        chunkLineRecords.push(pos.join(','))
      })

      // Commit the updated chunk line records to the state
      commit('SET_CHUNK_LINE_RECORDS', chunkLineRecords)
    },

    async updateChunkLineRecords({ state, commit }, posRef) {
      // Find the index of the specified record in the chunk line records
      const index = state.chunkLineRecords.indexOf(posRef)

      // If the record doesn't exist, return null
      if (index === -1) {
        return null
      }

      // Create a copy of the chunk line records for mutation
      const chunkLineRecords = [...state.chunkLineRecords]

      // Split the record into parts for modification
      const pos = posRef.split(',')

      // Toggle the status between 'blank' and 'green'
      pos[8] = pos[8] === 'blank' ? 'green' : 'blank'

      // Remove the old record and add the updated one
      chunkLineRecords.splice(index, 1)
      chunkLineRecords.push(pos.join(','))

      // Commit the updated records to the state
      commit('SET_CHUNK_LINE_RECORDS', chunkLineRecords)

      // Return the updated position for further use
      return pos
    },

    generateAtmPatternTableRows({ state, commit }) {
      // Set the loading state to true before processing
      commit('dataView/SET_LOADING', true, { root: true })

      // Reset the ATM pattern table rows
      commit('SET_ATM_PATTERN_TABLE_ROWS', {})

      // If there are no ATM patterns, stop processing
      if (!state.atmPatterns.length) {
        return
      }

      // Initialize variables for processing patterns
      const selectedAtmPatterns = [...state.selectedAtmPatterns]
      const updateStatusList = []
      const autoSelectedAtmPatterns = []
      const rows = {}

      // Iterate through all ATM patterns
      state.atmPatterns.forEach(value => {
        const pos = [...value.pos]
        let { openBlock } = value
        const index = selectedAtmPatterns.map(e => e.pattern).indexOf(value.pattern)

        // Update openBlock and status list for selected patterns
        if (index !== -1) {
          openBlock = selectedAtmPatterns[index].multiLine === 'true' || openBlock
          updateStatusList.push([...pos])
          selectedAtmPatterns.splice(index, 1)
        }

        const status = pos[8]

        // Determine if the pattern should be marked as checked
        const checked = index !== -1 || status === 'green'

        if (index === -1 && checked) {
          updateStatusList.push([...pos])
        }

        if (index === -1 && status === 'green') {
          autoSelectedAtmPatterns.push({ ...value })
        }

        // Build the updated value for the pattern
        const updatedValue = {
          ...value,
          pos,
          openBlock,
          checked: index !== -1 || status === 'green',
          nitb: false,
        }

        // Group patterns by their status in rows
        if (rows[status]?.length) {
          rows[status].push(updatedValue)
        } else {
          rows[status] = [updatedValue]
        }
      })

      // Emit events to update the status and selection of ATM patterns
      updateStatusList.forEach(pos => {
        bus.$emit('atm/updateStatus', { posRef: pos[7], autoChecked: true })
      })

      autoSelectedAtmPatterns.forEach(data => {
        bus.$emit('atm/updateSelectedAtmPattern', data)
      })

      // Commit the updated rows to the state
      commit('SET_ATM_PATTERN_TABLE_ROWS', rows)

      // Reset the loading state
      commit('dataView/SET_LOADING', false, { root: true })
    },

    resetAtmWizardTabs({ state, commit }) {
      // Create a copy of the ATM wizard tabs state
      const atmWizardTabs = { ...state.atmWizardTabs }

      // Reset the active state for each tab
      Object.keys(atmWizardTabs).forEach(key => {
        if (key === 'tableRowSelection') {
          atmWizardTabs[key].active = true
        } else {
          atmWizardTabs[key].active = false
        }
      })

      // Commit the updated tabs to the state
      commit('SET_ATM_WIZARD_TABS', atmWizardTabs)
    },

    resetStatusList({ state, commit }) {
      // Create a copy of the accordion options state
      const atmAccordionOptions = [...state.atmAccordionOptions]

      // Reset the visibility of each option
      atmAccordionOptions.forEach((_, index) => {
        atmAccordionOptions[index].visible = false
      })

      // Commit the updated accordion options to the state
      commit('SET_ATM_ACCORDION_OPTIONS', atmAccordionOptions)
    },

    reset({ rootGetters, commit, dispatch }) {
      // Fetch the table settings from root getters
      const tableSettings = rootGetters['applicationSettings/tableSettings']

      // Reset all relevant state properties
      commit('SET_ATM_CONFIG', tableSettings?.automatedTableModelConfig)
      commit('SET_CHUNK_LINE_RECORDS', [])
      commit('SET_USER_SELECTED_PATTERNS', [])
      commit('SET_EXTENDED_USER_SELECTED_PATTERNS', [])
      commit('SET_ATM_PATTERNS', [])
      commit('SET_SELECTED_ATM_PATTERNS', [])
      commit('SET_ATM_PATTERN_RECORDS', [])
      commit('SET_ATM_PATTERN_TABLE_ROWS', {})

      // Dispatch actions to reset wizard tabs and status lists
      dispatch('resetAtmWizardTabs')
      dispatch('resetStatusList')
    },
  },
  getters: {
    atmWizardTabs(state) {
      return state.atmWizardTabs
    },
    atmAccordionOptions(state) {
      return state.atmAccordionOptions
    },
    atmConfig(state) {
      return state.atmConfig
    },
    chunkLineRecords(state) {
      return state.chunkLineRecords
    },
    userSelectedPatterns(state) {
      return state.userSelectedPatterns
    },
    extendedUserSelectedPatterns(state) {
      return state.extendedUserSelectedPatterns
    },
    userSelectedOb(state) {
      return state.userSelectedOb
    },
    atmPatterns(state) {
      return state.atmPatterns
    },
    selectedAtmPatterns(state) {
      return state.selectedAtmPatterns
    },
    atmPatternRecords(state) {
      return state.atmPatternRecords
    },
    atmPatternTableRows(state) {
      return state.atmPatternTableRows
    },
  },
}
