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
 *   This file serves as the Vuex store module for managing batch-related data in the application.
 *
 * Dependencies:
 *   - vue, axios, bus and lodash
 *   - Helper functions
 *
 * Main Features:
 *   - Define the default state and initialize its values.
 *   - Implement mutations and getters for state management.
 *   - Write action methods to handle asynchronous operations.
 *   - Integrate and bind APIs for batch data.
 */

import Vue from 'vue'
import { cloneDeep } from 'lodash'
import axios from 'axios'
import bus from '@/bus'
import { v4 as uuidv4 } from 'uuid'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import {
  searchNodes, expandNodesByType, getNodes, getFlatNodes, getDocuments, getExcelData, getKeyItemById, idSplltier, createTransactionHierarchy,
} from './helper'
// getVerificationDocuments  // This is coming from helper but if we are not using setDocument function so it is useless

// Default structure for highlight key anchors data
const defaultHighlightKeyAnchorsData = {
  keyItemId: null, // ID of the key item being highlighted
  selectedAnchor: null, // Currently selected anchor
  source: null, // Source of the anchor data
}

// Default structure for document data
const defaultDocumentData = {
  pages: {}, // Placeholder for pages data
  excelData: null, // Placeholder for Excel data
}

export default {
  namespaced: true, // Enables namespacing for this Vuex module
  state: {
    // Main state properties
    batch: null, // Current batch data
    selectedBatch: null, // Current batch data
    batchNodes: [], // Nodes associated with the batch
    batches: [],
    batchesIds: [], // Nodes associated with the batch
    manualValidation: false, // Indicates if manual validation is enabled
    multiShipment: false, // Indicates if multiple shipments are involved
    verificationStatus: '', // Status of the verification process
    verificationDetails: [], // Details of the verification process
    nodes: [], // List of all nodes
    rootNodeList: null, // Root nodes in the hierarchy
    selectedNodeId: null, // ID of the currently selected node
    editableNode: null, // Node that is currently editable
    highlightRootNodes: false, // Flag to highlight root nodes
    nodeConfig: {}, // Configuration settings for nodes
    search: '', // Search query string
    expandedNodes: [], // List of expanded nodes
    matchedNodes: [], // Nodes matched with the search query
    zoom: 1, // Zoom level for the UI
    enableSelector: false, // Whether the node selector is enabled
    enableMeasure: false, // Whether the measurement tool is enabled
    view: 'key', // Current view mode (e.g., 'key', 'document', etc.)
    mode: 'edit', // Current mode (e.g., 'edit', 'view', etc.)
    status: null, // General status of the module
    refreshing: false, // Indicates if data is being refreshed
    totalPages: 0, // Total number of pages in the document
    documents: {}, // Dictionary of loaded documents
    selectedDocumentId: null, // ID of the selected document
    documentData: {
      ...defaultDocumentData, // Clone the default document structure
    },
    childNodes: [], // Child nodes for the currently selected node
    loadingDocumentData: false, // Indicates if document data is loading
    selectorPosition: null, // Position of the selector tool
    measuredDistance: null, // Result of a measurement action
    highlightKeyBlocks: false, // Flag to highlight key blocks
    chunkData: {}, // Chunk data for the batch
    chunkDataWithPlainText: '', // Chunk data  WithPlainText for the batch
    highlightKeyAnchorsData: {
      ...defaultHighlightKeyAnchorsData, // Clone the default anchor data structure
    },
    error: null, // Placeholder for error messages
    scrollToPos: null, // Position to scroll to in the UI
    testOptions: {
      skipPostProcessor: false, // Whether to skip the post-processing step
      skipKeyProcessing: false, // Whether to skip key processing
      skipTableProcessing: false, // Whether to skip table processing
    },
    selectedCellDetails: null, // Details of the currently selected cell (e.g., in a table)
    positionShiftData: null, // Data for handling position shifts
    isAddRow: false, // Flag for adding a row
    isDeleteRow: false, // Flag for deleting a row
    isAnyDeletableRow: true, // Indicates if there are rows that can be deleted
    currentEmailBatchId: '', // Batch ID for emails
    tempImageList: [], // Temporary list of images
    topPaneSize: 0,
    batchId: null,
    isAgentBlink: false,
    keyNodes: [],

    transaction: null, // Current transaction data
    transactionBatches: {},
    transactionNodes: [], // Nodes for the entire transaction
    selectedTransactionId: null, // ID of the selected transaction
    selectedBatchId: null,
    projectAllKeys: [],
    profileKeys: [],
    // profileDefinitionKeys: [],
    profileTableKeys: [],
    profileDetails: {},
    transactionType: '',
    tainingBatchLinkId: '',
    isProfileLoadig: false,
    showBottomPanel: false,
    isKeyRecognized: false,
    undoKeyMappingData: null,
    hideEmptyAutoExtrationKeys: {},
    matchedProfileKeys: [],
    extractedMatchedProfileKeys: [],
    trainingLinkedBatchIds: [],
    isCombineView: false,
    documentSortOrder: 'asc', // 'asc' or 'desc' for document sorting
    documentSortVersion: 0, // bump to force recompute of getters using sort
    selectedTransactionProcess: '',
  },
  // Define mutations for directly modifying the state
  mutations: {
    SET_SELECTED_TRANSACTION_PROCESS_NAME(state, value) {
      state.selectedTransactionProcess = value
    },
    SET_SHOW_BOTTOM_PANEL(state, value) {
      state.showBottomPanel = value
    },
    SET_COMBINE_VIEW(state, value) {
      state.isCombineView = value
    },
    SET_DOCUMENT_SORT_ORDER(state, value) {
      state.documentSortOrder = value // 'asc' or 'desc'
      state.documentSortVersion += 1
    },
    TOGGLE_DOCUMENT_SORT_ORDER(state) {
      state.documentSortOrder = state.documentSortOrder === 'asc' ? 'desc' : 'asc'
      state.documentSortVersion += 1
    },
    SET_SHOW_HIDE_RECOGNIZED_KEYS(state, value) {
      state.isKeyRecognized = value
    },
    REMOVE_TABLE_FROM_DOCUMENT(state, {
      transactionId, batchId, documentId, tableName,
    }) {
      const documentPath = state.documents?.[transactionId]?.[batchId]?.[documentId]

      if (documentPath?.children && Array.isArray(documentPath.children)) {
      // Remove the table from children array
        documentPath.children = documentPath.children.filter(child => !(child.type === 'table'
          && (child.table_name === tableName
           || child.name === tableName
           || child.id === tableName)))
      }
    },
    SET_TRANSACTION(state, transaction) {
      state.transaction = transaction
    },
    SET_TRANSACTION_BATCHES(state, transactionBatches) {
      state.transactionBatches = transactionBatches
    },
    SET_TRANSACTION_NODES(state, transactionNodes) {
      state.transactionNodes = transactionNodes
    },
    SET_SELECTED_TRANSACTION_ID(state, value) {
      state.selectedTransactionId = value
    },
    SET_SELECTED_BATCH_ID(state, value) {
      state.selectedBatchId = value
    },
    // new mutation end
    SET_BATCH_ID(state, value) {
      state.batchId = value
    },
    SET_AGENT_BLINK(state, value) {
      state.isAgentBlink = value
    },
    SET_TEMP_IMGE_LIST(state, value) {
      state.tempImageList = value
    },
    SET_BATCH(state, batch) {
      state.batch = batch
    },
    SET_SELECTED_BATCH(state, batch) {
      state.selectedBatch = batch
    },
    SET_BATCHES(state, batches) {
      state.batches = batches
    },
    SET_BATCH_NODES(state, batchNodes) {
      state.batchNodes = batchNodes
    },
    SET_BATCHES_IDS(state, batchesIds) {
      state.batchesIds = batchesIds
    },
    SET_TRAINING_BATCHES_LINKED_IDS(state, ids) {
      state.trainingLinkedBatchIds = ids
    },
    SET_VERIFICATION_BATCHES_IDS(state, verificationBatchesIds) {
      state.verificationBatchesIds = verificationBatchesIds
    },
    SET_VERIFICATION_STATUS(state, value) {
      state.verificationStatus = value
    },
    SET_MANUAL_VALIDATION(state, value) {
      state.manualValidation = value
    },
    SET_MULTI_SHIPMENT(state, value) {
      state.multiShipment = value
    },
    SET_VERIFICATION_DETAILS(state, value) {
      state.verificationDetails = value
    },
    SET_SELECTED_NODE_ID(state, nodeId) {
      state.selectedNodeId = nodeId
    },
    SET_EDITABLE_NODE(state, node) {
      state.editableNode = node
    },
    SET_NODES(state, nodes) {
      state.nodes = nodes
      state.keyNodes = nodes
    },
    SET_ROOT_NODE_LIST(state, value) {
      state.rootNodeList = value
    },
    SET_HIGHLIGHT_ROOT_NODES(state, status) {
      state.highlightRootNodes = status
    },
    SET_NODE_CONFIG(state, { id, value }) {
      Vue.set(state.nodeConfig, id, value)
    },
    CLEAR_NODE_CONFIG(state) {
      state.nodeConfig = {}
    },
    SET_SEARCH(state, value) {
      state.search = value
    },
    EXPAND_NODE(state, nodeId) {
      state.expandedNodes.push(nodeId)
    },
    COLLAPSE_NODE(state, nodeId) {
      state.expandedNodes = state.expandedNodes.filter(id => id !== nodeId)
    },
    SET_EXPANDED_NODES(state, expandedNodeIds) {
      state.expandedNodes = expandedNodeIds
    },
    SET_MATCHED_NODES(state, matchedNodeIds) {
      state.matchedNodes = matchedNodeIds
    },
    SET_ZOOM(state, zoom) {
      state.zoom = zoom
    },
    SET_ENABLE_SELECTOR(state, value) {
      state.enableSelector = value
    },
    SET_ENABLE_MEASURE(state, value) {
      state.enableMeasure = value
    },
    SET_VIEW(state, value) {
      state.view = value
    },
    SET_MODE(state, value) {
      state.mode = value
    },
    SET_STATUS(state, value) {
      state.status = value
    },
    SET_REFRESHING(state, value) {
      state.refreshing = value
    },
    SET_TOTAL_PAGES(state, value) {
      state.totalPages = value
    },
    SET_DOCUMENTS(state, documents) {
      state.documents = documents
    },
    SET_SELECTED_DOCUMENT_ID(state, value) {
      state.selectedDocumentId = value
    },
    SET_DOCUMENT_DATA(state, value) {
      state.documentData = value
    },
    SET_LOADING_DOCUMENT_DATA(state, value) {
      state.loadingDocumentData = value
    },
    SET_SELECTOR_POSITION(state, value) {
      state.selectorPosition = value
    },
    SET_MEASURED_DISTANCE(state, value) {
      state.measuredDistance = value
    },
    SET_HIGHLIGHT_KEY_BLOCKS(state, status) {
      state.highlightKeyBlocks = status
    },
    SET_CHUNK_DATA(state, value) {
      state.chunkData = value
    },
    SET_CHUNK_DATA_PLAIN_TEXT(state, value) {
      state.chunkDataWithPlainText = value
    },
    SET_HIGHLIGHT_KEY_ANCHORS_DATA(state, { keyItemId, selectedAnchor, source }) {
      state.highlightKeyAnchorsData = {
        keyItemId,
        selectedAnchor,
        source,
      }
    },
    SET_ERROR(state, value) {
      state.error = value
    },
    SET_SCROLL_TO_POS(state, value) {
      state.scrollToPos = value
    },
    SET_TEST_OPTIONS(state, value) {
      state.testOptions = value
    },
    SET_SELECTED_CELL_DETAILS(state, value) {
      state.selectedCellDetails = value
    },
    SET_POSITION_SHIFT_DATA(state, value) {
      state.positionShiftData = value
    },
    TOGGLE_ADD_ROW(state, value) {
      state.isAddRow = value
    },
    TOGGLE_DELETE_ROW(state, value) {
      state.isDeleteRow = value
    },
    CHECK_DELETE_ROW(state, value) {
      state.isAnyDeletableRow = value
    },
    SET_TOP_PANESIZE(state, newSize) {
      state.topPaneSize = newSize
    },
    SET_PROFILE_DETAILS(state, value) {
      state.profileDetails = value
    },
    SET_MATCHED_PROFILE_KEYS(state, value) {
      state.matchedProfileKeys = value
    },
    // SET_EXTRACTED_MATCHED_PROFILE_KEYS(state, value) {
    //   state.extractedMatchedProfileKeys = value
    // },
    SET_PROJECT_KEYS(state, value) {
      state.projectAllKeys = value
    },
    SET_PROFILE_KEYS(state, value) {
      state.profileKeys = value
    },
    // SET_PROFILE_AND_DEFINITION_KEYS(state, value) {
    //   state.profileDefinitionKeys = value
    // },
    SET_PROFILE_TABLE_KEYS(state, value) {
      state.profileTableKeys = value
    },
    SET_TRANSACTION_TYPE(state, type) {
      state.transactionType = type
    },
    SET_TRAINING_LINK_BATCH_ID(state, id) {
      state.tainingBatchLinkId = id
    },
    SET_PROFILE_LOADING(state, type) {
      state.isProfileLoadig = type
    },
    SET_UNDO_KEY_MAPPING_DATA(state, value) {
      state.undoKeyMappingData = value
    },
    SET_HIDE_EMPTY_AUTO_EXTRACTION_KEYS(state, value) {
      state.hideEmptyAutoExtrationKeys = value
    },
  },
  actions: {
    // Remove Table fro transactions
    // Vuex Action to remove a table from a document in a transaction
    removeTableFromTransaction({ commit, state }, { batchId, documentId, tableName }) {
      const { transaction } = state

      // Clone the transaction deeply to avoid direct mutation
      const updatedTransaction = {
        ...transaction,
        batches: transaction.batches.map(batch => {
          if (batch.id !== batchId) return batch

          const updatedNodes = (batch.data_json?.nodes || []).map(node => {
            if (node.id !== documentId) return node

            // If the node has tables, filter out the target table
            if (Array.isArray(node.tables)) {
              return {
                ...node,
                tables: node.tables.filter(table => table.name !== tableName),
              }
            }

            return node
          })

          return {
            ...batch,
            data_json: {
              ...batch.data_json,
              nodes: updatedNodes,
            },
          }
        }),
      }

      // Commit the updated transaction
      commit('SET_TRANSACTION', updatedTransaction)
    },
    // Setting  selected Batch
    async changeBatch({ commit, state, dispatch }, batchId) {
      // Find the batch in the transaction data
      const batchToSelect = state.transaction?.batches?.find(batch => batch.id === batchId) || state.transaction.batches[0]
      const batch = {
        id: batchToSelect.id,
        vendor: batchToSelect.vendor,
        type: batchToSelect.document_types,
        nameMatchingText: batchToSelect?.name_matching_text || 'test',
        definitionId: batchToSelect.profile,
        mode: batchToSelect.mode,
        subPath: batchToSelect.sub_path,
        definitionVersion: batchToSelect.data_json.definition_version,
        isExcel: batchToSelect.data_json.batch_type === '.xlsx',
        project: batchToSelect.data_json.Project,
        isDatasetBatch: batchToSelect.is_dataset_batch,
      }
      commit('SET_BATCH', batch)
      commit('SET_SELECTED_BATCH', batchToSelect)
      // Change type to 'batch' instead of 'root'
      commit('SET_BATCH_NODES', [{ type: 'batch', id: batchToSelect.id, children: batchToSelect.data_json.nodes }])
      commit('SET_SELECTED_BATCH_ID', batch.id)

      // Reset document selection
      // commit('SET_SELECTED_DOCUMENT_ID', null)
      // Then load the first document of the new batch
      // await dispatch('dataView/fetchDefinition', null, { root: true })
      await dispatch('selectFirstDocument')
      await dispatch('loadDocumentData')
    },
    // Add this action to your actions object
    // Action to set the selected node ID
    setSelectedNodeId({ commit }, nodeId) {
      // Commit the mutation to update the selected node ID
      commit('SET_SELECTED_NODE_ID', nodeId)
    },

    // Action to set the editable node
    setEditableNode({ state, commit }, node) {
      // Check if the editable node is already set and matches the new node
      if (state.editableNode && node && state.editableNode.id === node.id) {
        state.editableNode.v = node.v // Update the value directly in the state
        return // Exit if no changes are needed
      }

      // Commit the mutation to update the editable node
      commit('SET_EDITABLE_NODE', node)
    },

    // Action to update the node configuration
    setNodeConfig({ commit }, data) {
      // Commit the mutation to set the node configuration
      commit('SET_NODE_CONFIG', data)
    },
    // Action to get profile details
    async getProfileDetails({ state, commit }) {
      try {
        commit('SET_PROFILE_LOADING', true)

        const profileName = state.transaction?.profile
        if (!profileName) {
          return
        }
        const res = await axios.get(`/get_profile_by_name/${profileName}`)
        const profileDetails = res.data?.profile || {}

        commit('SET_PROFILE_DETAILS', profileDetails)
        commit('SET_PROFILE_LOADING', false)
      } catch (error) {
        const err = error?.response?.data?.detail || 'Fetching Process Details Error'
        commit('SET_PROFILE_LOADING', false)
        throw new Error(err) // Throw error for higher-level handling
      }
    },
    // Action to set the search query and update the related state
    setSearch({ commit, state }, value) {
      let expandedIds = [] // Initialize an empty array for expanded node IDs
      let matchedIds = [] // Initialize an empty array for matched node IDs

      if (value) {
        // Perform a search and get the result
        const searchResult = searchNodes(state.batchNodes, value)
        expandedIds = searchResult.expandedIds // Extract expanded node IDs
        matchedIds = searchResult.matchedIds // Extract matched node IDs
      }

      // Commit updates for search query and results
      commit('SET_SEARCH', value)
      commit('SET_EXPANDED_NODES', expandedIds)
      commit('SET_MATCHED_NODES', matchedIds)
      commit('SET_SELECTED_NODE_ID', null) // Reset the selected node ID
    },

    // Action to check if a batch is available
    async checkBatchAvailability({ rootGetters }, batchId) {
      try {
        // Call the API to check batch availability
        const res = await axios.get('/check_batch_availability', {
          params: { batch_id: batchId },
        })

        // Get all definitions from the root getters
        const allDefinitions = rootGetters['dataView/allDefinitions']

        // Return availability if the definition exists in all definitions
        return res.data.available && allDefinitions.includes(res.data.definition_id)
          ? res.data.available
          : false
      } catch {
        // Return false in case of an error
        return false
      }
    },

    // Action to fetch verification details for an email batch - improved
    async fetchVerificationDetails({ commit, dispatch, state }, emailBatchId) {
      state.currentEmailBatchId = emailBatchId // Set the current email batch ID

      try {
        // Fetch verification details from the API
        const res = await axios.get(`/pipeline/get_verification_details/${emailBatchId}/`)

        // Sort batches by ID for consistency
        res.data.batches_info.sort((a, b) => {
          if (a.id < b.id) return -1
          if (a.id > b.id) return 1
          return 0
        })

        // Transform verification data to match transaction structure
        const normalizedBatches = res.data.batches_info.map((batch, index) => {
          // Extract data from nested data_json structure
          const dataJson = batch.data_json || {}

          return {
            // Main batch properties (directly available in transaction API)
            id: batch.id || `batch-${index}`,
            profile: dataJson.DefinitionID || null, // Extract from data_json.DefinitionID
            project: dataJson.Project || '',
            status: batch.status || 'completed',
            sub_path: batch.sub_path || '',
            vendor: dataJson.Vendor || '', // Extract from data_json.Vendor
            document_types: dataJson.DocumentType || '', // Extract from data_json.DocumentType
            name_matching_text: dataJson.NameMatchingText || 'test',
            // Keep data_json structure but ensure it has the right format
            data_json: {
              id: dataJson.id || batch.id,
              TYPE: dataJson.TYPE || '',
              bvOCR: dataJson.bvOCR || '',
              DefinitionID: dataJson.DefinitionID || '',
              DocumentType: dataJson.DocumentType || '',
              Language: dataJson.Language || 'English',
              NameMatchingText: dataJson.NameMatchingText || null,
              Project: dataJson.Project || '',
              STATUS: dataJson.STATUS || '0',
              Vendor: dataJson.Vendor || '',
              aidbServerIP: dataJson.aidbServerIP || '',
              batch_type: dataJson.batch_type || '.pdf',
              bvBarcodeRead: dataJson.bvBarcodeRead || 'N',
              bvBatchType: dataJson.bvBatchType || 'Process',
              bvFilePath: dataJson.bvFilePath || '',
              bvPageRotate: dataJson.bvPageRotate || 'N',
              bvSelectedDocTypes: dataJson.bvSelectedDocTypes || 'None',
              definition_version: dataJson.definition_version,
              nodes: Array.isArray(dataJson.nodes) ? dataJson.nodes : [],
              ...dataJson, // Preserve any other properties
            },
          }
        })

        // Commit updates to the state
        commit('SET_MANUAL_VALIDATION', res.data.manual_validation || false)
        commit('SET_MULTI_SHIPMENT', res.data.multi_shipment || false)
        commit('SET_VERIFICATION_STATUS', res.data.verification_status || '')
        commit('SET_VERIFICATION_DETAILS', normalizedBatches)

        // Load the verification page with normalized data
        await dispatch('loadVerificationPage', {
          data: normalizedBatches,
          emailBatchId,
        })
      } catch (error) {
        // Handle errors and display a toast notification
        const err = error?.response?.data?.detail || 'Error fetching verification details'

        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: err,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        // Commit the error to the state and reset loading
        commit('SET_ERROR', err)
        commit('dataView/SET_LOADING', false, { root: true })

        // Set safe fallback state
        commit('SET_TRANSACTION_NODES', [])
        commit('SET_BATCH_NODES', [])
        commit('SET_NODES', [])
        commit('SET_DOCUMENTS', {})
      }
    },

    // Action to load the verification page - improved to match loadTransaction pattern
    async loadVerificationPage({ commit, dispatch }, { data, emailBatchId }) {
      // Create transaction-like data structure
      const transactionData = {
        transaction_id: emailBatchId,
        profile: data[0]?.profile || null, // Use the profile from the first batch
        profile_information: {
          multi_shipment: false, // This can be set from the verification API response
        },
        batches: data || [],
      }

      // Set the process name for prompt keys
      commit('SET_SELECTED_TRANSACTION_PROCESS_NAME', transactionData.profile)

      // Use the existing loadTransaction function
      dispatch('loadTransaction', transactionData)

      // Set verification-specific data
      const batchesIds = data?.map(batch => batch.id) || []
      commit('SET_BATCHES_IDS', batchesIds)

      // Set verification details (keep the original data for verification-specific operations)
      commit('SET_VERIFICATION_DETAILS', data)
      const firstBatchId = data[0]?.id
      if (firstBatchId) {
        commit('SET_SELECTED_BATCH_ID', firstBatchId)
        commit('SET_BATCH_ID', firstBatchId)
      }
      // Dispatch additional actions
      await dispatch('expandNodes', ['document'])
      await dispatch('selectFirstDocument')
      await dispatch('loadDocumentData')

      // Reset table list data
      await dispatch('dataView/setDJsonTableList', null, { root: true })
    },

    // Action to fetch a batch by its ID
    // Action to fetch a batch by its ID
    async fetchBatch({ dispatch, commit, getters }, { selectedTransaction, selectFirstDocument }) {
      const transactionType = getters.getTransactionType
      const linkTraningBacth = getters.getTrainingLinkBatchId
      const omitTraining = transactionType !== 'training'

      try {
        // Base params
        const params = {
          transaction_id: selectedTransaction,
        }

        // In training mode, always add is_training: true
        // Only add batch_id if linkTraningBacth has a value
        if (!omitTraining) {
          params.is_training = true
          if (linkTraningBacth) {
            params.batch_id = linkTraningBacth
          }
        }

        const res = await axios.get('/pipeline/get_transaction_batches/', { params })
        const batchesIds = res.data?.batches?.map(batch => batch.id)

        // Dispatch actions to load and process the transaction
        // await dispatch('dataView/fetchSelectorDataByBatch', res.data, { root: true })
        commit('SET_TRANSACTION_BATCHES', res.data)
        commit('SET_SELECTED_TRANSACTION_PROCESS_NAME', res.data.profile)
        commit('SET_TRAINING_BATCHES_LINKED_IDS', res.data.batch_ids || [])
        await dispatch('loadTransaction', res.data)
        await dispatch('expandNodes', ['document'])

        if (selectFirstDocument) {
          await dispatch('selectFirstDocument')
        }
        commit('SET_BATCHES_IDS', batchesIds)
      } catch (error) {
        // Handle errors by throwing a descriptive error
        const err = error?.response?.data?.detail || 'Fetching transaction'
        throw new Error(err)
      }
    },
    // Action to load batch data into the state
    async loadTransaction({ commit, getters }, transactionData) {
      const transactionNodes = createTransactionHierarchy(transactionData)

      const transaction = {
        id: transactionData.transaction_id,
        profile: transactionData.profile,
        batches: transactionData.batches || [],
      }

      // Try to use the selected batch from Vuex (if it exists and matches a real batch)
      const { selectedBatchId } = getters
      const matchingBatch = transaction.batches.find(batch => batch.id === selectedBatchId)

      // Fallback to the first batch if no match is found
      const usedBatch = matchingBatch || transaction.batches[0] || {}

      const batch = {
        id: usedBatch.id,
        vendor: usedBatch.vendor,
        type: usedBatch.document_types,
        nameMatchingText: usedBatch?.name_matching_text || 'test',
        definitionId: usedBatch.profile,
        mode: usedBatch.mode,
        subPath: usedBatch.sub_path,
        definitionVersion: usedBatch.data_json?.definition_version,
        isExcel: usedBatch.data_json?.batch_type === '.xlsx',
        project: usedBatch.data_json?.Project,
        isDatasetBatch: usedBatch.is_dataset_batch,
      }

      commit('SET_MULTI_SHIPMENT', transactionData?.profile_information?.multi_shipment)
      commit('SET_TRANSACTION', transaction)
      commit('SET_BATCH', batch)
      commit('SET_SELECTED_BATCH', usedBatch)
      commit('SET_BATCHES', transaction.batches)
      commit('SET_TRANSACTION_NODES', transactionNodes)
      commit('SET_BATCH_NODES', [{ type: 'batch', id: usedBatch.id, children: usedBatch.data_json?.nodes || [] }])
      commit('SET_NODES', getNodes(transactionNodes))
      commit('SET_DOCUMENTS', getDocuments(transactionNodes))
      commit('SET_SELECTED_TRANSACTION_ID', transaction.id)
      commit('SET_SELECTED_BATCH_ID', batch.id)
      commit('SET_BATCH_ID', batch.id)

      localStorage.setItem('previous_transaction_id', transaction.id)
    },

    // Action to load document data associated with a batch
    async loadDocumentData({ commit, state }) {
      commit('SET_LOADING_DOCUMENT_DATA', true) // Indicate loading status
      try {
        // Fetch document data from the API with transaction, batch, and document IDs
        const response = await axios.get('/ra_json/', {
          params: {
            transaction_id: state.selectedTransactionId,
            batch_id: state.selectedBatchId,
            document_id: state.selectedDocumentId,
          },
        })

        const documentData = { ...defaultDocumentData } // Initialize default document structure
        if (state.batch.isExcel) {
          // If the batch is Excel, process Excel-specific data
          documentData.excelData = getExcelData(response.data.nodes)
        } else {
          // Otherwise, set page data
          documentData.pages = response.data.nodes
        }

        // Update the state with document details
        commit('SET_TOTAL_PAGES', response.data.total_pages)
        commit('SET_DOCUMENT_DATA', documentData)
        commit('SET_LOADING_DOCUMENT_DATA', false)
      } catch (error) {
        // Display an error notification on failure
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.response?.data?.detail || 'Error fetching document data',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        // Reset document data on error
        commit('SET_DOCUMENT_DATA', { ...defaultDocumentData })
        commit('SET_LOADING_DOCUMENT_DATA', false)
      }
    },

    async loadNestedRaJson({ state }, pageIds) {
      try {
        // Fetch nested data for a specific page
        const response = await axios.get('/get_ra_json_page_data/', {
          params: {
            batch_id: state.batch.id,
            document_id: state.selectedDocumentId,
            page_ids: pageIds,
          },
        })
        return response.data || [] // Return the child nodes data
      } catch (error) {
        // Show an error message if fetching fails
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.response?.data?.detail || `Error fetching child nodes for page ${pageIds}`,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        return [] // Return an empty array on error
      }
    },

    // Action to fetch position shift data
    async fetchPositionShiftData({ rootGetters, commit }) {
      try {
        const selectedTableName = rootGetters['dataView/selectedTableName'] // Get selected table ID
        const { table_unique_id } = rootGetters['dataView/table'][selectedTableName]

        // Fetch position shift data from the API
        const res = await axios.post('/pipeline/position_shift_data/', {
          batch_id: rootGetters['batch/batch'].id,
          table_unique_id,
          definition_version: rootGetters['dataView/selectedDefinitionVersion'],
        })

        commit('SET_POSITION_SHIFT_DATA', res?.data?.data || []) // Commit fetched data
      } catch (error) {
        const err = error?.response?.data?.detail || 'Fetching Position Shift data'
        throw new Error(err) // Throw error for higher-level handling
      }
    },

    // Action to select the first document in the list
    async selectFirstDocument({ commit, state }) {
      if (!state.documents) {
        return
      }

      // First, select the transaction if not already selected
      if (!state.selectedTransactionId) {
        const transactionIds = Object.keys(state.documents)
        if (transactionIds.length > 0) {
          commit('SET_SELECTED_TRANSACTION_ID', transactionIds[0])
        } else {
          return
        }
      }

      // Then, select the batch if not already selected
      if (!state.selectedBatchId) {
        const batchIds = Object.keys(state.documents[state.selectedTransactionId] || {})
        if (batchIds.length > 0) {
          commit('SET_SELECTED_BATCH_ID', batchIds[0])
        } else {
          return
        }
      }

      // Finally, select the document
      const documentIds = Object.keys(state.documents[state.selectedTransactionId][state.selectedBatchId] || {})
      if (documentIds.length > 0) {
        commit('SET_SELECTED_DOCUMENT_ID', documentIds[0])
      }
    },

    // Action to expand specific node types
    expandNodes({ commit, state }, nodeTypes) {
      const expandedIds = expandNodesByType(state.batchNodes, nodeTypes) // Expand nodes based on type
      commit('SET_EXPANDED_NODES', expandedIds) // Commit expanded node IDs
    },

    // Action to zoom in on the UI
    zoomIn({ commit, state }) {
      const newVal = state.zoom + 0.1 // Increase zoom level
      if (newVal <= 10) { // Ensure zoom level doesn't exceed maximum
        commit('SET_ZOOM', newVal)
      }
    },

    // Action to zoom out on the UI
    zoomOut({ commit, state }) {
      const newVal = state.zoom - 0.1 // Decrease zoom level
      if (newVal > 0.1) { // Ensure zoom level stays above minimum
        commit('SET_ZOOM', newVal)
      }
    },
    // Toggles the selector mode in the application
    toggleSelector({ commit, state }) {
      commit('SET_ENABLE_SELECTOR', !state.enableSelector) // Toggle the selector state
      if (state.enableSelector && state.enableMeasure) {
        commit('SET_ENABLE_MEASURE', false) // Disable measure mode if it's active
      }
    },

    // Toggles the measure mode in the application
    toggleMeasure({ commit, state }) {
      commit('SET_ENABLE_MEASURE', !state.enableMeasure) // Toggle the measure state
      if (state.enableMeasure && state.enableSelector) {
        commit('SET_ENABLE_SELECTOR', false) // Disable selector mode if it's active
      }
    },

    // Toggles the highlighting of root nodes
    toggleHighlightRootNodes({ commit, state }) {
      commit('SET_HIGHLIGHT_ROOT_NODES', !state.highlightRootNodes) // Toggle root node highlighting
    },

    // Toggles the highlighting of key blocks
    toggleHighlightKeyBlocks({ commit, state }) {
      commit('SET_HIGHLIGHT_KEY_BLOCKS', !state.highlightKeyBlocks) // Toggle key block highlighting
    },

    // Updates the value of a node in the verification details
    updateNodeValue({ commit, state }, data) {
      try {
        const {
          batchId, documentId, keyId, keyItemId, keyItemChildId,
        } = idSplltier(data.id)

        const verificationDetails = [...state.verificationDetails]
        const dataJsonIndex = verificationDetails.findIndex(e => e.id === batchId)

        const docIndex = verificationDetails[dataJsonIndex].data_json.nodes.findIndex(e => e.id === documentId)

        const document = verificationDetails[dataJsonIndex].data_json.nodes[docIndex]

        const docItemIndex = document.children.findIndex(e => e.id === keyId) // Locate the document item
        const keyItemIndex = document.children[docItemIndex].children.findIndex(e => e.id === keyItemId) // Locate the key item

        if (!keyItemChildId) {
          // If no child ID is provided, update the key item's value
          document.children[docItemIndex].children[keyItemIndex].v = data.nodeValue
        } else {
          // Otherwise, update the child key item's value
          const keyItemChildIdIndex = document.children[docItemIndex].children[keyItemIndex].children.findIndex(e => e.id === keyItemChildId)
          document.children[docItemIndex].children[keyItemIndex].children[keyItemChildIdIndex].v = data.nodeValue
        }

        // Update the verification details in the state
        verificationDetails[dataJsonIndex].data_json.nodes[docIndex] = document
        commit('SET_VERIFICATION_DETAILS', verificationDetails)
      } catch (error) {
        // Show an error toast notification on failure
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.message || 'Error updating node value',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },

    // Adds a new node or updates an existing one with a value
    addNodeWithValue({ commit, state }, data) {
      // Helper function to generate the next ID in sequence

      function getNextId(currentId) {
        const parts = currentId.split('.')
        let lastSegment = parseInt(parts[parts.length - 1], 10)
        lastSegment += 1
        parts[parts.length - 1] = lastSegment.toString().padStart(3, '0') // Pad the new segment with zeros
        return parts.join('.')
      }

      try {
        const {
          batchId, documentId, keyId, keyItemId, keyItemChildId,
        } = idSplltier(data.id)

        const verificationDetails = [...state.verificationDetails] // Clone the verification details array
        const dataJsonIndex = verificationDetails.findIndex(e => e.id === batchId) // Locate the batch

        const docIndex = verificationDetails[dataJsonIndex].data_json.nodes.findIndex(e => e.id === documentId) // Locate the document
        const document = verificationDetails[dataJsonIndex].data_json.nodes[docIndex]

        const docItemIndex = document.children.findIndex(e => e.id === keyId) // Locate the document item
        const keyItemIndex = document.children[docItemIndex].children.findIndex(e => e.id === keyItemId) // Locate the key item

        if (!keyItemChildId) {
          // Add or update a key item
          if (keyItemIndex > -1) {
            // Update existing key item
            document.children[docItemIndex].children[keyItemIndex].v = data.v
            document.children[docItemIndex].children[keyItemIndex].pos = data.pos
          } else {
            // Add a new key item
            const { children } = document.children[docItemIndex]
            const newCell = cloneDeep(children[children.length - 1]) // Clone the last item to use as a template
            newCell.id = getNextId(newCell.id)
            newCell.v = data.v
            newCell.pos = data.pos
            newCell.label = data.label
            document.children[docItemIndex].children.push(newCell)
          }
        } else {
          // Add or update a key item child
          const keyItemChildIdIndex = document.children[docItemIndex].children[keyItemIndex].children.findIndex(e => e.label === data.label)
          if (keyItemChildIdIndex > -1) {
            // Update existing key item child
            document.children[docItemIndex].children[keyItemIndex].children[keyItemChildIdIndex].v = data.v
            document.children[docItemIndex].children[keyItemIndex].children[keyItemChildIdIndex].pos = data.pos
          } else {
            // Add a new key item child
            const { children } = document.children[docItemIndex].children[keyItemIndex]
            const newCell = cloneDeep(children[children.length - 1]) // Clone the last item to use as a template
            newCell.id = getNextId(newCell.id)
            newCell.v = data.v
            newCell.pos = data.pos
            newCell.label = data.label
            document.children[docItemIndex].children[keyItemIndex].children.push(newCell)
          }
        }

        // Update the verification details in the state
        commit('SET_VERIFICATION_DETAILS', verificationDetails)
      } catch (error) {
        // Show an error toast notification on failure
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.message || 'Error updating node value',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },
    // Adds a new row to the document or its children
    async addRow({ commit, state, dispatch }, data) {
      // Helper function to increment the last segment of an ID
      const incrementId = id => {
        const parts = id.split('.')
        const lastPart = (parseInt(parts.pop(), 10) + 1).toString().padStart(3, '0') // Increment and pad
        return [...parts, lastPart].join('.')
      }

      // Helper function to increment the second last segment of an ID
      const incrementSecondLastPartOfId = id => {
        const parts = id.split('.')
        const secondLast = parts.length - 2
        parts[secondLast] = (parseInt(parts[secondLast], 10) + 1).toString().padStart(3, '0') // Increment and pad
        return parts.join('.')
      }

      try {
        const {
          batchId, documentId, keyId, keyItemId, keyItemChildId,
        } = idSplltier(data.id)

        const verificationDetails = [...state.verificationDetails] // Clone the verification details
        const dataJsonIndex = verificationDetails.findIndex(e => e.id === batchId) // Find the batch
        const docIndex = verificationDetails[dataJsonIndex].data_json.nodes.findIndex(e => e.id === documentId) // Find the document
        const document = verificationDetails[dataJsonIndex].data_json.nodes[docIndex] // Reference the document
        const docItemIndex = document.children.findIndex(e => e.id === keyId) // Find the document item

        if (!keyItemChildId) {
          // Case: Adding a new sibling to the document item
          document.children.forEach((item, index) => {
            if (index > docItemIndex) {
              // Increment IDs for items after the new insertion point
              // eslint-disable-next-line no-param-reassign
              item.id = incrementId(item.id)
              item.children.forEach(child => {
                // eslint-disable-next-line no-param-reassign
                child.id = incrementSecondLastPartOfId(child.id) // Increment child IDs
              })
            }
          })
          const copyObj = cloneDeep(document.children[docItemIndex]) // Clone the current item
          copyObj.id = incrementId(copyObj.id) // Assign a new ID
          copyObj.children = copyObj.children.map(child => ({
            ...child,
            id: incrementSecondLastPartOfId(child.id),
            pos: '',
            v: '', // Reset values for the new row
          }))
          document.children.splice(docItemIndex + 1, 0, copyObj) // Insert the new row
        } else {
          // Case: Adding a new sibling to a child item
          const keyItemIndex = document.children[docItemIndex].children.findIndex(e => e.id === keyItemId)
          document.children[docItemIndex].children.forEach((item, index) => {
            if (index > keyItemIndex) {
              // Increment IDs for items after the new insertion point
              // eslint-disable-next-line no-param-reassign
              item.id = incrementId(item.id)
              item.children.forEach(child => {
                // eslint-disable-next-line no-param-reassign
                child.id = incrementSecondLastPartOfId(child.id) // Increment child IDs
              })
            }
          })
          const copyObj = cloneDeep(document.children[docItemIndex].children[keyItemIndex]) // Clone the current child
          copyObj.id = incrementId(copyObj.id) // Assign a new ID
          copyObj.children = copyObj.children.map(child => ({
            ...child,
            id: incrementSecondLastPartOfId(child.id),
            pos: '',
            v: '', // Reset values for the new row
          }))
          document.children[docItemIndex].children.splice(keyItemIndex + 1, 0, copyObj) // Insert the new child row
        }

        dispatch('setEditableNode', null) // Reset the editable node
        verificationDetails[dataJsonIndex].data_json.nodes[docIndex] = document // Update the document
        commit('SET_VERIFICATION_DETAILS', verificationDetails) // Commit the changes
      } catch (error) {
        // Handle errors with a toast notification
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.message || 'Error updating node value',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },

    // Deletes a row from the document or its children
    async deleteRow({ commit, state, dispatch }, data) {
      try {
        const {
          batchId, documentId, keyId, keyItemId, keyItemChildId,
        } = idSplltier(data.id)

        const verificationDetails = [...state.verificationDetails]

        const dataJsonIndex = verificationDetails.findIndex(e => e.id === batchId)

        const docIndex = verificationDetails[dataJsonIndex].data_json.nodes.findIndex(e => e.id === documentId)

        const document = verificationDetails[dataJsonIndex].data_json.nodes[docIndex]

        const docItemIndex = document.children.findIndex(e => e.id === keyId)

        if (!keyItemChildId) {
          // Case: Deleting a document item
          document.children.splice(docItemIndex, 1) // Remove the item
        } else {
          // Case: Deleting a child item
          const keyItemIndex = document.children[docItemIndex].children.findIndex(e => e.id === keyItemId)
          document.children[docItemIndex].children.splice(keyItemIndex, 1) // Remove the child
        }

        dispatch('setEditableNode', null) // Reset the editable node
        verificationDetails[dataJsonIndex].data_json.nodes[docIndex] = document // Update the document
        commit('SET_VERIFICATION_DETAILS', verificationDetails) // Commit the changes
      } catch (error) {
        // Handle errors with a toast notification
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.message || 'Error updating node value',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },
    // Sets the document for verification and formats its structure
    // setDocument({
    //   state, getters, dispatch, commit,
    // }) {
    //   dispatch('setEditableNode', {})
    //   const verificationDetails = [...state.verificationDetails]
    //   // const batchId = `${getters.selectedDocumentId.split('.')[0]}.${getters.selectedDocumentId.split('.')[1]}`
    //   const { selectedBatchId } = getters
    //   const dataJsonIndex = verificationDetails.findIndex(e => e.id === selectedBatchId)
    //   const batchNodeChildren = verificationDetails[dataJsonIndex].data_json.nodes

    //   const batchNodes = [{
    //     type: 'batch',
    //     id: state.selectedBatchId,
    //     children: batchNodeChildren,
    //   }]

    //   const formatedDocuments = getVerificationDocuments(batchNodes)
    //   const structured = {
    //     [state.currentEmailBatchId]: {
    //       ...formatedDocuments,
    //     },
    //   }

    //   commit('SET_DOCUMENTS', structured)

    //   dispatch('setEditableNode', null)
    // },
    // Store Action - fetchEmailBatches (minimalistic)
    async fetchEmailBatches({ dispatch, getters, rootGetters }, batchId) {
      // Get countries data
      const countries = rootGetters['auth/selectedProjectCountries']
      const result = {}
      const currentRouteName = rootGetters['app/currentRouteName']
      countries.forEach(e => {
        const { countryCode, project } = e
        if (!result[countryCode]) {
          result[countryCode] = []
        }
        if (!result[countryCode].includes(project)) {
          result[countryCode].push(project)
        }
      })
      const countryData = {
        project_countries: { ...result },
      }
      const params = {
        page_size: 10,
        page: 1,
        sort_desc: true,
        linked_batch_id: batchId,
      }

      const response = await axios.post('/email-batches/filter_list/', countryData, { params })
      const batch = response.data.results[0]
      const batchTransactionId = batch.id
      const { selectedTransactionId } = getters
      // Check if transaction needs to be changed
      if (selectedTransactionId !== batchTransactionId) {
        await dispatch('fetchBatch', {
          selectedTransaction: batchTransactionId,
          selectFirstDocument: true,
        })
        if (currentRouteName === 'automated-table-model') {
          // const routeParams = { id: batchTransactionId }
          bus.$emit('navigate', {
            name: currentRouteName,
            params: { id: batchTransactionId },
          })
        }

        return true // Transaction changed
      }

      return false // No transaction change needed
    },

    // Updated scrollToPos action
    async scrollToPos({
      commit, state, dispatch, rootGetters,
    }, pos) {
      const [left, top, right, bottom, pageId, documentId, batchId] = pos

      // Check if transaction has changed or not
      const currentRouteName = rootGetters['app/currentRouteName']
      if (currentRouteName === 'automated-table-model') {
        await dispatch('fetchEmailBatches', batchId)
      }

      const scrollToPos = {
        pos: [left, top, right, bottom].join(','),
        pageId,
        documentId,
      }
      commit('SET_SCROLL_TO_POS', scrollToPos)

      // Check if batch has changed or not
      const batchChanged = state.batch.id !== batchId
      if (batchChanged) {
        await dispatch('changeBatch', batchId)
      }

      if (documentId !== state.selectedDocumentId) {
        commit('SET_SELECTED_DOCUMENT_ID', documentId)
        return
      }

      if (batchChanged) return

      bus.$emit('scrollToPos', scrollToPos)
      commit('SET_SCROLL_TO_POS', null)
    },

    async fetchProjectKeys({ commit, state }) {
      const res = await axios.get(`/get-project-keys/${state.profileDetails?.project_id}`)
      if (res.data) {
        commit('SET_PROJECT_KEYS', res.data)
      }
    },
    reset({ commit }) {
      commit('SET_COMBINE_VIEW', false)
      commit('SET_BATCH_ID', null)
      commit('SET_SELECTED_BATCH_ID', null)
      commit('SET_BATCH', null)
      commit('SET_SELECTED_BATCH', null)
      commit('SET_BATCHES', null)
      commit('SET_BATCH_NODES', [])
      commit('SET_NODES', [])
      commit('SET_ROOT_NODE_LIST', null)
      commit('SET_SELECTED_NODE_ID', null)
      commit('SET_EDITABLE_NODE', null)
      commit('CLEAR_NODE_CONFIG')
      commit('SET_SEARCH', '')
      commit('SET_EXPANDED_NODES', [])
      commit('SET_MATCHED_NODES', [])
      commit('SET_HIGHLIGHT_ROOT_NODES', false)
      commit('SET_ZOOM', 1)
      commit('SET_ENABLE_SELECTOR', false)
      commit('SET_VIEW', 'key')
      commit('SET_MODE', 'edit')
      commit('SET_STATUS', null)
      commit('SET_REFRESHING', false)
      commit('SET_TOTAL_PAGES', 0)
      commit('SET_DOCUMENTS', {})
      commit('SET_SELECTED_DOCUMENT_ID', null)
      commit('SET_DOCUMENT_DATA', { ...defaultDocumentData })
      commit('SET_LOADING_DOCUMENT_DATA', false)
      commit('SET_SELECTOR_POSITION', null)
      commit('SET_HIGHLIGHT_KEY_BLOCKS', false)
      commit('SET_CHUNK_DATA', {})
      commit('SET_CHUNK_DATA_PLAIN_TEXT', {})
      commit('SET_ENABLE_MEASURE', false)
      commit('SET_MEASURED_DISTANCE', null)
      commit('SET_HIGHLIGHT_KEY_ANCHORS_DATA', defaultHighlightKeyAnchorsData)
      commit('SET_SELECTED_CELL_DETAILS', null)
      commit('SET_PROFILE_DETAILS', {})
      commit('SET_HIDE_EMPTY_AUTO_EXTRACTION_KEYS', {})
      commit('SET_MATCHED_PROFILE_KEYS', [])
      commit('SET_PROJECT_KEYS', [])
      commit('SET_PROFILE_KEYS', [])
      commit('SET_PROFILE_TABLE_KEYS', [])
      commit('SET_TRANSACTION_BATCHES', {})
      commit('SET_TRANSACTION_TYPE', '')
      commit('SET_TRAINING_LINK_BATCH_ID', '')
      commit('SET_SHOW_BOTTOM_PANEL', false)
      commit('SET_SHOW_HIDE_RECOGNIZED_KEYS', false)
      commit('SET_UNDO_KEY_MAPPING_DATA', null)
      commit('SET_TRAINING_BATCHES_LINKED_IDS', [])
      commit('SET_SELECTED_TRANSACTION_PROCESS_NAME', '')
    },
    // refresh batch data
    refreshBatchData({ commit, dispatch, state }) {
      commit('SET_REFRESHING', true)
      axios.get(`/batches/${state.batch.id}/`)
        .then(res => {
          // dispatch('loadBatch', res.data)
          dispatch('atm/loadAtmPatterns', res.data?.atm_data, { root: true })
          commit('SET_REFRESHING', false)
        })
        .catch(error => {
          Vue.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error refreshing batch',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          commit('SET_REFRESHING', false)
        })
    },
    // load Chunk Data
    loadChunkData({ commit, state, rootGetters }) {
      return new Promise((resolve, reject) => {
        const { batch } = state

        const selectedTableName = rootGetters['dataView/selectedTableName']
        const { table_unique_id } = rootGetters['dataView/table'].find(table => table.table_name === selectedTableName)

        axios.post('/pipeline/chunk_data/', {
          batch_id: batch.id,
          table_unique_id,
          definition_version: rootGetters['dataView/selectedDefinitionVersion'],
        })
          .then(res => {
            const chunkDataResponse = res.data.data
            const chunkData = {}

            Object.keys(chunkDataResponse).forEach(documentId => {
              chunkData[documentId] = {
                chunkLines: [],
              }
              const chunksData = chunkDataResponse[documentId].chunking_data
              const chunkShapesData = chunkDataResponse[documentId].chunking_shape_data
              Object.keys(chunksData).forEach(pageIndex => {
                Object.keys(chunksData[pageIndex]).forEach(line => {
                  const chunks = []
                  chunksData[pageIndex][line].forEach((chunkItem, index) => {
                    chunks.push({
                      value: chunkItem[0],
                      pos: chunkItem[1],
                      pageId: chunkItem[2],
                      shape: chunkShapesData[pageIndex][line][index][0],
                    })
                  })
                  chunkData[documentId].chunkLines.push({
                    chunks,
                  })
                })
              })
            })

            commit('SET_CHUNK_DATA', chunkData)
            resolve()
          })
          .catch(error => {
            const message = error?.response?.data?.detail || 'Error loading chunk data'
            commit('SET_CHUNK_DATA', {})
            reject(new Error(message))
          })
      })
    },
    loadChunkDataWithPlainText({ commit, state }) {
      return new Promise((resolve, reject) => {
        const { batch } = state

        axios.post('/pipeline/chunk_data_plain_text/', {
          batch_id: batch.id,
          document_id: state.selectedDocumentId,
        })
          .then(res => {
            const chunkData = res.data.data

            commit('SET_CHUNK_DATA_PLAIN_TEXT', chunkData)
            resolve()
          })
          .catch(error => {
            const message = error?.response?.data?.detail || 'Error loading chunk data'
            commit('SET_CHUNK_DATA_PLAIN_TEXT', '')
            reject(new Error(message))
          })
      })
    },

    clearAnchorHighlights({ commit }) {
      commit('SET_HIGHLIGHT_KEY_ANCHORS_DATA', defaultHighlightKeyAnchorsData)
    },
    // Add helper functions at the top of your store file or import them

    // Updated fetchProfileKeys action
    fetchProfileKeys({
      getters, rootGetters, state, commit,
    }) {
      const batchId = state.selectedBatch.id
      const documentId = state.selectedDocumentId

      const batchNode = state.transactionNodes[0].children.find(e => e.type === 'batch' && e.id === batchId)
      const documentNode = batchNode.children.find(e => e.type === 'document' && e.id === documentId)
      const keyNode = documentNode.children.find(e => e.type === 'key')

      const matchedProfileKeys = keyNode?.children.filter(e => e.is_profile_key_found).map(e => e.label) || []
      // const extractedMatchedProfileKeys = keyNode?.children.filter(e => (e.is_profile_key_found && e.is_pure_autoextraction)).map(e => e.label) || []

      const qualifierNodes = keyNode?.children.filter(e => (e.qualifier_parent || '').trim()) || []
      const qualifierParentNames = qualifierNodes.map(e => e.qualifier_parent) || []
      const profileKeys = cloneDeep(getters.profileDetails?.keys) || []
      const definitionItems = rootGetters['dataView/selectedDefinition']?.key?.items || []
      const updatedKeys = []
      const definitionKeys = [] // Track definition keys separately

      // Filter profile keys to render multiple qualifier keys
      const filteredProfileKeys = profileKeys.filter(e => !qualifierParentNames.includes(e.label))
      for (let i = 0; i < qualifierNodes.length; i += 1) {
        const node = qualifierNodes[i]
        filteredProfileKeys.push({
          type: 'key',
          label: node.qualifier_parent,
          keyValue: node.qualifier_parent,
          qualifierValue: node.label,
        })
      }
      // First, add ALL definition keys exactly as-is (preserving duplicates)
      // But exclude prompt type keys as they're managed separately
      for (let i = 0; i < definitionItems.length; i += 1) {
        const defItem = definitionItems[i]
        // Skip prompt type keys - they're managed in profile.promptKeys
        if (defItem.type === 'prompt') {
          // eslint-disable-next-line no-continue
          continue
        }
        const keyWithId = {
          ...defItem,
          id: defItem.id || uuidv4(),
        }
        definitionKeys.push(keyWithId)
      }

      // Then, add profile keys that are NOT in definition as auto-type keys
      // for (let i = 0; i < filteredProfileKeys.length; i += 1) {
      //   const original = filteredProfileKeys[i]

      //   // Only handle keys of type 'key' (not 'table')
      //   if (original.type !== 'table') {
      //     // Check if this profile key already exists in definition
      //     // const isInDefinition = definitionItems.some(def => {
      //     //   const defKeyLabelCamel = def.keyLabel ? toCamelCase(def.keyLabel) : ''
      //     //   const profileKeyLabelCamel = original.label
      //     //   return defKeyLabelCamel.toLowerCase() === profileKeyLabelCamel.toLowerCase()
      //     // })

      //     // Only add as auto-type key if NOT in definition
      //     // if (!isInDefinition) {
      //     //   const transformedKey = {
      //     //     id: original.id || uuidv4(),
      //     //     type: 'auto',
      //     //     shape: '',
      //     //     endPos: '',
      //     //     export: false,
      //     //     pageId: '',
      //     //     topPos: '',
      //     //     keyLabel: original.keyValue || original.label || '',
      //     //     selector: false,
      //     //     startPos: '',
      //     //     typeData: {},
      //     //     bottomPos: '',
      //     //     pageIndex: '',
      //     //     anchorShapes: null,
      //     //     compoundItems: [],
      //     //     isCompoundKey: false,
      //     //     isCompoundItem: false,
      //     //     qualifierValue: original.qualifierValue ?? '',
      //     //     regexExtractor: null,
      //     //     advanceSettings: {},
      //     //     extractMultiple: false,
      //     //     removeDuplicates: false,
      //     //     excelRegexExtractor: null,
      //     //     singleColumnExtractor: null,
      //     //   }

      //     //   updatedKeys.push(transformedKey)
      //     // }
      //   }
      // }

      commit('SET_PROFILE_KEYS', updatedKeys)
      commit('SET_MATCHED_PROFILE_KEYS', matchedProfileKeys)
      // commit('SET_EXTRACTED_MATCHED_PROFILE_KEYS', extractedMatchedProfileKeys)

      // Get all keyLabels from definition (for checking, not for removing duplicates)
      // const definitionKeyLabelsLower = definitionKeys.map(key => (key.keyLabel || '').toLowerCase())

      // // Find matched keys from updatedKeys that are NOT in definitionKeys
      // const matchedKeysToAdd = []
      // for (let i = 0; i < extractedMatchedProfileKeys.length; i += 1) {
      //   const matchedLabel = extractedMatchedProfileKeys[i]

      //   // Skip if this keyLabel already exists in definitionKeys (case-insensitive)
      //   if (definitionKeyLabelsLower.includes(matchedLabel.toLowerCase())) {
      //     // eslint-disable-next-line no-continue
      //     continue
      //   }

      //   // Find the key from updatedKeys that matches this extractedMatchedProfileKey
      //   let keyToAdd = updatedKeys.find(key => {
      //     const normalizedKeyLabel = key.keyLabel || ''
      //     return normalizedKeyLabel.toLowerCase() === matchedLabel.toLowerCase()
      //   })

      //   if (keyToAdd) {
      //     // Ensure the type is 'auto' for extracted matched profile keys
      //     keyToAdd = { ...keyToAdd, type: 'auto' }
      //     matchedKeysToAdd.push(keyToAdd)
      //   }
      // }

      // // Combine: definitionKeys (can have duplicates) + extracted matched keys
      // const combinedKeys = [...definitionKeys, ...matchedKeysToAdd]

      // commit('SET_PROFILE_AND_DEFINITION_KEYS', combinedKeys)
    },
    fetchProfileTableKeys({ getters, commit }) {
      const profileTKeys = getters.profileDetails?.keys || []
      const findTableKeys = profileTKeys.filter(k => k.type === 'table')

      commit('SET_PROFILE_TABLE_KEYS', findTableKeys)
    },
  },

  // All the getters for batches
  getters: {
    showBottomPanel(state) {
      return state.showBottomPanel
    },
    isCombineView(state) {
      return state.isCombineView
    },
    isKeyRecognized(state) {
      return state.isKeyRecognized
    },
    batch(state) {
      return state.batch
    },
    selectedBatch(state) {
      return state.selectedBatch
    },
    batches(state) {
      return state.batches
    },
    batchNodes(state) {
      return state.batchNodes
    },
    batchesIds(state) {
      return state.batchesIds
    },
    trainingBatchLinkedIds(state) {
      return state.trainingLinkedBatchIds
    },
    verificationStatus(state) {
      return state.verificationStatus
    },
    manualValidation(state) {
      return state.manualValidation
    },
    multiShipment(state) {
      return state.multiShipment
    },
    verificationDetails(state) {
      return state.verificationDetails
    },
    matchedNodes(state) {
      return state.matchedNodes
    },
    nodeConfig(state) {
      return state.nodeConfig
    },
    editableNode(state) {
      return state.editableNode
    },
    selectedNode(state) {
      if (state.selectedNodeId) {
        return {
          id: state.selectedNodeId,
          ...state.nodes[state.selectedNodeId],
        }
      }
      return null
    },
    selectedPageId(state, getters) {
      return getters.selectedNode ? getters.selectedNode.pageId : null
    },
    highlightRootNodes(state) {
      return state.highlightRootNodes
    },
    search(state) {
      return state.search
    },
    isExpandedNode: state => id => state.expandedNodes.includes(id),
    isMatchedNode: state => id => state.matchedNodes.includes(id),
    zoom(state) {
      return state.zoom
    },
    enableSelector(state) {
      return state.enableSelector
    },
    enableMeasure(state) {
      return state.enableMeasure
    },
    rootNodeList(state) {
      return state.rootNodeList
    },
    expandedNodes: state => state.expandedNodes,
    // flatNodes(state, getters, rootGetters) {
    //   const addressBlockKeys = []
    //   const { options } = rootGetters.definitionSettings

    //   if (Object.keys(options).length) {
    //     options['options-keys'].items.forEach(e => {
    //       if (e.type === 'addressBlock') {
    //         addressBlockKeys.push(e.keyValue)
    //       }
    //     })
    //   }

    //   return getFlatNodes(state.batchNodes, state.expandedNodes, state.matchedNodes, getters.selectedNode,
    //     state.highlightRootNodes, addressBlockKeys)
    // },
    view(state) {
      return state.view
    },
    mode(state) {
      return state.mode
    },
    status(state) {
      return state.status
    },
    refreshing(state) {
      return state.refreshing
    },
    documents(state) {
      return state.documents
    },
    totalPages(state) {
      return state.totalPages
    },
    selectedDocumentId(state) {
      return state.selectedDocumentId
    },
    // selectedDocument(state, getters) {
    //   if (getters.selectedDocumentId) {
    //     return {
    //       id: getters.selectedDocumentId,
    //       ...state.documents[getters.selectedDocumentId],
    //     }
    //   }
    //   return null
    // },
    selectedDocumentIndex(state) {
      if (!state.selectedDocumentId) {
        return -1
      }

      return Object.keys(state.documents).findIndex(documentId => documentId === state.selectedDocumentId)
    },
    selectedDocumentKeysForLookup(state, getters) {
      if (!state.selectedDocumentId) {
        return []
      }

      const { keys } = getters.selectedDocument

      return keys.filter(key => key.qualifierParent !== 'references').map(key => ({
        label: key.label,
        value: key.value,
      }))
    },
    selectedPage(state, getters) {
      if (getters.selectedDocument && getters.selectedPageId) {
        const page = state.documentData.pages[getters.selectedPageId]
        if (!page) {
          return null
        }
        return {
          id: getters.selectedPageId,
          ...page,
        }
      }
      return null
    },
    documentData(state) {
      return state.documentData
    },
    loadingDocumentData(state) {
      return state.loadingDocumentData
    },
    selectorPosition(state) {
      return state.selectorPosition
    },
    measuredDistance(state) {
      return state.measuredDistance
    },
    highlightKeyBlocks(state) {
      if (state.view !== 'analyzer') {
        return false
      }

      return state.highlightKeyBlocks
    },
    chunkData(state) {
      if (!state.selectedDocumentId) {
        return null
      }
      return state.chunkData[state.selectedDocumentId]
    },
    chunkDataWithPlainText(state) {
      return state.chunkDataWithPlainText
    },
    highlightKeyAnchorsData(state) {
      return state.highlightKeyAnchorsData
    },
    displayKeyAnchors(state, getters, rootState, rootGetters) {
      const { keyItemId, source } = state.highlightKeyAnchorsData
      if (keyItemId === null) {
        return false
      }
      const keyItems = rootGetters[`dataView/${source}`]
      const keyItem = getKeyItemById(keyItems, keyItemId)
      if (!keyItem) {
        return false
      }

      if (keyItem.type === 'anchors') {
        if (!keyItem.anchorShapes || keyItem.anchorShapes == null) {
          return false
        }
      }

      if (keyItem.type === 'regexExtractor') {
        if (!keyItem.regexExtractor || keyItem.regexExtractor == null) {
          return false
        }
      }

      return true
    },
    keyAnchorsData(state, getters, rootState, rootGetters) {
      if (!getters.displayKeyAnchors) {
        return null
      }
      const { keyItemId, selectedAnchor, source } = state.highlightKeyAnchorsData
      const keyItems = rootGetters[`dataView/${source}`]
      const keyItem = getKeyItemById(keyItems, keyItemId)

      let anchorShapes
      if (keyItem.type === 'anchors') {
        anchorShapes = keyItem.anchorShapes
      } else if (keyItem.type === 'regexExtractor') {
        anchorShapes = keyItem.regexExtractor.anchors
      }

      return {
        ...anchorShapes,
        selectedAnchor,
      }
    },
    error(state) {
      return state.error
    },
    testOptions(state) {
      return state.testOptions
    },
    selectedCellDetails(state) {
      return state.selectedCellDetails
    },
    positionShiftData(state) {
      return state.positionShiftData
    },
    getIsAddRow(state) {
      return state.isAddRow
    },
    getIsDeleteRow(state) {
      return state.isDeleteRow
    },
    getIsAnyDeletableRow(state) {
      return state.isAnyDeletableRow
    },
    getTempImageList(state) {
      return state.tempImageList
    },
    getTopPaneSize(state) {
      return state.topPaneSize
    },
    // Add these getters
    transaction(state) {
      return state.transaction
    },
    transactionBatches(state) {
      return state.transactionBatches
    },
    transactionNodes(state) {
      return state.transactionNodes
    },

    // Update the selectedDocument getter
    selectedDocument(state, getters) {
      if (getters.selectedDocumentId && state.selectedTransactionId && state.selectedBatchId) {
        const documentData = state.documents?.[state.selectedTransactionId]?.[state.selectedBatchId]?.[getters.selectedDocumentId]
        if (documentData) {
          return {
            id: getters.selectedDocumentId,
            ...documentData,
          }
        }
      }
      return null
    },

    // Update the flatNodes getter to use transaction nodes
    flatNodes(state, getters) {
      const addressBlockKeys = []
      // const { options } = rootGetters.definitionSettings

      // if (Object.keys(options).length) {
      //   options['options-keys'].items.forEach(e => {
      //     if (e.type === 'addressBlock') {
      //       addressBlockKeys.push(e.keyValue)
      //     }
      //   })
      // }

      // Use transactionNodes instead of batchNodes to get the full hierarchy
      // Touch version to ensure dependency on sort changes
      // eslint-disable-next-line no-unused-expressions
      state.documentSortVersion
      return getFlatNodes(state.transactionNodes, state.expandedNodes, state.matchedNodes, getters.selectedNode,
        state.highlightRootNodes, addressBlockKeys, state.documentSortOrder)
    },

    // Getter for document sort order
    documentSortOrder(state) {
      return state.documentSortOrder
    },

    // Add selectedTransactionId and selectedBatchId getters
    selectedTransactionId(state) {
      return state.selectedTransactionId
    },
    selectedBatchId(state) {
      return state.selectedBatchId
    },
    profileDetails(state) {
      return state.profileDetails
    },
    matchedProfileKeys(state) {
      return state.matchedProfileKeys
    },
    extractedMatchedProfileKeys(state) {
      return state.extractedMatchedProfileKeys
    },
    projectKeys(state) {
      return state.projectAllKeys
    },
    profileKeys(state) {
      return state.profileKeys
    },
    // profileDefinitionKeys(state) {
    //   // Return only definition keys - prompt keys are managed separately
    //   // and merged at the component level when needed
    //   return state.profileDefinitionKeys || []
    // },
    profileTableKeys(state) {
      return state.profileTableKeys
    },
    getTransactionType(state) {
      return state.transactionType
    },
    getTrainingLinkBatchId(state) {
      return state.tainingBatchLinkId
    },
    isProfileLoadig(state) {
      return state.isProfileLoadig
    },
    tableExistsInSelectedDocument: (state, getters) => tableName => {
      const selectedDoc = getters.selectedDocument
      if (selectedDoc?.children && Array.isArray(selectedDoc.children)) {
        return selectedDoc.children.some(child => child.type === 'table'
        && (child.table_name === tableName
         || child.name === tableName
         || child.id === tableName))
      }
      return false
    },
    undoKeyMappingData(state) {
      return state.undoKeyMappingData
    },
    hideEmptyAutoExtrationKeys(state) {
      return state.hideEmptyAutoExtrationKeys
    },
    scrollToPos(state) {
      return state.scrollToPos
    },
    selectedTransactionProcess(state) {
      return state.selectedTransactionProcess
    },
  },
}
