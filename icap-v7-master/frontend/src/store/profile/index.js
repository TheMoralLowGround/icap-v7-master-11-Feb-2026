// store/modules/profileCreation.js
import axios from 'axios'
// import { normalizeProcessName } from '@/utils/normalize'
// PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
// import { v4 as uuidv4 } from 'uuid'

const getDefaultState = () => ({
  keys: [],
  emailDomains: null,
  processId: null,
  processUid: null,
  currentProcessName: null,
  dictionariesProcess: null, // Single process object, not an array
  emailFrom: null,
  emailSubjectMatchOption: 'ProcessId',
  emailSubjectMatchText: null,
  generalInfo: {
    id: null,
    name: '',
    freeName: '',
    project: '',
    countryCode: '',
    // modeOfTransport: '',
  },
  docTypes: [],
  manualValidation: false,
  multiShipment: false,
  sendTimeStamp: false,
  automaticSplitting: false,
  ignoreDensePages: false,
  exceptionalExcel: false,
  success_notify_email_sender: false,
  success_notify_email_recipients: false,
  success_notify_additional_emails: null,
  success_notify_exclude_emails: null,
  failure_notify_email_sender: false,
  failure_notify_email_recipients: false,
  failure_notify_additional_emails: null,
  failure_notify_exclude_emails: null,
  customers: [],
  process_customers: [],
  documents: [],
  translated_documents: [],
  generalFormValid: false,
  classifiableDocTypes: [],
  selectDefaultKeys: false,
  lookupItems: [],
  partiesConfigTable: [], // Array structure: [{ table: 'CUSTOM_MASTER', columns: [] }]
  partiesDynamicColumn: {},
  selecedProcessName: '',
  dictionaries: [], // Array structure: [{ name: 'dict_name', columns: [], data: [] }]
  // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
  // promptKeys: [],
  // updatePromptKeys: null,
})
export default {
  namespaced: true,
  state: getDefaultState(),
  mutations: {
    SET_SELECTED_KEYS(state, keys) {
      state.keys = keys
    },
    SET_DICTIONARIES(state, dictionaries) {
      state.dictionaries = dictionaries
    },
    SET_DICTIONARIES_PROCESS(state, processes) {
      state.dictionariesProcess = processes
    },
    SET_PROMPT_KEYS(state, value) {
      state.promptKeys = value
    },
    UPDATE_PROMPT_KEYS(state, value) {
      state.updatePromptKeys = value
    },
    SET_PARTIES_DYNAMIC_COLUMNS(state, columns) {
      state.partiesDynamicColumn = columns
    },
    SET_LOOKUP_ITEMS(state, lookupItems) {
      state.lookupItems = lookupItems
    },
    ADD_KEY(state, key) {
      if (!state.keys.some(k => k.keyValue === key.keyValue)) {
        state.keys.push(key)
      }
    },
    REMOVE_KEY(state, keyValue) {
      state.keys = state.keys.filter(k => k.keyValue !== keyValue)
    },
    UPDATE_DOCUMENTS(state, documents) {
      state.documents = documents
    },
    UPDATE_DOCUMENT_BY_INDEX(state, payload) {
      state.documents.splice(payload.index, 1, payload.updatedDoc)
    },
    UPDATE_DOCUMENT(state, { id, updatedDoc }) {
      const index = state.documents.findIndex(doc => doc.id === id)
      if (index !== -1) {
        state.documents.splice(index, 1, updatedDoc)
      }
    },
    ADD_DOCUMENT(state, document) {
      // Fix for the replacement issue - we now properly add to the array
      state.documents = [...state.documents, document]
    },
    REMOVE_DOCUMENT(state, index) {
      state.documents.splice(index, 1)
    },
    REMOVE_DOCUMENT_BY_ID(state, id) {
      state.documents = state.documents.filter(doc => doc.id !== id)
    },
    SET_TRANSLATED_DOCUMENTS(state, translatedDocuments) {
      state.translated_documents = translatedDocuments
    },
    // Customer mutations
    updateCustomers(state, customers) {
      state.customers = customers
    },
    addCustomer(state, customer) {
      state.customers = [...state.customers, customer]
    },
    updateCustomer(state, { index, customer }) {
      if (index >= 0 && index < state.customers.length) {
        // Create a new array with the updated customer
        state.customers = [
          ...state.customers.slice(0, index),
          customer,
          ...state.customers.slice(index + 1),
        ]
      }
    },
    removeCustomer(state, index) {
      if (index >= 0 && index < state.customers.length) {
        state.customers.splice(index, 1)
      }
    },

    // Process Customer mutations
    UPDATE_PROCESS_CUSTOMERS(state, customers) {
      state.process_customers = customers
    },
    ADD_PROCESS_CUSTOMER(state, customer) {
      state.process_customers = [...state.process_customers, customer]
    },
    UPDATE_PROCESS_CUSTOMER(state, { index, customer }) {
      if (index >= 0 && index < state.process_customers.length) {
        state.process_customers = [
          ...state.process_customers.slice(0, index),
          customer,
          ...state.process_customers.slice(index + 1),
        ]
      }
    },
    REMOVE_PROCESS_CUSTOMER(state, index) {
      if (index >= 0 && index < state.process_customers.length) {
        state.process_customers.splice(index, 1)
      }
    },

    // Email settings mutation
    updateEmailSettings(state, settings) {
      state.emailSettings = settings
    },
    loadState(state, payload) {
      Object.assign(state, payload)
    },
    loadProfile(state, payload) {
      state.generalInfo = {
        id: payload?.id || null,
        name: payload?.free_name || '',
        freeName: payload?.free_name || '',
        project: payload?.project || '',
        countryCode: payload?.country || '',
        // modeOfTransport: payload?.mode_of_transport || '',
      }
      state.currentProcessName = payload.name
      state.exceptionalExcel = payload?.exceptional_excel
      state.manualValidation = payload?.manual_validation
      state.multiShipment = payload?.multi_shipment
      state.automaticSplitting = payload?.automatic_splitting
      state.ignoreDensePages = payload?.ignore_dense_pages
      state.sendTimeStamp = payload?.send_time_stamp
      state.success_notify_email_sender = payload?.success_notify_email_sender || false
      state.success_notify_email_recipients = payload?.success_notify_email_recipients || false
      state.success_notify_additional_emails = payload?.success_notify_additional_emails || null
      state.success_notify_exclude_emails = payload?.success_notify_exclude_emails || null
      state.failure_notify_email_sender = payload?.failure_notify_email_sender || false
      state.failure_notify_email_recipients = payload?.failure_notify_email_recipients || false
      state.failure_notify_additional_emails = payload?.failure_notify_additional_emails || null
      state.failure_notify_exclude_emails = payload?.failure_notify_exclude_emails || null
      state.customers = payload?.customers || []
      state.process_customers = payload?.process_customers || []
      state.documents = payload?.documents || []
      state.lookupItems = payload?.lookup_items || []
      state.translated_documents = payload?.translated_documents || []
      state.keys = payload?.keys || []
      state.emailDomains = payload.email_domains
      state.emailFrom = payload.email_from
      state.emailSubjectMatchOption = payload?.email_subject_match_option || 'ProcessId'
      state.emailSubjectMatchText = payload?.email_subject_match_text || null
      state.processId = payload?.process_id || null
      state.processUid = payload?.process_uid || null
      state.partiesConfigTable = payload?.parties_config || []
      state.selecedProcessName = payload?.name || ''
    },
    updateGeneralInfo(state, payload) {
      state.generalInfo = { ...state.generalInfo, ...payload }
    },
    updateSettings(state, payload) {
      state.settings = { ...state.settings, ...payload }
    },
    updateDocuments(state, documents) {
      state.documents = documents
    },
    // Boolean settings mutations
    updateManualValidation(state, value) {
      state.manualValidation = value
    },
    updateMultiShipment(state, value) {
      state.multiShipment = value
    },
    updateSendTimeStamp(state, value) {
      state.sendTimeStamp = value
    },
    updateAutomaticSplitting(state, value) {
      state.automaticSplitting = value
    },
    updateIgnoreDensePages(state, value) {
      state.ignoreDensePages = value
    },
    updateExceptionalExcel(state, value) {
      state.exceptionalExcel = value
    },
    updateSuccessNotifyEmailSender(state, value) {
      state.success_notify_email_sender = value
    },
    updateSuccessNotifyEmailRecipients(state, value) {
      state.success_notify_email_recipients = value
    },
    updateFailureNotifyEmailSender(state, value) {
      state.failure_notify_email_sender = value
    },
    updateFailureNotifyEmailRecipients(state, value) {
      state.failure_notify_email_recipients = value
    },
    updateSuccessNotifyAdditionalEmails(state, value) {
      state.success_notify_additional_emails = value
    },
    updateSuccessNotifyExcludeEmails(state, value) {
      state.success_notify_exclude_emails = value
    },
    updateFailureNotifyAdditionalEmails(state, value) {
      state.failure_notify_additional_emails = value
    },
    updateFailureNotifyExcludeEmails(state, value) {
      state.failure_notify_exclude_emails = value
    },
    // Email settings mutations
    updateEmailDomains(state, value) {
      state.emailDomains = value
    },
    updateEmailFrom(state, value) {
      state.emailFrom = value
    },
    updateEmailSubjectMatchOption(state, value) {
      state.emailSubjectMatchOption = value
    },
    updateEmailSubjectMatchText(state, value) {
      state.emailSubjectMatchText = value
    },
    resetState(state) {
      Object.assign(state, getDefaultState())
    },
    setGeneralFormValid(state, isValid) {
      state.generalFormValid = isValid
    },
    SET_CLASSIFIABLE_DOC_TYPES(state, docTypes) {
      state.classifiableDocTypes = docTypes
    },
    updateSelectDefaultKeys(state, value) {
      state.selectDefaultKeys = value
    },
    setProcessId(state, processId) {
      state.processId = processId
    },

    clearProcessId(state) {
      state.processId = null
    },

    setProcessUid(state, processUid) {
      state.processUid = processUid
    },

    clearProcessUid(state) {
      state.processUid = null
    },

    // Parties Table mutations
    SET_PARTIES_TABLE(state, partiesConfigTable) {
      state.partiesConfigTable = partiesConfigTable
    },
    UPDATE_PARTIES_TABLE_COLUMNS(state, { tableName, columns }) {
      const tableIndex = state.partiesConfigTable.findIndex(t => t.table === tableName)
      if (tableIndex !== -1) {
        state.partiesConfigTable[tableIndex].columns = columns
      } else {
        state.partiesConfigTable.push({ table: tableName, columns })
      }
    },
    REMOVE_PARTIES_TABLE(state, tableName) {
      state.partiesConfigTable = state.partiesConfigTable.filter(t => t.table !== tableName)
    },
    SET_PARTIES_DYNAMIC_COLUMN(state, columnData) {
      state.partiesDynamicColumn = columnData
    },
  },
  actions: {
    initializeNewProfile({ commit }) {
      commit('resetState')
    },
    async loadProfile({ commit }, profileId) {
      const response = await axios.get(`/dashboard/profiles/${profileId}/`)
      commit('loadProfile', response.data)
    },
    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // async getPromptKeys({ commit, rootGetters, dispatch }) {
    //   const processName = rootGetters['batch/selectedTransactionProcess']
    //   const response = await axios.get('/dashboard/profiles/get_process_prompt_keys/', {
    //     params: { process_name: processName },
    //   })

    //   // Transform backend format to keyItem format
    //   const transformedKeys = (response.data || []).map(item => ({
    //     id: uuidv4(),
    //     keyLabel: item.keyValue || item.label,
    //     qualifierValue: '',
    //     type: 'prompt',
    //     prompt: item.prompt || {},
    //     startPos: '',
    //     topPos: '',
    //     endPos: '',
    //     bottomPos: '',
    //     pageId: '',
    //     pageIndex: '',
    //     anchorShapes: null,
    //     selector: false,
    //     extractMultiple: false,
    //     removeDuplicates: false,
    //     singleColumnExtractor: null,
    //     regexExtractor: null,
    //     advanceSettings: {},
    //     typeData: {},
    //     isCompoundKey: false,
    //     compoundItems: [],
    //     isCompoundItem: false,
    //     keyItemValues: {
    //       startPos: '',
    //       endPos: '',
    //       topPos: '',
    //       bottomPos: '',
    //       pageIndex: '',
    //       pageId: '',
    //       selectedText: '',
    //     },
    //     keyItemLabels: {
    //       startPos: '',
    //       endPos: '',
    //       topPos: '',
    //       bottomPos: '',
    //       pageIndex: '',
    //       pageId: '',
    //       selectedText: '',
    //     },
    //   }))

    //   commit('SET_PROMPT_KEYS', transformedKeys)

    //   // After fetching prompt keys, merge them into the definition's key.items
    //   // This ensures they appear in the UI alongside definition keys
    //   dispatch('dataView/mergePromptKeysIntoDefinition', null, { root: true })
    // },
    // async updatePromptKeys({ commit, rootGetters }, keys) {
    //   const processName = rootGetters['batch/selectedTransactionProcess']
    //   const payload = {
    //     process_name: processName,
    //     keys,
    //   }
    //   const response = await axios.patch('/dashboard/profiles/update_process_prompt_keys/', payload)
    //   commit('UPDATE_PROMPT_KEYS', response.data)
    // },
    // COMMENTED OUT: Using projectKeyItems filtering instead of dynamic columns API
    // async fetchPartiesDynamicColumn({ commit }) {
    //   try {
    //     const response = await axios.get('/lookup/dynamic_columns/')
    //     commit('SET_PARTIES_DYNAMIC_COLUMN', response.data?.data || {})
    //     return response.data?.data || {}
    //   } catch (error) {
    //     // eslint-disable-next-line no-console
    //     console.error('Error fetching parties dynamic columns:', error)
    //     commit('SET_PARTIES_DYNAMIC_COLUMN', {})
    //     return {}
    //   }
    // },
    async fetchAutomaticClassifiableDocTypes({ commit }) {
      const response = await axios.get('/pipeline/automatic_classifiable_doc_types/')
      commit('SET_CLASSIFIABLE_DOC_TYPES', response.data.map(docType => docType?.toLowerCase()))
    },
    async createDictionaryTable({ state }, { name, description, columns }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to create a dictionary table')
      }

      const payload = {
        name,
        description: description || `${name} table`,
        column_schema: columns,
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', payload, {
        params: {
          endpoint: `dictionaries/tables/${processUid}/`,
          request_type: 'POST',
        },
      })

      return response.data
    },
    async fetchAllDictionaries({ state, commit }) {
      try {
        const { processUid } = state
        if (!processUid) {
          throw new Error('Process UID is required to fetch dictionaries')
        }

        const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
          params: {
            endpoint: `dictionaries/tables/${processUid}/formatted`,
            request_type: 'GET',
          },
        })

        commit('SET_DICTIONARIES', response.data)
        return response.data
      } catch (error) {
        // Set empty array on error - silent fail for non-critical operation
        commit('SET_DICTIONARIES', [])
        throw error
      }
    },
    async fetchDictionariesProcesses({ state, commit }) {
      try {
        const { processUid } = state
        if (!processUid) {
          throw new Error('Process UID is required to search for a process')
        }

        const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
          params: {
            endpoint: `dictionaries/processes/${processUid}`,
            request_type: 'GET',
          },
        })

        // Response is an object, not an array
        commit('SET_DICTIONARIES_PROCESS', response.data)
        return response.data
      } catch (error) {
        // Set null on error - silent fail for non-critical operation
        commit('SET_DICTIONARIES_PROCESS', null)
        throw error
      }
    },
    async createDictionariesProcess({ state, commit }) {
      const { processUid, processId, selecedProcessName } = state
      if (!processUid) {
        throw new Error('Process UID is required to create dictionaries process')
      }

      const payload = {
        process_uid: processUid,
        process_id: processId || null,
        display_name: selecedProcessName || null,
        description: selecedProcessName || processUid,
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', payload, {
        params: {
          endpoint: 'dictionaries/processes',
          request_type: 'POST',
        },
      })

      // Store the created process in state
      commit('SET_DICTIONARIES_PROCESS', response.data)

      return response.data
    },
    async ensureDictionariesProcessExists({ state, dispatch }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required')
      }

      // Try to fetch the specific process
      try {
        await dispatch('fetchDictionariesProcesses')
        // If successful, the process exists and is stored in state
        return true
      } catch (error) {
        // Process doesn't exist, create it
        await dispatch('createDictionariesProcess')
        return true
      }
    },
    // Parties Process Management (similar to dictionaries)
    async fetchPartiesProcesses({ state }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to search for parties process')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `parties/processes/${processUid}`,
          request_type: 'GET',
        },
      })

      return response.data
    },
    async createPartiesProcess({ state }) {
      const { processUid, processId, selecedProcessName } = state
      if (!processUid) {
        throw new Error('Process UID is required to create parties process')
      }

      const payload = {
        process_uid: processUid,
        process_id: processId || null,
        display_name: selecedProcessName || null,
        description: selecedProcessName || processUid,
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', payload, {
        params: {
          endpoint: 'parties/processes',
          request_type: 'POST',
        },
      })

      return response.data
    },
    async ensurePartiesProcessExists({ state, dispatch }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required')
      }

      // Try to fetch the specific process
      try {
        await dispatch('fetchPartiesProcesses')
        // If successful, the process exists
        return true
      } catch (error) {
        // Process doesn't exist, create it
        await dispatch('createPartiesProcess')
        return true
      }
    },
    async updateDictionaryColumns({ state }, { tableName, columns }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to update dictionary columns')
      }

      // Send only the columns array directly - no wrapper object
      const response = await axios.post('/pipeline/qdrant_vector_db/', columns, {
        params: {
          endpoint: `dictionaries/tables/${processUid}/${tableName}/schema`,
          request_type: 'PUT',
        },
      })

      return response.data
    },
    async addDictionaryRecord({ state }, { tableName, record }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to add dictionary record')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', record, {
        params: {
          endpoint: `dictionaries/table-rows/${processUid}/${tableName}`,
          request_type: 'POST',
        },
      })

      return response.data
    },
    async updateDictionaryRecord({ state }, { tableName, recordId, record }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to update dictionary record')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', record, {
        params: {
          endpoint: `dictionaries/table-rows/${processUid}/${tableName}/${recordId}`,
          request_type: 'PUT',
        },
      })

      return response.data
    },
    async deleteDictionaryRecord({ state }, { tableName, rowId }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to delete dictionary record')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `dictionaries/table-rows/${processUid}/${tableName}/${rowId}`,
          request_type: 'DELETE',
        },
      })

      return response.data
    },
    async deleteDictionaryTable({ state }, { tableName }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to delete dictionary table')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `dictionaries/tables/${processUid}/${tableName}`,
          request_type: 'DELETE',
        },
      })

      return response.data
    },
    async deleteDictionaryColumn({ state }, { tableName, columnKey }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to delete dictionary column')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `dictionaries/tables/${processUid}/${tableName}/columns/${columnKey}`,
          request_type: 'DELETE',
        },
      })

      return response.data
    },
    async updateDictionaryDescription({ state }, { tableName, description }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to update dictionary description')
      }

      const payload = {
        description,
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', payload, {
        params: {
          endpoint: `dictionaries/tables/${processUid}/${tableName}/description`,
          request_type: 'PUT',
        },
      })

      return response.data
    },
    // Parties actions (similar to dictionaries but for parties tables)
    async addPartyRecord({ state }, { tableName, record }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to add party record')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', record, {
        params: {
          endpoint: `parties/table-rows/${processUid}/${tableName}`,
          request_type: 'POST',
        },
      })

      return response.data
    },
    async updatePartyRecord({ state }, { tableName, recordId, record }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to update party record')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', record, {
        params: {
          endpoint: `parties/table-rows/${processUid}/${tableName}/${recordId}`,
          request_type: 'PUT',
        },
      })

      return response.data
    },
    async deletePartyRecords({ state }, { tableName, ids }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to delete party records')
      }

      // Delete each record individually
      const deletePromises = ids.map(id => axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `parties/table-rows/${processUid}/${tableName}/${id}`,
          request_type: 'DELETE',
        },
      }))

      await Promise.all(deletePromises)

      return { success: true }
    },
    async fetchPartyTableFormatted({ state }, { tableName }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to fetch party table')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `parties/tables/${processUid}/${tableName}/formatted`,
          request_type: 'GET',
        },
      })

      return response.data
    },
    async fetchAllPartyTables({ state }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to fetch party tables')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `parties/tables/${processUid}`,
          request_type: 'GET',
        },
      })

      return response.data
    },
    async createPartyTable({ state }, {
      name, description, columns, force,
    }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to create party table')
      }

      const payload = {
        name,
        description: description || null,
        column_schema: columns, // Match dictionaries structure with column_schema
      }

      // Add force parameter if provided
      if (force) {
        payload.force = true
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', payload, {
        params: {
          endpoint: `parties/tables/${processUid}/`,
          request_type: 'POST',
        },
      })

      return response.data
    },
    async deletePartyTable({ state }, { tableName }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to delete party table')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `parties/tables/${processUid}/${tableName}/`,
          request_type: 'DELETE',
        },
      })

      return response.data
    },
    async updatePartyColumns({ state }, { tableName, columns }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to update party columns')
      }

      // Send columns array directly - identical to dictionaries
      const response = await axios.post('/pipeline/qdrant_vector_db/', columns, {
        params: {
          endpoint: `parties/tables/${processUid}/${tableName}/schema`,
          request_type: 'PUT',
        },
      })

      return response.data
    },
    async deletePartyColumn({ state }, { tableName, columnKey }) {
      const { processUid } = state
      if (!processUid) {
        throw new Error('Process UID is required to delete party column')
      }

      const response = await axios.post('/pipeline/qdrant_vector_db/', {}, {
        params: {
          endpoint: `parties/tables/${processUid}/${tableName}/columns/${columnKey}`,
          request_type: 'DELETE',
        },
      })

      return response.data
    },
  },
  getters: {
    keys: state => state.keys,
    documents: state => state.documents,
    translated_documents: state => state.translated_documents,
    partiesDynamicColumn: state => state.partiesDynamicColumn,
    selecedProcessName: state => state.selecedProcessName,
    dictionaries: state => state.dictionaries,
    dictionariesProcess: state => state.dictionariesProcess,
    profilePayload: state => ({
      ...state.generalInfo,
      customers: state.customers,
      process_customers: state.process_customers,
      documents: state.documents,
    }),
    process_customers: state => state.process_customers,
    processId(state) {
      return state.processId
    },
    processUid(state) {
      return state.processUid
    },
    currentProcessName(state) {
      return state.currentProcessName
    },
    lookupItems: state => state.lookupItems,
    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // getPromptKeys: state => state.getPromptKeys,
    // promptKeys: state => state.promptKeys,
  },
}
