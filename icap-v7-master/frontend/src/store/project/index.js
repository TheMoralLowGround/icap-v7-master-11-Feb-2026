import axios from 'axios'
import { cloneDeep, merge } from 'lodash'
import Vue from 'vue'
import projectSettings from './helper'

export default {
  namespaced: true,

  state: {
    project: cloneDeep(projectSettings),
    keyQualifiers: [],
    compoundKeyName: [],
    testResult: null,
    outputTestResult: null,
    outputGetResult: null,
    outputTestJson: null,
    inputLogs: [],
    isProjectLoading: false,
  },

  mutations: {
    RESET_PROJECT(state) {
      state.project = cloneDeep(projectSettings)
      state.isProjectLoading = false
    },

    SET_PROJECT_LOADING(state, isLoading) {
      state.isProjectLoading = isLoading
    },

    SET_OUTPUT_TEST_RESULT(state, res) {
      state.outputTestJson = res
    },
    SET_OUTPUT_TEST_JSON(state, res) {
      state.outputTestResult = res
    },
    SET_OUTPUT_POST_RESULT(state, res) {
      state.outputPostResult = res
    },
    GET_OUTPUT_RESULT(state, res) {
      state.outputGetResult = res
    },
    SET_INPUT_LOGS(state, res) {
      state.inputLogs = res
    },
    SET_PROJECT(state, payload) {
      state.project = payload
    },

    ADD_KEY_ITEM(state, item) {
      state.project.settings.options['options-keys'].items.unshift(item)
    },

    UPDATE_KEY_ITEM(state, { index, updatedItem }) {
      Vue.set(state.project.settings.options['options-keys'].items, index, updatedItem)
    },

    DELETE_KEY_ITEM(state, index) {
      state.project.settings.options['options-keys'].items.splice(index, 1)
    },
    SET_KEY_ITEMS(state, items) {
      state.project.settings.options['options-keys'].items = items
    },

    SET_DOC_TYPES(state, items) {
      state.project.settings.options['options-meta-root-type'].items = items
    },

    SET_MAPPED_KEY(state, items) {
      state.project.settings.options['options-mapped-keys'].items = items
    },

    ADD_KEY_QUALIFIER(state, qualifier) {
      if (!state.project.settings.keyQualifiers) {
        state.project.settings.keyQualifiers = []
      }
      state.project.settings.keyQualifiers.push(qualifier)
    },

    SET_KEY_QUALIFIER(state, { index, item }) {
      if (Array.isArray(state.project.settings.keyQualifiers)) {
        Vue.set(state.project.settings.keyQualifiers, index, item)
      }
    },

    REMOVE_KEY_QUALIFIER(state, index) {
      state.project.settings.keyQualifiers.splice(index, 1)
    },

    SET_QUALIFIER_OPTIONS(state, { qualifierName, options }) {
      const qualifier = state.project.settings.keyQualifiers?.find(q => q.name === qualifierName)
      if (qualifier) {
        qualifier.options = options
      }
    },

    UPDATE_QUALIFIER_OPTIONS(state, { qualifierName, options }) {
      const qualifier = state.project.settings.keyQualifiers?.find(q => q.name === qualifierName)
      if (qualifier) {
        qualifier.options = options
      }
    },
    ADD_COMPOUND_KEYS(state, compoundKeys) {
      if (!state.project.settings.compoundKeys) {
        state.project.settings.compoundKeys = []
      }
      state.project.settings.compoundKeys.push(compoundKeys)
    },

    SET_COMPOUND_KEYS(state, { index, item }) {
      if (Array.isArray(state.project.settings.compoundKeys)) {
        Vue.set(state.project.settings.compoundKeys, index, item)
      }
    },

    REMOVE_COMPOUND_KEYS(state, index) {
      state.project.settings.compoundKeys.splice(index, 1)
    },

    SET_COMPOUND_KEY_OPTIONS(state, { compoundKeyName, options }) {
      const compoundKey = state.project.settings.compoundKeys?.find(q => q.name === compoundKeyName)
      if (compoundKey) {
        compoundKey.options = options
      }
    },

    UPDATE_COMPOUND_KEY_OPTIONS(state, { compoundKeyName, options }) {
      const compoundKey = state.project.settings.compoundKeys?.find(q => q.name === compoundKeyName)
      if (compoundKey) {
        compoundKey.options = options
      }
    },

    // Agents Mutations
    SET_AGENTS(state, agents) {
      if (!state.project.settings.aIAgents) {
        state.project.settings.aIAgents = []
      }
      state.project.settings.aIAgents = agents
    },

    ADD_AGENT(state, agent) {
      if (!state.project.settings.aIAgents) {
        state.project.settings.aIAgents = []
      }
      state.project.settings.aIAgents.push(agent)
    },

    SET_AGENT(state, { index, item }) {
      if (Array.isArray(state.project.settings.aIAgents)) {
        Vue.set(state.project.settings.aIAgents, index, item)
      }
    },

    REMOVE_AGENT(state, index) {
      state.project.settings.aIAgents.splice(index, 1)
    },

    UPDATE_AGENT(state, { agentId, updates }) {
      const agent = state.project.settings.aIAgents?.find(a => a.id === agentId)
      if (agent) {
        Object.assign(agent, updates)
      }
    },

    TOGGLE_AGENT_SELECTION(state, agentId) {
      const agent = state.project.settings.aIAgents?.find(a => a.id === agentId)
      if (agent && !agent.disabled) {
        agent.selected = !agent.selected
      }
    },

    SELECT_ALL_AGENTS(state) {
      if (state.project.settings.aIAgents) {
        state.project.settings.aIAgents.forEach((agent, index) => {
          if (!agent.disabled) {
            Vue.set(state.project.settings.aIAgents[index], 'selected', true)
          }
        })
      }
    },

    CLEAR_ALL_AGENTS(state) {
      if (state.project.settings.aIAgents) {
        state.project.settings.aIAgents.forEach((agent, index) => {
          Vue.set(state.project.settings.aIAgents[index], 'selected', false)
        })
      }
    },

    SET_OCR_ENGINE_TYPE(state, engineType) {
      if (!state.project.settings.otherSettings) {
        state.project.settings.otherSettings = {}
      }
      if (!state.project.settings.otherSettings.ocr_settings) {
        state.project.settings.otherSettings.ocr_settings = {}
      }
      state.project.settings.otherSettings.ocr_settings.engine_type = engineType
    },

    SET_CLASSIFIER_SETTING(state, value) {
      if (!state.project.settings.otherSettings) {
        state.project.settings.otherSettings = {}
      }
      if (!state.project.settings.otherSettings.classifier_settings) {
        state.project.settings.otherSettings.classifier_settings = {}
      }
      state.project.settings.otherSettings.classifier_settings = {
        ...state.project.settings.otherSettings.classifier_settings,
        ...value,
      }
    },

    SET_PREPROCESS_SETTING(state, value) {
      if (!state.project.settings.otherSettings) {
        state.project.settings.otherSettings = {}
      }
      if (!state.project.settings.otherSettings.preprocess_settings) {
        state.project.settings.otherSettings.preprocess_settings = {}
      }
      state.project.settings.otherSettings.preprocess_settings = {
        ...state.project.settings.otherSettings.preprocess_settings,
        ...value,
      }
    },

    // Input Channels Mutations
    SET_INPUT_CHANNEL_CONFIG(state, { channelType, config, enabled }) {
      if (!state.project.settings.inputChannels) {
        Vue.set(state.project.settings, 'inputChannels', {})
      }
      if (!state.project.settings.inputChannels[channelType]) {
        Vue.set(state.project.settings.inputChannels, channelType, { enabled: false, config: {} })
      }
      Vue.set(state.project.settings.inputChannels[channelType], 'config', config)
      Vue.set(state.project.settings.inputChannels[channelType], 'enabled', enabled)
    },

    UPDATE_INPUT_CHANNEL_CONFIG(state, { channelType, config }) {
      if (!state.project.settings.inputChannels) {
        Vue.set(state.project.settings, 'inputChannels', {})
      }
      if (!state.project.settings.inputChannels[channelType]) {
        Vue.set(state.project.settings.inputChannels, channelType, { enabled: false, config: {} })
      }
      const currentConfig = state.project.settings.inputChannels[channelType].config || {}
      Vue.set(state.project.settings.inputChannels[channelType], 'config', { ...currentConfig, ...config })
    },

    ENABLE_INPUT_CHANNEL(state, channelType) {
      if (!state.project.settings.inputChannels) {
        Vue.set(state.project.settings, 'inputChannels', {})
      }
      if (!state.project.settings.inputChannels[channelType]) {
        Vue.set(state.project.settings.inputChannels, channelType, { enabled: false, config: {} })
      }
      Vue.set(state.project.settings.inputChannels[channelType], 'enabled', true)
    },

    DISABLE_INPUT_CHANNEL(state, channelType) {
      if (state.project.settings.inputChannels && state.project.settings.inputChannels[channelType]) {
        Vue.set(state.project.settings.inputChannels[channelType], 'enabled', false)
      }
    },

    TOGGLE_INPUT_CHANNEL(state, { channelType, enabled }) {
      if (!state.project.settings.inputChannels) {
        Vue.set(state.project.settings, 'inputChannels', {})
      }
      if (!state.project.settings.inputChannels[channelType]) {
        Vue.set(state.project.settings.inputChannels, channelType, { enabled: false, config: {} })
      }
      Vue.set(state.project.settings.inputChannels[channelType], 'enabled', enabled)
    },

    RESET_INPUT_CHANNEL(state, channelType) {
      if (state.project.settings.inputChannels && state.project.settings.inputChannels[channelType]) {
        Vue.set(state.project.settings.inputChannels, channelType, { enabled: false, config: {} })
      }
    },
    // Output Chanels related changes
    SET_OUTPUT_CHANNEL_CONFIG(state, { channelType, config }) {
      if (!state.project.settings.outputChannels) {
        Vue.set(state.project.settings, 'outputChannels', {})
      }
      if (!state.project.settings.outputChannels[channelType]) {
        Vue.set(state.project.settings.outputChannels, channelType, { enabled: false, config: {} })
      }
      Vue.set(state.project.settings.outputChannels[channelType], 'config', config)
    },

    UPDATE_OUTPUT_CHANNEL_CONFIG(state, { channelType, config }) {
      if (!state.project.settings.outputChannels) {
        Vue.set(state.project.settings, 'outputChannels', {})
      }
      if (!state.project.settings.outputChannels[channelType]) {
        Vue.set(state.project.settings.outputChannels, channelType, { enabled: false, config: {} })
      }
      const currentConfig = state.project.settings.outputChannels[channelType].config || {}
      Vue.set(state.project.settings.outputChannels[channelType], 'config', { ...currentConfig, ...config })
    },

    ENABLE_OUTPUT_CHANNEL(state, channelType) {
      if (!state.project.settings.outputChannels) {
        Vue.set(state.project.settings, 'outputChannels', {})
      }
      if (!state.project.settings.outputChannels[channelType]) {
        Vue.set(state.project.settings.outputChannels, channelType, { enabled: false, config: {} })
      }
      Vue.set(state.project.settings.outputChannels[channelType], 'enabled', true)
    },

    DISABLE_OUTPUT_CHANNEL(state, channelType) {
      if (state.project.settings.outputChannels && state.project.settings.outputChannels[channelType]) {
        Vue.set(state.project.settings.outputChannels[channelType], 'enabled', false)
      }
    },

    TOGGLE_OUTPUT_CHANNEL(state, { channelType, enabled }) {
      if (!state.project.settings.outputChannels) {
        Vue.set(state.project.settings, 'outputChannels', {})
      }
      if (!state.project.settings.outputChannels[channelType]) {
        Vue.set(state.project.settings.outputChannels, channelType, { enabled: false, config: {} })
      }
      Vue.set(state.project.settings.outputChannels[channelType], 'enabled', enabled)
    },

    RESET_OUTPUT_CHANNEL(state, channelType) {
      if (state.project.settings.outputChannels && state.project.settings.outputChannels[channelType]) {
        Vue.set(state.project.settings.outputChannels, channelType, { enabled: false, config: {} })
      }
    },
    SET_OUTPUT_CHANNEL_TYPES(state, outputChannelTypes) {
      if (!state.project.settings.outputChannels) {
        Vue.set(state.project.settings, 'outputChannels', {})
      }
      Vue.set(state.project.settings.outputChannels, 'outputChannelTypes', outputChannelTypes)
    },
  },

  actions: {
    resetProject({ commit }) {
      commit('RESET_PROJECT')
    },

    // Test output API connection
    async testOutputConnection({ commit }, { payload }) {
      const response = await axios.post('/pipeline/test_output_connection/', payload)
      commit('SET_OUTPUT_TEST_RESULT', response.data)
      return response
    },
    // async fetchOutputTestJson({ commit }, { payload }) {
    //   const response = await axios.post('/pipeline/get_test_json/', payload)
    //   commit('SET_OUTPUT_TEST_JSON', response.data)
    //   return response
    // },
    async fetchOutputApiConfig({ commit }, { params }) {
      const response = await axios.get('/dashboard/output-channels/', { params: { ...params } })
      commit('GET_OUTPUT_RESULT', response)
      return response
    },
    // Save output API configuration
    async saveOutputApiConfig({ commit }, { payload }) {
      const response = await axios.post('/dashboard/output-channels/', payload)
      commit('SET_OUTPUT_POST_RESULT', response)
      return response
    },
    async UpdateOutputApiConfig({ commit }, { payload }) {
      const response = await axios.put(`/dashboard/output-channels/${payload.id}/`, payload)
      commit('SET_OUTPUT_POST_RESULT', response)
      return response
    },
    async DeleteOutputApiConfig(context, id) {
      const params = {
        output_id: id,
      }
      const response = await axios.delete('/dashboard/output-channels/', { params })
      return response
    },
    // Alternative version if you want to pass the entire payload object
    async testGraphConfig({ commit }, { inputType, payload }) {
      const requestPayload = {
        client_id: payload.client_id,
        client_secret: payload.client_secret,
        tenant_id: payload.tenant_id,
        input_type: inputType,
      }
      const response = await axios.post('/pipeline/test_graph_config/', requestPayload)
      commit('SET_TEST_RESULT', response.data)
      return response.data
    },
    async testImapConfig({ commit }, { payload }) {
      const requestPayload = {
        email: payload.email,
        password: payload.password,
        server: payload.server,
        port: payload.port,
      }
      const response = await axios.post('/pipeline/test_imap_config/', requestPayload)
      commit('SET_TEST_RESULT', response.data)
      return response.data
    },

    async getInputChannelLogs({ commit }, { service, project }) {
      const requestPayload = {
        project,
        service,
      }
      const response = await axios.post('/pipeline/get_service_logs/', requestPayload)
      commit('SET_INPUT_LOGS', response)
      return response
    },

    async fetchProjectDetail({ commit }, projectId) {
      commit('SET_PROJECT_LOADING', true)
      try {
        const res = await axios.get(`/dashboard/projects/${projectId}/`)
        const merged = merge(cloneDeep(projectSettings), res.data)
        commit('SET_PROJECT', merged)
      } finally {
        commit('SET_PROJECT_LOADING', false)
      }
    },

    async saveProject({ state }) {
      const payload = {
        name: state.project.name,
        settings: state.project.settings,
      }
      await axios.put(`/dashboard/projects/${state.project.id}/`, payload)
    },

    addKeyQualifier({ commit }, nextIndex) {
      const newQualifier = {
        name: `Qualifier ${nextIndex}`,
        options: [],
      }
      commit('ADD_KEY_QUALIFIER', newQualifier)
    },

    updateQualifierOptions({ commit, getters }, { qualifierName, options }) {
      const { keyQualifiers } = getters
      const index = keyQualifiers.findIndex(q => q.name === qualifierName)
      if (index !== -1) {
        const updated = { ...keyQualifiers[index], options }
        commit('SET_KEY_QUALIFIER', { index, item: updated })
      }
    },
    addCompoundKeys({ commit }, nextIndex) {
      const newCompoundKey = {
        name: `Compound key ${nextIndex}`,
        keyItems: [],
      }
      commit('ADD_COMPOUND_KEYS', newCompoundKey)
    },

    updateCompoundKeyOptions({ commit, getters }, { compoundKeyName, keyItems }) {
      const { compoundKeys } = getters
      const index = compoundKeys.findIndex(q => q.name === compoundKeyName)
      if (index !== -1) {
        const updated = { ...compoundKeys[index], keyItems }
        commit('SET_COMPOUND_KEYS', { index, item: updated })
      }
    },

    deleteCompoundKey({ commit, getters }, compoundKeyName) {
      const index = getters.compoundKeys.findIndex(c => c.name === compoundKeyName)
      if (index !== -1) {
        commit('REMOVE_COMPOUND_KEYS', index)
      }
    },

    // AI Agents Actions
    setAIAgents({ commit }, agents) {
      commit('SET_AGENTS', agents)
    },

    addAIAgent({ commit }, agent) {
      commit('ADD_AGENT', agent)
    },

    updateAIAgent({ commit, getters }, { agentId, updates }) {
      const { aIAgents } = getters
      const index = aIAgents.findIndex(a => a.id === agentId)
      if (index !== -1) {
        const updated = { ...aIAgents[index], ...updates }
        commit('SET_AGENT', { index, item: updated })
      }
    },

    deleteAIAgent({ commit, getters }, agentId) {
      const index = getters.aIAgents.findIndex(a => a.id === agentId)
      if (index !== -1) {
        commit('REMOVE_AGENT', index)
      }
    },

    toggleAIAgentSelection({ commit }, agentId) {
      commit('TOGGLE_AGENT_SELECTION', agentId)
    },

    selectAllAIAgents({ commit }) {
      commit('SELECT_ALL_AGENTS')
    },

    clearAllAIAgents({ commit }) {
      commit('CLEAR_ALL_AGENTS')
    },

    addKeyItem({ commit }, item) {
      commit('ADD_KEY_ITEM', item)
    },

    updateKeyItems({ commit }, items) {
      commit('SET_KEY_ITEMS', items)
    },

    updateMappedKeys({ commit }, items) {
      commit('SET_MAPPED_KEY', items)
    },

    updateDocTypes({ commit }, items) {
      commit('SET_DOC_TYPES', items)
    },

    deleteKeyItem({ commit, getters }, keyValue) {
      const index = getters.keyItems.findIndex(i => i.keyValue === keyValue)
      if (index !== -1) {
        commit('DELETE_KEY_ITEM', index)
      }
    },

    // Input Channels Actions
    updateInputChannelConfig({ commit, getters }, { channelType, config, enabled }) {
      // If enabled is not provided, preserve current state
      const currentEnabled = enabled !== undefined ? enabled : getters.isInputChannelEnabled(channelType)
      commit('SET_INPUT_CHANNEL_CONFIG', { channelType, config, enabled: currentEnabled })

      // Don't automatically enable - let the toggle handle this
      if (currentEnabled) {
        commit('ENABLE_INPUT_CHANNEL', channelType)
      }
    },

    partialUpdateInputChannelConfig({ commit }, { channelType, config }) {
      commit('UPDATE_INPUT_CHANNEL_CONFIG', { channelType, config })
    },

    enableInputChannel({ commit }, channelType) {
      commit('ENABLE_INPUT_CHANNEL', channelType)
    },

    disableInputChannel({ commit }, channelType) {
      commit('DISABLE_INPUT_CHANNEL', channelType)
    },

    toggleInputChannel({ commit }, { channelType, enabled }) {
      commit('TOGGLE_INPUT_CHANNEL', { channelType, enabled })
    },

    resetInputChannel({ commit }, channelType) {
      commit('RESET_INPUT_CHANNEL', channelType)
    },

    async saveInputChannelConfig({ dispatch }, { channelType, config }) {
      dispatch('updateInputChannelConfig', { channelType, config })
      await dispatch('saveProject')
    },

    async saveEmailConfig({ dispatch }, config) {
      await dispatch('saveInputChannelConfig', { channelType: 'email', config })
    },

    async saveApiConfig({ dispatch }, config) {
      await dispatch('saveInputChannelConfig', { channelType: 'api', config })
    },

    async saveOneDriveConfig({ dispatch }, config) {
      await dispatch('saveInputChannelConfig', { channelType: 'onedrive', config })
    },

    async saveSharePointConfig({ dispatch }, config) {
      await dispatch('saveInputChannelConfig', { channelType: 'sharepoint', config })
    },

    // Output Channels Actions
    updateOutputChannelConfig({ commit }, { channelType, config }) {
      commit('SET_OUTPUT_CHANNEL_CONFIG', { channelType, config })
      commit('ENABLE_OUTPUT_CHANNEL', channelType)
    },

    partialUpdateOutputChannelConfig({ commit }, { channelType, config }) {
      commit('UPDATE_OUTPUT_CHANNEL_CONFIG', { channelType, config })
    },

    enableOutputChannel({ commit }, channelType) {
      commit('ENABLE_OUTPUT_CHANNEL', channelType)
    },

    disableOutputChannel({ commit }, channelType) {
      commit('DISABLE_OUTPUT_CHANNEL', channelType)
    },

    toggleOutputChannel({ commit }, { channelType, enabled }) {
      commit('TOGGLE_OUTPUT_CHANNEL', { channelType, enabled })
    },

    resetOutputChannel({ commit }, channelType) {
      commit('RESET_OUTPUT_CHANNEL', channelType)
    },

    async saveOutputChannelConfig({ dispatch }, { channelType, config }) {
      dispatch('updateOutputChannelConfig', { channelType, config })
      await dispatch('saveProject')
    },

    // async saveOutputApiConfig({ dispatch }, config) {
    //   await dispatch('saveOutputChannelConfig', { channelType: 'api', config })
    // },

  },

  getters: {
    project: state => state.project,

    isProjectLoading: state => state.isProjectLoading,

    settings: state => state.project.settings || {},

    otherSettings: state => state.project.settings.otherSettings || {},

    options: (state, getters) => getters.settings.options || {},

    keyItems: (state, getters) => getters.options['options-keys']?.items || [],

    keyModeTypes: (state, getters) => getters.options['options-col-modType']?.items || [],

    optionTypes: (state, getters) => getters.options['options-col-type']?.items || [],

    mappedKeys: (state, getters) => getters.options['options-mapped-keys']?.items || [],

    docTypes: (state, getters) => getters.options['options-meta-root-type']?.items || [],

    modTypes: (state, getters) => getters.options['options-col-modType']?.items || [],

    keyQualifiers: (state, getters) => getters.settings?.keyQualifiers || [],

    compoundKeys: (state, getters) => getters.settings?.compoundKeys || [],

    // Agents Getters
    aIAgents: (state, getters) => getters.settings?.aIAgents || [],

    selectedAIAgents: (state, getters) => getters.aIAgents.filter(a => a.selected),

    availableAIAgents: (state, getters) => getters.aIAgents.filter(a => !a.disabled),

    selectedAIAgentsCount: (state, getters) => getters.selectedAIAgents.length,

    allAvailableAIAgentsSelected: (state, getters) => {
      const available = getters.availableAIAgents
      return available.length > 0 && available.every(a => a.selected)
    },

    getAIAgentById: state => agentId => {
      const aIAgents = state.project?.settings?.aIAgents || []
      return aIAgents.find(a => a.id === agentId)
    },

    getQualifierOptions: state => qualifierName => {
      const keyQualifiers = state.project?.settings?.keyQualifiers || []
      const item = keyQualifiers.find(q => q.name === qualifierName)
      return item?.options || []
    },
    getCompoundKeyOptions: state => compoundKeyName => {
      const compoundKeys = state.project?.settings?.compoundKeys || []
      const item = compoundKeys.find(q => q.name === compoundKeyName)
      return item?.keyItems || []
    },

    projectOcrSettings(state) {
      return state.project?.settings?.otherSettings?.ocr_settings || { engine_type: 'internal' }
    },
    projectClassifierSettings(state) {
      return state.project?.settings?.otherSettings?.classifier_settings || { automatic_splitting: false, disable_classification_review: false }
    },
    projectPreprocessSettings(state) {
      return state.project?.settings?.otherSettings?.preprocess_settings || { ignore_dense_page: false }
    },

    // Input Channels Getters
    inputChannels: (state, getters) => getters.settings?.inputChannels || {},

    getInputChannelConfig: state => channelType => {
      const inputChannels = state.project?.settings?.inputChannels || {}
      return inputChannels[channelType]?.config || {}
    },

    isInputChannelEnabled: state => channelType => {
      const inputChannels = state.project?.settings?.inputChannels || {}
      return inputChannels[channelType]?.enabled || false
    },

    isInputChannelConfigured: state => channelType => {
      const inputChannels = state.project?.settings?.inputChannels || {}
      const config = inputChannels[channelType]?.config || {}
      return Object.keys(config).length > 0
    },

    enabledInputChannels(state, getters) {
      const { inputChannels } = getters
      return Object.keys(inputChannels).filter(channelType => inputChannels[channelType]?.enabled === true)
    },

    configuredInputChannels(state, getters) {
      const { inputChannels } = getters
      return Object.keys(inputChannels).filter(channelType => {
        const config = inputChannels[channelType]?.config || {}
        return Object.keys(config).length > 0
      })
    },

    activeInputChannels(state, getters) {
      const { inputChannels } = getters
      return Object.keys(inputChannels).filter(channelType => {
        const channel = inputChannels[channelType] || {}
        const config = channel.config || {}
        return channel.enabled && Object.keys(config).length > 0
      })
    },

    getEmailConfig(state, getters) {
      return getters.getInputChannelConfig('email')
    },

    getApiConfig(state, getters) {
      return getters.getInputChannelConfig('api')
    },

    getOneDriveConfig(state, getters) {
      return getters.getInputChannelConfig('onedrive')
    },

    getSharePointConfig(state, getters) {
      return getters.getInputChannelConfig('sharepoint')
    },

    isEmailEnabled(state, getters) {
      return getters.isInputChannelEnabled('email')
    },

    isApiEnabled(state, getters) {
      return getters.isInputChannelEnabled('api')
    },

    isOneDriveEnabled(state, getters) {
      return getters.isInputChannelEnabled('onedrive')
    },

    isSharePointEnabled(state, getters) {
      return getters.isInputChannelEnabled('sharepoint')
    },

    toNormalLabel: () => camelCaseStr => {
      if (!camelCaseStr) return ''

      // If already contains space, capitalize first letter only
      if (camelCaseStr.includes(' ')) {
        return camelCaseStr.charAt(0).toUpperCase() + camelCaseStr.slice(1)
      }

      // Insert space before capital letters
      const spaced = camelCaseStr.replace(/([A-Z])/g, ' $1')

      // Capitalize first letter
      return spaced.charAt(0).toUpperCase() + spaced.slice(1)
    },

    // Output Channels Getters
    outputChannels: (state, getters) => getters.settings?.outputChannels || {},

    getOutputChannelConfig: state => channelType => {
      const outputChannels = state.project?.settings?.outputChannels || {}
      return outputChannels[channelType]?.config || {}
    },

    isOutputChannelEnabled: state => channelType => {
      const outputChannels = state.project?.settings?.outputChannels || {}
      return outputChannels[channelType]?.enabled || false
    },

    isOutputChannelConfigured: state => channelType => {
      const outputChannels = state.project?.settings?.outputChannels || {}
      const config = outputChannels[channelType]?.config || {}
      return Object.keys(config).length > 0
    },

    enabledOutputChannels(state, getters) {
      const { outputChannels } = getters
      return Object.keys(outputChannels).filter(channelType => outputChannels[channelType]?.enabled === true)
    },

    configuredOutputChannels(state, getters) {
      const { outputChannels } = getters
      return Object.keys(outputChannels).filter(channelType => {
        const config = outputChannels[channelType]?.config || {}
        return Object.keys(config).length > 0
      })
    },

    activeOutputChannels(state, getters) {
      const { outputChannels } = getters
      return Object.keys(outputChannels).filter(channelType => {
        const channel = outputChannels[channelType] || {}
        const config = channel.config || {}
        return channel.enabled && Object.keys(config).length > 0
      })
    },

    getOutputApiConfig(state, getters) {
      return getters.getOutputChannelConfig('api')
    },

    isOutputApiEnabled(state, getters) {
      return getters.isOutputChannelEnabled('api')
    },
    outputChannelTypes: (state, getters) => getters.settings?.outputChannels?.outputChannelTypes || [],

  },
}
