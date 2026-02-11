/**
 * Organization: AIDocbuilder Inc.
 * File: default-settings/index.js
 * Version: 1.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Code review and optimization
 *
 * Last Updated By: Vinay
 * Last Updated At: 2023-12-15
 *
 * Description:
 *   This file serves as a Vuex store module for managing default settings within the application.
 *
 * Dependencies:
 *   - Vuex
 *
 * Main Features:
 *   - Define default state values, including compound keys for behavior settings.
 *   - Provide a getter to access default behavior configuration.
 *   - Modularized and namespaced for better state management.
 */

export default {
  namespaced: true,
  state: {
    defaultBehaviour: {
      compoundKeys: [
        'housebill',
        'masterbill',
      ],
    },
  },
  mutations: {},
  actions: {},
  getters: {
    defaultBehaviour(state) {
      return state.defaultBehaviour
    },
  },
}
