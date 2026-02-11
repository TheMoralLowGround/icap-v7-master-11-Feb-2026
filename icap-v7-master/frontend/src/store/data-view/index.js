/**
 * Organization: AIDocbuilder Inc.
 * File: batch/index.js
 * Version: 6.0
 *
 * Authors:
 *   - Vinay: Initial implementation
 *   - Ali: Code optimization
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   This file serves as the Vuex store module for managing view toolbar related data in the application.
 *
 * Dependencies:
 *   - `axios`: For performing HTTP requests to fetch and save settings.
 *   - Custom web socket
 *   - Helper functions
 *
 * Main Features:
 *   - Define the default state and initialize its values.
 *   - Implement mutations and getters for state management.
 *   - Write action methods to handle asynchronous operations.
 *   - Integrate and bind APIs for view toolbar related data.
 */

import Vue from 'vue'
import { cloneDeep } from 'lodash'
import axios from 'axios'
import WS from '@/utils/ws'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import {
  getNewTable, getDefinitionKey, vendorDefinition, findTableIndexByName,
} from './helper'

export default {
  // Enable Vuex module namespacing for modular state management
  namespaced: true,
  // Define the state to hold various data
  state: {
    defaultModes: {
      keySettings: 'key-items',
      tableSettings: 'table-models',
      chunkData: 'chunk-data',
      automatedTableModel: 'automated-table-model',
      verification: 'verification',
      definedKeys: 'defined-keys',
    },
    mainMode: '',
    mode: '',
    allDefinitions: [],
    typesByDefinition: [],
    batchesByDefinitionType: [],
    selectedDefinition: null,
    dJsonTableList: [],
    selectedTableId: 0,
    selectedTableName: '',
    displayNotInUseFields: true,
    keyRuleItem: null,
    keyRuleItemEditIndex: -1,
    tableRuleItem: null,
    tableRuleItemEditIndex: -1,
    keyLookupItem: null,
    keyLookupItemEditIndex: -1,
    loading: false,
    loadingError: null,
    selectedDefinitionVersion: null,
    cellRangePermission: null,
    tableLookupItem: null,
    tableLookupItemEditIndex: -1,
    tableFields: [],
    routeId: null,
    isAutoExtracted: false,
    changeDefinotinVersion: false,
    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // duplicatePromptKeys: [], // Store duplicate key information for highlighting
  },
  // Define mutations for directly modifying the state
  mutations: {

    SET_SELECTED_TABLE_NAME(state, tableName) {
      if (tableName) {
        state.selectedTableName = tableName
      } else if (
        state.selectedDefinition
    && Array.isArray(state.selectedDefinition.table)
    && state.selectedDefinition.table.length > 0
    && state.selectedDefinition.table[0].table_name
      ) {
        const defaultTableName = state.selectedDefinition.table[0].table_name
        state.selectedTableName = defaultTableName
      } else {
        state.selectedTableName = ''
      }
    },

    SET_SELECTED_TABLE_ID(state, tableName) {
      state.selectedTableName = tableName
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedTableId = tableIndex
      } else {
        state.selectedTableId = 0 // Fallback to first table for backward compatibility
      }
    },
    SET_SELECTED_TABLE_BY_ID(state, tableId) {
      state.selectedTableId = tableId
      if (state.selectedDefinition?.table?.[tableId]) {
        state.selectedTableName = state.selectedDefinition.table[tableId].table_name
      }
    },
    SET_MODEL_AUTO_PATTERNS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models.autoPatterns = value
      }
    },

    SET_MODEL_USER_SELECTED_PATTERNS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models.userSelectedPatterns = value
      }
    },

    SET_MODEL_EXTENDED_USER_SELECTED_PATTERNS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models.extendedUserSelectedPatterns = value
      }
    },

    SET_MODEL_USER_SELECTED_OB(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models.userSelectedOb = value
      }
    },

    SET_MODEL_MULTIPLE_LINE_RECORD(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models.multipleLineRecord = value
      }
    },

    SET_MODEL_AUTO_TYPE(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models.type = value
      }
    },

    SET_TABLE_MODELS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.models = value
      }
    },

    SET_TABLE_COLUMNS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.columns = value
      }
    },

    SET_TABLE_KEY_ITEMS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.keyItems = value
      }
    },

    SET_TABLE_COLUMN_PROMPTS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.columnPrompts = value
      }
    },

    SET_TABLE_RULE_ITEMS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.ruleItems = value
      }
    },

    SET_TABLE_NORMALIZER_ITEMS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.normalizerItems = value
      }
    },
    SET_ROUTE_ID(state, id) {
      state.routeId = id
    },
    SET_MAIN_MODE(state, value) {
      state.mainMode = value
    },
    SET_MODE(state, value) {
      state.mode = value
    },
    SET_ALL_DEFINITIONS(state, value) {
      state.allDefinitions = value
    },
    SET_TYPES_BY_DEFINITION(state, value) {
      state.typesByDefinition = value
    },
    SET_BATCHES_BY_DEFINITION_TYPE(state, value) {
      state.batchesByDefinitionType = value
    },
    SET_SELECTED_DEFINITION(state, value) {
      state.selectedDefinition = value
    },
    SET_D_JSON_TABLE_LIST(state, value) {
      state.dJsonTableList = value
    },

    SET_KEY_MODELS(state, value) {
      state.selectedDefinition.key.models = value
    },
    SET_KEY_ITEMS(state, value) {
      state.selectedDefinition.key.items = value
    },
    SET_KEY_RULE_ITEMS(state, value) {
      state.selectedDefinition.key.ruleItems = value
    },
    SET_KEY_NOT_IN_USE_ITEMS(state, value) {
      state.selectedDefinition.key.notInUseItems = value
    },
    SET_KEY_LOOKUP_ITEMS(state, value) {
      state.selectedDefinition.key.lookupItems = value
    },
    SET_DISPLAY_NOT_IN_USE_FIELDS(state, value) {
      state.displayNotInUseFields = value
    },
    SET_KEY_RULE_ITEM(state, value) {
      state.keyRuleItem = value
    },
    SET_KEY_RULE_ITEM_EDIT_INDEX(state, value) {
      state.keyRuleItemEditIndex = value
    },
    SET_KEY_RULE_ITEM_RULES(state, value) {
      state.keyRuleItem.rules = value
    },
    SET_TABLE_RULE_ITEM(state, value) {
      state.tableRuleItem = value
    },
    SET_TABLE_RULE_ITEM_EDIT_INDEX(state, value) {
      state.tableRuleItemEditIndex = value
    },
    SET_TABLE_RULE_ITEM_RULES(state, value) {
      state.tableRuleItem.rules = value
    },
    SET_KEY_LOOKUP_ITEM(state, value) {
      state.keyLookupItem = value
    },
    SET_KEY_LOOKUP_ITEM_EDIT_INDEX(state, value) {
      state.keyLookupItemEditIndex = value
    },
    SET_KEY_LOOKUP_ITEM_QUERIES(state, value) {
      state.keyLookupItem.queries = value
    },
    SET_TABLE_LOOKUP_ITEMS(state, value) {
      const tableIndex = findTableIndexByName(state.selectedDefinition.table, state.selectedTableName)
      if (tableIndex !== -1) {
        state.selectedDefinition.table[tableIndex].table_definition_data.lookupItems = value
      }
    },
    SET_TABLE_LOOKUP_ITEM(state, value) {
      state.tableLookupItem = value
    },
    SET_TABLE_LOOKUP_ITEM_EDIT_INDEX(state, value) {
      state.tableLookupItemEditIndex = value
    },
    SET_TABLE_LOOKUP_ITEM_QUERIES(state, value) {
      state.tableLookupItem.queries = value
    },
    SET_LOADING(state, value) {
      state.loading = value
    },
    SET_LOADING_ERROR(state, value) {
      state.loadingError = value
    },
    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // SET_DUPLICATE_PROMPT_KEYS(state, value) {
    //   state.duplicatePromptKeys = value
    // },
    SET_SELECTED_DEFINITION_VERSION(state, value) {
      state.selectedDefinitionVersion = value
    },
    SET_CELL_RANGE_PERMISSION(state, value) {
      state.cellRangePermission = value
    },
    SET_TABLE_FIELDS(state, value) {
      state.tableFields = value
    },
    AUTO_EXTRACTED_KEY(state, value) {
      state.isAutoExtracted = value
    },
    IS_CHANGE_DEFINITION_VERSION(state, value) {
      state.changeDefinotinVersion = value
    },
  },
  actions: {

    // Asynchronous action to set the D JSON table list based on the selected document
    async setDJsonTableList({ rootGetters, commit }) {
      // Retrieve verification details and selected document ID from root getters
      const verificationDetails = rootGetters['batch/verificationDetails']
      const selectedDocumentId = rootGetters['batch/selectedDocumentId']

      // Construct the batch ID by extracting parts from the selected document ID
      const batchId = `${selectedDocumentId.split('.')[0]}.${selectedDocumentId.split('.')[1]}`
      // Find the batch object that matches the batchId
      const batch = verificationDetails.find(e => e.id === batchId)
      // Find the specific document data related to the selected document ID
      const documentData = batch.data_json.nodes.find(e => e.id === selectedDocumentId)

      // Initialize an empty list to hold the tables
      const dJsonTableList = []

      // If document data exists, loop through its children and find tables
      if (documentData) {
        documentData.children.forEach(e => {
          if (e.type === 'table') {
            dJsonTableList.push({
              table_id: e.table_id, // Capture the table id
              table_name: e.table_name, // Capture the table name
              table_unique_id: e.table_unique_id, // Capture the table unique ID
            })
          }
        })
      }

      // Sort the table list by table_id in ascending order
      // dJsonTableList.sort((a, b) => a.table_id - b.table_id)
      dJsonTableList.sort()

      // Commit the sorted table list to the store
      commit('SET_D_JSON_TABLE_LIST', dJsonTableList)
    },

    // Action to fetch all definitions based on selected project countries
    async fetchAllDefinitions({ rootGetters, commit, state }) {
      // Prevent fetching again if all definitions are already loaded
      if (state.allDefinitions.length) {
        return
      }

      try {
        // Get the selected project countries from the store
        const selectedProjectCountries = rootGetters['auth/selectedProjectCountries']
        const result = {}

        // Group projects by country code
        selectedProjectCountries.forEach(e => {
          const { countryCode, project } = e

          if (!result[countryCode]) {
            result[countryCode] = []
          }

          if (!result[countryCode].includes(project)) {
            result[countryCode].push(project)
          }
        })

        // Send a request to get all definitions based on the country and project grouping
        const res = await axios.post('/all_definitions/', {
          project_countries: result,
        })

        // Commit the fetched definitions to the store
        commit('SET_ALL_DEFINITIONS', res.data)
      } catch (error) {
        // If there's an error, throw a new error with a meaningful message
        const err = error?.response?.data?.detail || 'Fetching all Definitions'
        throw new Error(err)
      }
    },

    // Action to fetch selector data based on a specific batch
    async fetchSelectorDataByBatch({ state, dispatch }, payload) {
      const data = {
        definitionId: payload.profile,
        definitionType: payload.type || 'Booking Request',
        batchType: localStorage.getItem('batch-type'),
        batchId: state.routeId,
      }

      // If necessary data isn't loaded yet, dispatch actions to fetch required data
      if (!state.batchesByDefinitionType.length) {
        await dispatch('fetchBatchesByDefinitionType', data)
      }
    },

    // Action to fetch types by definition ID
    async fetchTypesByDefinition({ commit }, definitionId) {
      try {
        // Send a request to fetch types based on the provided definition ID
        const res = await axios.get('/get_types_by_definition/', {
          params: {
            definition_id: definitionId,
          },
        })

        // Commit the fetched types to the store after sorting them
        commit('SET_TYPES_BY_DEFINITION', res.data.sort())
      } catch (error) {
        // If an error occurs, commit an error and stop loading
        const err = error?.response?.data?.detail || 'Error fetching types by definition'
        commit('batch/SET_ERROR', err, { root: true })
        commit('SET_LOADING', false)
      }
    },

    // Action to fetch batches by definition type
    async fetchBatchesByDefinitionType({ commit }, payload) {
      try {
        // Send a request to fetch batches based on definition ID and type
        const res = await axios.get('/get_batches_by_definition_type/', {
          params: {
            definition_id: payload.definitionId,
            definition_type: payload.definitionType,
            batch_type: payload.batchType,
            batch_id: payload.batchId,
          },
        })

        // Commit the fetched batches to the store after sorting them
        commit('SET_BATCHES_BY_DEFINITION_TYPE', res.data.sort())
      } catch (error) {
        // If an error occurs, commit an error and stop loading
        const err = error?.response?.data?.detail || 'Error fetching batches'
        commit('batch/SET_ERROR', err, { root: true })
        commit('SET_LOADING', false)
      }
    },

    // Action to fetch a specific definition based on the current route
    async fetchDefinition({
      dispatch, rootGetters, state,
    }, currentRouteName) {
      let url = ''
      let params = {}
      // Determine the URL and parameters based on the current route name
      const batch = rootGetters['batch/batch']
      const selectedDocument = rootGetters['batch/selectedDocument']
      const raJsonDocumentData = rootGetters['batch/documentData']
      if (currentRouteName === 'template-batch') {
        url = '/dashboard/get_template_definition/'
        params = {
          template_name: batch.definitionId,
          definition_version: state.selectedDefinitionVersion,
        }
      } else {
        url = '/search_definition/'
        params = {
          definition_id: batch.definitionId,
          type: batch.type,
          name_matching_text: batch.nameMatchingText,
          definition_version: state.selectedDefinitionVersion,
          vendor_name: selectedDocument.vendor || batch.vendor,
          layout_id: raJsonDocumentData.pages[0]?.layout_id || selectedDocument.layoutId,
        }
      }
      // Send a request to fetch the definition
      try {
        const res = await axios.get(url, {
          params,
        })
        await dispatch('setSelectedDefinition', res.data)
      } catch (error) {
        // If an error occurs, throw a new error with a meaningful message
        // const err = error?.response?.data?.detail || 'Fetching Definition'
        const tables = rootGetters['batch/selectedDocument']?.tables || []
        const tableSettings = rootGetters['applicationSettings/tableSettings']
        const definition = vendorDefinition(tables, tableSettings)
        await dispatch('setSelectedDefinition', definition)
        // throw new Error(err)
      }

      // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
      // After setting definition (which only has definition keys), merge in prompt keys
      // This ensures prompt keys are always visible regardless of which batch/document is selected
      // dispatch('mergePromptKeysIntoDefinition')
    },
    // Action to set the selected definition in the store
    setSelectedDefinition({
      rootGetters, commit, state, dispatch,
    }, data) {
      let definition = data

      // If the definition exists, process the tables and update the models
      if (definition != null) {
        commit('SET_CELL_RANGE_PERMISSION', definition.key?.cell_range_permission)

        const tableSettings = rootGetters['applicationSettings/tableSettings']
        let table

        if (Array.isArray(data?.table) && data.table.length) {
          table = data.table

          table.forEach((item, index) => {
            // If the table doesn't have models, generate new ones
            if (Object.keys(item.table_definition_data.models).length === 0) {
              const newTable = getNewTable(tableSettings)
              table[index].table_definition_data.models = newTable.table_definition_data.models
            } else if (!('autoPatterns' in item.table_definition_data.models)) {
              // Ensure 'autoPatterns' exists in the model
              table[index].table_definition_data.models.autoPatterns = []
            }
          })
        } else {
          // If no table is defined, create a new table
          table = [getNewTable(tableSettings)]
        }

        // Add key information to the definition
        definition = {
          ...data,
          table,
          key: getDefinitionKey(data),
        }
      }

      // Commit the selected definition to the store
      commit('SET_SELECTED_DEFINITION', definition)

      // Note: We don't merge prompt keys here because they will be fetched and merged
      // separately via getPromptKeys action (which is called after this in most flows)

      if ((!state.selectedTableName && definition?.table?.length) || (state.changeDefinotinVersion && definition?.table?.length)) {
        const firstTableName = definition.table[0].table_name
        commit('SET_SELECTED_TABLE_NAME', firstTableName)
        commit('SET_SELECTED_TABLE_ID', firstTableName)
      }
      commit('IS_CHANGE_DEFINITION_VERSION', false)
      // Refresh data for rule and lookup screens if necessary
      if (definition && state.keyRuleItemEditIndex !== -1) {
        dispatch('setKeyRuleItemByIndex', state.keyRuleItemEditIndex)
      }
      if (definition && state.tableRuleItemEditIndex !== -1) {
        dispatch('setTableRuleItemByIndex', state.tableRuleItemEditIndex)
      }
      if (definition && state.keyLookupItemEditIndex !== -1) {
        dispatch('setKeyLookupItemByIndex', state.keyLookupItemEditIndex)
      }
      if (definition && state.tableLookupItemEditIndex !== -1) {
        dispatch('setTableLookupItemByIndex', state.tableLookupItemEditIndex)
      }
    },

    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // Action to merge prompt keys from profile store into definition's key.items
    // This ensures prompt keys are always displayed in the UI alongside definition keys
    // mergePromptKeysIntoDefinition({ state, rootGetters, commit }) {
    //   // Skip if no definition is loaded
    //   if (!state.selectedDefinition?.key?.items) return

    //   // Get current definition keys (filter out any existing prompt keys to avoid duplicates)
    //   const definitionKeys = state.selectedDefinition.key.items.filter(item => item.type !== 'prompt')

    //   // Get prompt keys from profile store (clone to avoid reference issues)
    //   const promptKeys = cloneDeep(rootGetters['profile/promptKeys'] || [])

    //   // Merge them together
    //   const mergedKeys = [...definitionKeys, ...promptKeys]

    //   // Deduplicate by ID (in case of any race conditions or double-adds)
    //   const seenIds = new Set()
    //   const deduplicatedKeys = mergedKeys.reduce((acc, key) => {
    //     if (!seenIds.has(key.id)) {
    //       seenIds.add(key.id)
    //       acc.push(key)
    //     }
    //     return acc
    //   }, [])

    //   // Update the store with merged and deduplicated keys
    //   commit('SET_KEY_ITEMS', deduplicatedKeys)
    // },

    // Action to handle changes in the definition
    async onChangeDefinition({ rootGetters, dispatch, commit }, definitionId) {
      commit('SET_LOADING', true)

      // Get the selected project countries from the store
      const selectedProjectCountries = rootGetters['auth/selectedProjectCountries']
      const result = {}

      // Group projects by country code
      selectedProjectCountries.forEach(e => {
        const { countryCode, project } = e

        if (!result[countryCode]) {
          result[countryCode] = []
        }

        if (!result[countryCode].includes(project)) {
          result[countryCode].push(project)
        }
      })

      // Request the latest batch information based on the definition ID and project countries
      const res = await axios.post('/latest_batch_info/', {
        definition_id: definitionId,
        project_countries: result,
      })

      // If no batch is available, show an error message and stop loading
      if (!res.data.batch_id) {
        commit('SET_LOADING', false)

        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: `No batch available for this "${definitionId}" profile`,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        return
      }

      // Reset and fetch new types and batches based on the selected definition
      commit('SET_BATCHES_BY_DEFINITION_TYPE', [])
      await dispatch('atm/reset', null, { root: true })

      await dispatch('fetchTypesByDefinition', definitionId)
      await dispatch('onChangeBatch', { batchId: res.data.batch_id, refresh: true })

      commit('SET_LOADING', false)
    },

    // Action to handle changes in the definition type
    async onChangeDefinitionType({ state, dispatch, commit }, definitionType) {
      commit('SET_LOADING', true)

      // Get the definition ID and existing batches by definition type
      const definitionId = state.selectedDefinition.definition_id
      const batchesByDefinitionType = [...state.batchesByDefinitionType]
      const batchType = localStorage.getItem('batch-type')
      const batchId = state.routeId

      // Fetch batches based on the definition ID and type
      await dispatch('fetchBatchesByDefinitionType',
        {
          definitionId,
          definitionType,
          batchType,
          batchId,
        })

      // If no batches are found, reset the batches and show an error message
      if (!state.batchesByDefinitionType.length) {
        commit('SET_BATCHES_BY_DEFINITION_TYPE', batchesByDefinitionType)
        commit('SET_LOADING', false)

        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: `No batch available for this "${definitionId} - ${definitionType}" profile`,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        return
      }

      // Reset the ATM data and change the batch
      await dispatch('atm/reset', null, { root: true })

      const [selectedBatch] = state.batchesByDefinitionType

      await dispatch('changeBatch', { batchId: selectedBatch, refresh: true })

      commit('SET_LOADING', false)
    },
    // Action to handle the change of batch with specific payload
    async onChangeBatch({
      rootGetters, getters, dispatch, commit, state,
    }, payload) {
      // Set loading state to true to indicate a data fetch operation is ongoing
      commit('SET_LOADING', true)

      try {
        // Commit the selected table ID to the store
        commit('SET_SELECTED_TABLE_ID', state.selectedTableName)
        commit('SET_SELECTED_TABLE_NAME', state.selectedTableName)

        // Leave the current batch status room on WebSocket
        WS.leaveRoom(`batch_status_${rootGetters['batch/batch'].id}`)

        // Fetch the batch data from the server based on the batch ID provided in the payload
        await dispatch('batch/fetchBatch', {
          selectedTransaction: payload.batchId,
          selectFirstDocument: true,
        }, { root: true })

        // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
        // Fetch prompt keys after transaction is loaded

        // If the refresh flag is true, fetch the associated definition data
        // Note: fetchDefinition automatically merges prompt keys after fetching
        if (payload.refresh) {
          await dispatch('fetchDefinition')
        }

        // Get the current route name to determine further actions
        const currentRouteName = rootGetters['app/currentRouteName']

        // If not in 'template-batch' view, fetch ATM chunk data
        if (currentRouteName !== 'template-batch') {
          await dispatch('atm/fetchAtmChunkData', null, { root: true })
        }

        // Depending on model configuration, refresh user-selected patterns
        if (getters.modelMultipleLineRecord) {
          await dispatch('atm/refreshExtendUserSelectedPatterns', null, { root: true })
        } else {
          await dispatch('atm/refreshUserSelectedPatterns', null, { root: true })
        }

        // Refresh selected OB (object) patterns
        await dispatch('atm/refreshUserSelectedOb', null, { root: true })

        // If the batch view is 'chunk-data', load chunk data
        if (rootGetters['batch/view'] === 'chunk-data') {
          await dispatch('batch/loadChunkData', null, { root: true })
          await dispatch('batch/loadChunkDataWithPlainText', null, { root: true })
        }

        // Rejoin the batch status room on WebSocket for real-time updates
        WS.joinRoom(`batch_status_${payload.batchId}`)

        // Set loading state to false as the operations are complete
        commit('SET_LOADING', false)
      } catch (error) {
        // If an error occurs, commit the error and stop the loading state
        commit('batch/SET_ERROR', error, { root: true })
        commit('SET_LOADING', false)
      }
    },

    // Action to reset the state by clearing various pieces of data
    reset({ commit, dispatch }) {
      // Reset all necessary states related to the batch, mode, definitions, etc.
      commit('SET_MAIN_MODE', '')
      commit('SET_MODE', '')
      commit('SET_ALL_DEFINITIONS', [])
      commit('SET_TYPES_BY_DEFINITION', [])
      commit('SET_BATCHES_BY_DEFINITION_TYPE', [])
      commit('SET_SELECTED_DEFINITION', null)
      // commit('SET_SELECTED_TABLE_ID', 0)
      commit('SET_SELECTED_TABLE_NAME', '')
      commit('SET_DISPLAY_NOT_IN_USE_FIELDS', true)
      commit('SET_KEY_RULE_ITEM', null)
      commit('SET_LOADING', false)
      commit('SET_LOADING_ERROR', null)
      commit('SET_KEY_RULE_ITEM_EDIT_INDEX', -1)
      commit('SET_TABLE_RULE_ITEM', null)
      commit('SET_TABLE_RULE_ITEM_EDIT_INDEX', -1)
      commit('SET_SELECTED_DEFINITION_VERSION', null)
      commit('SET_KEY_LOOKUP_ITEM', null)
      commit('SET_KEY_LOOKUP_ITEM_EDIT_INDEX', -1)
      commit('SET_TABLE_LOOKUP_ITEM', null)
      commit('SET_TABLE_LOOKUP_ITEM_EDIT_INDEX', -1)
      commit('AUTO_EXTRACTED_KEY', false)
      commit('IS_CHANGE_DEFINITION_VERSION', false)

      // Reset ATM-specific data
      dispatch('atm/reset', null, { root: true })
    },

    // Action to select the first mode based on the current batch view
    async selectFirstMode({ rootGetters, dispatch }) {
      const batchView = rootGetters['batch/view']

      let mainMode = ''

      // Set the main mode based on the current batch view
      if (batchView === 'key') {
        mainMode = 'keySettings'
      } else if (batchView === 'table') {
        mainMode = 'tableSettings'
      } else if (batchView === 'chunk-data') {
        mainMode = 'chunkData'
      } else if (batchView === 'analyzer') {
        mainMode = 'automatedTableModel'
      }

      // Dispatch action to set the main mode
      await dispatch('setMainMode', mainMode)
    },

    // Action to set the main mode and further set the associated mode
    async setMainMode({ commit, state, dispatch }, mainMode) {
      commit('SET_MAIN_MODE', mainMode)

      // Dispatch action to set the corresponding mode based on the main mode
      await dispatch('setMode', state.defaultModes[mainMode])
    },

    // Action to set the current mode and handle rules reset
    setMode({ commit, state }, mode) {
      // Commit the mode change
      commit('SET_MODE', mode)

      // Reset rule items if the mode is different from 'key-rules', 'table-rules', or 'key-lookup'
      if (mode !== 'key-rules' && state.keyRuleItem) {
        commit('SET_KEY_RULE_ITEM', null)
        commit('SET_KEY_RULE_ITEM_EDIT_INDEX', -1)
      }
      if (mode !== 'table-rules' && state.tableRuleItem) {
        commit('SET_TABLE_RULE_ITEM', null)
        commit('SET_TABLE_RULE_ITEM_EDIT_INDEX', -1)
      }
      if (mode !== 'key-lookup' && state.keyLookupItem) {
        commit('SET_KEY_LOOKUP_ITEM', null)
        commit('SET_KEY_LOOKUP_ITEM_EDIT_INDEX', -1)
      }
      if (mode !== 'table-lookup' && state.tableLookupItem) {
        commit('SET_TABLE_LOOKUP_ITEM', null)
        commit('SET_TABLE_LOOKUP_ITEM_EDIT_INDEX', -1)
      }
    },

    // Action to set a key rule item based on ID and keyId
    setKeyRuleItem({ commit, getters }, { id, keyId }) {
      let editIndex = -1
      const { keyRuleItems } = getters
      let record

      // Find the existing key rule item using the provided ID and keyId
      let keyRuleItemIndex = keyRuleItems.findIndex(keyRuleItem => keyRuleItem.id === id && keyRuleItem.keyId === keyId)
      if (keyRuleItemIndex !== -1) {
        record = cloneDeep(keyRuleItems[keyRuleItemIndex])
        editIndex = keyRuleItemIndex
      } else {
        // If not found, search for a key rule item with an unset keyId
        keyRuleItemIndex = keyRuleItems.findIndex(keyRuleItem => keyRuleItem.id === id && !keyRuleItem.keyId)
        if (keyRuleItemIndex !== -1) {
          record = cloneDeep(keyRuleItems[keyRuleItemIndex])
          record.keyId = keyId
          editIndex = keyRuleItemIndex
        } else {
          // If no matching rule found, create a new one
          record = {
            id,
            keyId,
            rules: [],
          }
        }
      }

      // Commit the edit index and the key rule item data to the store
      commit('SET_KEY_RULE_ITEM_EDIT_INDEX', editIndex)
      commit('SET_KEY_RULE_ITEM', record)
    },

    // Action to set the key rule item by index
    setKeyRuleItemByIndex({ commit, getters }, index) {
      commit('SET_KEY_RULE_ITEM_EDIT_INDEX', index)
      commit('SET_KEY_RULE_ITEM', cloneDeep(getters.keyRuleItems[index]))
    },

    // Action to save the key rule item after editing
    async saveKeyRuleItem({
      commit, state, getters, dispatch,
    }) {
      const keyRuleItems = cloneDeep(getters.keyRuleItems)
      const record = state.keyRuleItem
      const editIndex = state.keyRuleItemEditIndex

      // If the item is new and has rules, push it to the keyRuleItems list
      if (editIndex === -1 && record.rules.length) {
        keyRuleItems.push(record)
        commit('SET_KEY_RULE_ITEM_EDIT_INDEX', keyRuleItems.length - 1)
      }

      // If the item exists, update it in the list
      if (editIndex !== -1 && record.rules.length) {
        keyRuleItems[editIndex] = record
      }

      // If the item exists but has no rules, remove it from the list and change mode
      if (editIndex !== -1 && !record.rules.length) {
        await dispatch('setMode', 'key-rule-items')
        keyRuleItems.splice(editIndex, 1)
      }

      // Commit the updated list of key rule items
      commit('SET_KEY_RULE_ITEMS', keyRuleItems)
    },
    // Action to add a new table to the selected definition
    addTable({ rootGetters, commit, getters }, { tableName, tableId, isAuto = 'new' }) {
      const { selectedDefinition } = getters // Get the current selected definition
      const tableSettings = rootGetters['applicationSettings/tableSettings'] // Get table settings from root getters
      // Create a new table object based on the settings and table info
      const newTable = getNewTable(tableSettings, tableId, tableName, isAuto)

      // Push the new table into the selected definition's table list
      selectedDefinition.table.push(newTable)

      // Commit the updated selected definition to the store
      commit('SET_SELECTED_DEFINITION', getters.selectedDefinition)
    },

    // Action to rename an existing table within the selected definition
    renameTable({ commit, getters }, { tableName, tableId }) {
      const { selectedDefinition } = getters // Get the current selected definition

      // Update the name of the specified table using the tableId
      selectedDefinition.table[tableId].table_name = tableName

      // Commit the updated selected definition to the store
      commit('SET_SELECTED_DEFINITION', selectedDefinition)
    },

    // Action to delete a table from the selected definition
    deleteTable({ commit, getters }, { tableId }) {
      const { selectedDefinition } = getters // Get the current selected definition

      // Filter out the table with the specified tableId from the list of tables
      selectedDefinition.table = selectedDefinition.table.filter(i => i.table_id !== tableId)

      // Reassign the table_id of each remaining table to maintain a continuous index
      selectedDefinition.table.forEach((item, index) => {
        selectedDefinition.table[index].table_id = index
      })

      // Commit the updated selected definition to the store
      commit('SET_SELECTED_DEFINITION', selectedDefinition)
    },

    // Action to set or edit a table rule item based on the provided label
    setTableRuleItem({ commit, getters }, { label }) {
      let editIndex = -1
      // Get the list of table rule items
      const tableRuleItems = getters.tableRuleItems || [] // Ensure it is an array
      let record

      // Find an existing table rule item with the specified label
      const tableRuleItemIndex = tableRuleItems.findIndex(tableRuleItem => tableRuleItem.label === label)
      if (tableRuleItemIndex !== -1) {
        record = cloneDeep(tableRuleItems[tableRuleItemIndex]) // If found, clone the item
        editIndex = tableRuleItemIndex // Set the edit index
      } else {
        // If not found, create a new record for the rule item
        record = {
          label,
          rules: [],
        }
      }

      // Commit the edit index and the table rule item data to the store
      commit('SET_TABLE_RULE_ITEM_EDIT_INDEX', editIndex)
      commit('SET_TABLE_RULE_ITEM', record)
    },

    // Action to set a table rule item by its index
    setTableRuleItemByIndex({ commit, getters }, index) {
      commit('SET_TABLE_RULE_ITEM_EDIT_INDEX', index) // Commit the index of the rule item
      commit('SET_TABLE_RULE_ITEM', cloneDeep(getters.tableRuleItems[index])) // Commit the rule item by index
    },

    // Action to save the changes made to a table rule item
    async saveTableRuleItem({
      commit, state, getters, dispatch,
    }) {
      const tableRuleItems = cloneDeep(getters.tableRuleItems) // Clone the existing table rule items
      const record = state.tableRuleItem // Get the current table rule item from state
      const editIndex = state.tableRuleItemEditIndex // Get the index of the table rule item to be edited

      // If it's a new item and it has rules, push it to the list of rule items
      if (editIndex === -1 && record.rules.length) {
        tableRuleItems.push(record)
        commit('SET_TABLE_RULE_ITEM_EDIT_INDEX', tableRuleItems.length - 1) // Set the index of the new item
      }

      // If it's an existing item with rules, update the item at the edit index
      if (editIndex !== -1 && record.rules.length) {
        tableRuleItems[editIndex] = record
      }

      // If it's an existing item with no rules, remove it from the list
      if (editIndex !== -1 && !record.rules.length) {
        await dispatch('setMode', 'table-rule-items') // Set mode to 'table-rule-items' before deletion
        tableRuleItems.splice(editIndex, 1) // Remove the item from the list
      }

      // Commit the updated list of table rule items to the store
      commit('SET_TABLE_RULE_ITEMS', tableRuleItems)
    },

    // Action to set or edit a key lookup item based on the provided keyId and nestedLabel
    setKeyLookupItem({ commit, getters }, { keyId, nestedLabel }) {
      let editIndex = -1
      const { keyLookupItems } = getters // Get the list of key lookup items
      let record

      // Find an existing key lookup item with the specified keyId and nestedLabel
      const keyLookupItemIndex = keyLookupItems.findIndex(item => item.nestedLabel === nestedLabel && item.keyId === keyId)
      if (keyLookupItemIndex !== -1) {
        record = cloneDeep(keyLookupItems[keyLookupItemIndex]) // If found, clone the item
        editIndex = keyLookupItemIndex // Set the edit index
      } else {
        // If not found, create a new record for the key lookup item
        record = {
          keyId,
          nestedLabel,
          queries: [],
        }
      }

      // Commit the edit index and the key lookup item data to the store
      commit('SET_KEY_LOOKUP_ITEM_EDIT_INDEX', editIndex)
      commit('SET_KEY_LOOKUP_ITEM', record)
    },

    // Action to set a key lookup item by its index
    setKeyLookupItemByIndex({ commit, getters }, index) {
      commit('SET_KEY_LOOKUP_ITEM_EDIT_INDEX', index) // Commit the index of the key lookup item
      commit('SET_KEY_LOOKUP_ITEM', cloneDeep(getters.keyLookupItems[index])) // Commit the key lookup item by index
    },

    // Action to save the changes made to a key lookup item
    saveKeyLookupItem({ commit, state, getters }) {
      const keyLookupItems = cloneDeep(getters.keyLookupItems) // Clone the existing key lookup items
      const record = state.keyLookupItem // Get the current key lookup item from state
      const editIndex = state.keyLookupItemEditIndex // Get the index of the key lookup item to be edited

      // If it's a new item, push it to the list of key lookup items
      if (editIndex === -1) {
        keyLookupItems.push(record)
        commit('SET_KEY_LOOKUP_ITEM_EDIT_INDEX', keyLookupItems.length - 1) // Set the index of the new item
      } else {
        // If it's an existing item, update the item at the edit index
        keyLookupItems[editIndex] = record
      }

      // Commit the updated list of key lookup items to the store
      commit('SET_KEY_LOOKUP_ITEMS', keyLookupItems)
    },
    // Action to set or edit a table lookup item based on the provided nestedLabel
    setTableLookupItem({ commit, getters }, { label }) {
      let editIndex = -1
      const { tableLookupItems } = getters // Get the list of table lookup items
      let record

      // Find an existing table lookup item with the specified nestedLabel
      const tableLookupItemIndex = (tableLookupItems || []).findIndex(item => item.label === label)
      if (tableLookupItemIndex !== -1) {
        record = cloneDeep(tableLookupItems[tableLookupItemIndex]) // If found, clone the item
        editIndex = tableLookupItemIndex // Set the edit index
      } else {
        // If not found, create a new record for the table lookup item
        record = {
          label,
          queries: [],
        }
      }

      // Commit the edit index and the table lookup item data to the store
      commit('SET_TABLE_LOOKUP_ITEM_EDIT_INDEX', editIndex)
      commit('SET_TABLE_LOOKUP_ITEM', record)
    },

    // Action to set a table lookup item by its index
    setTableLookupItemByIndex({ commit, getters }, index) {
      commit('SET_TABLE_LOOKUP_ITEM_EDIT_INDEX', index) // Commit the index of the key lookup item
      commit('SET_TABLE_LOOKUP_ITEM', cloneDeep(getters.tableLookupItems[index])) // Commit the key lookup item by index
    },

    // Action to save the changes made to a table lookup item
    saveTableLookupItem({ commit, state, getters }) {
      const tableLookupItems = cloneDeep(getters.tableLookupItems) || [] // Clone the existing table lookup items
      const record = state.tableLookupItem // Get the current key lookup item from state
      const editIndex = state.tableLookupItemEditIndex // Get the index of the table lookup item to be edited

      // If it's a new item, push it to the list of table lookup items
      if (editIndex === -1) {
        tableLookupItems.push(record)
        commit('SET_TABLE_LOOKUP_ITEM_EDIT_INDEX', tableLookupItems.length - 1) // Set the index of the new item
      } else {
        // If it's an existing item, update the item at the edit index
        tableLookupItems[editIndex] = record
      }

      // Commit the updated list of table lookup items to the store
      commit('SET_TABLE_LOOKUP_ITEMS', tableLookupItems)
    },
  },
  getters: {
    mainMode(state) {
      return state.mainMode
    },
    mode(state) {
      return state.mode
    },
    allDefinitions(state) {
      return state.allDefinitions
    },
    typesByDefinition(state) {
      return state.typesByDefinition
    },
    batchesByDefinitionType(state) {
      return state.batchesByDefinitionType
    },
    selectedDefinition(state) {
      return state.selectedDefinition
    },
    selectedTableId(state) {
      return state.selectedTableId || 0
    },
    selectedTableName(state) {
      return state.selectedTableName
    },
    table(state) {
      if (state.mainMode === 'verification') {
        return state.dJsonTableList
      }

      return state.selectedDefinition?.table
    },
    // Helper to get current table by name
    currentTable(state) {
      if (!state.selectedDefinition?.table || !state.selectedTableName) return null
      return state.selectedDefinition.table.find(t => t.table_name === state.selectedTableName)
    },
    tableModels(state, getters) {
      return getters.currentTable?.table_definition_data?.models || {}
    },
    tableColumns(state, getters) {
      return getters.currentTable?.table_definition_data?.columns || []
    },
    tableKeyItems(state, getters) {
      return getters.currentTable?.table_definition_data?.keyItems || []
    },
    tableColumnPrompts(state, getters) {
      return getters.currentTable?.table_definition_data?.columnPrompts || []
    },
    tableRuleItems(state, getters) {
      return getters.currentTable?.table_definition_data?.ruleItems || []
    },
    tableNormalizerItems(state, getters) {
      return getters.currentTable?.table_definition_data?.normalizerItems || []
    },
    key(state) {
      return state.selectedDefinition?.key
    },
    keyItems(state) {
      return state.selectedDefinition?.key.items
    },
    keyModels(state) {
      return state.selectedDefinition?.key.models
    },
    keyRuleItems(state) {
      return state.selectedDefinition?.key.ruleItems
    },
    keyNotInUseItems(state) {
      return state.selectedDefinition?.key.notInUseItems
    },
    keyLookupItems(state) {
      return state.selectedDefinition?.key.lookupItems
    },
    tableLookupItems(state, getters) {
      return getters.currentTable?.table_definition_data?.lookupItems || []
    },
    displayNotInUseFields(state) {
      return state.displayNotInUseFields
    },
    keyRuleItem(state) {
      return state.keyRuleItem
    },
    keyRuleItemEditIndex(state) {
      return state.keyRuleItemEditIndex
    },
    keyRuleItemRules(state) {
      return state.keyRuleItem?.rules || []
    },
    tableRuleItem(state) {
      return state.tableRuleItem
    },
    tableRuleItemEditIndex(state) {
      return state.tableRuleItemEditIndex
    },
    tableRuleItemRules(state) {
      return state.tableRuleItem?.rules || []
    },
    keyLookupItem(state) {
      return state.keyLookupItem
    },
    keyLookupItemQueries(state) {
      return state.keyLookupItem?.queries || []
    },
    tableLookupItem(state) {
      return state.tableLookupItem
    },
    tableLookupItemQueries(state) {
      return state.tableLookupItem?.queries || []
    },
    loading(state) {
      return state.loading
    },
    loadingError(state) {
      return state.loadingError
    },
    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // duplicatePromptKeys(state) {
    //   return state.duplicatePromptKeys
    // },
    selectedDefinitionVersion(state) {
      return state.selectedDefinitionVersion
    },
    selectedModelType(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.type
    },
    modelAutoPattern(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.autoPatterns
    },
    modelUserSelectedPatterns(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.userSelectedPatterns || []
    },
    modelExtendedUserSelectedPatterns(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.extendedUserSelectedPatterns || []
    },
    modelUserSelectedOb(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.userSelectedOb || []
    },
    modelAutoPositionShiftCal(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.autoPositionShiftCal
    },
    modelMultipleLineRecord(state, getters) {
      return getters.currentTable?.table_definition_data?.models?.multipleLineRecord || false
    },
    showChunkData(state) {
      return state.showChunkData
    },
    getCellRangePermission(state) {
      return state.cellRangePermission
    },
    getTableFields(state) {
      return state.tableFields
    },
    getAutoExtractedKeys(state) {
      return state.isAutoExtracted
    },

  },
}
