/**
 * Organization: AIDocbuilder Inc.
 * File: theme/index.js
 * Version: 1.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Code optimization and enhancement
 *
 * Last Updated By: Vinay
 * Last Updated At: 2023-11-01
 *
 * Description:
 *   This Vuex store module manages the theme settings for the application.
 *   It provides state, mutations, actions, and getters to handle:
 *     - Light and dark mode configurations
 *     - Application logos, header colors, and title colors
 *     - Dynamic favicon and application title
 *
 * Dependencies:
 *   - axios: For making HTTP requests to fetch theme settings
 *   - lodash (cloneDeep): For deep cloning the default settings object
 *   - @/utils/env: For accessing environment variables (e.g., backend URLs)
 *
 * Main Features:
 *   - **State Management**:
 *       - Stores theme configurations, including light and dark mode properties.
 *   - **Mutations**:
 *       - Update the theme settings state synchronously with fetched data.
 *   - **Actions**:
 *       - Fetch theme settings from the backend API and process the response.
 *       - Resolve asset URLs dynamically based on environment variables.
 *   - **Getters**:
 *       - Provide access to the processed theme settings for use in components.
 *
 * Notes:
 *   - This module is namespaced to maintain scope isolation within Vuex.
 *   - Includes error handling for API calls to improve robustness.
 */

import axios from 'axios'
import { cloneDeep } from 'lodash'

import getEnv from '@/utils/env'

const defaultSettings = {
  appTitle: 'Data Definitions Editor 7.2.0',
  light: {
    logo: null,
    headerColor: null,
    headerTextColor: null,
    appTitleColor: null,
  },
  dark: {
    logo: null,
    headerColor: null,
    headerTextColor: null,
    appTitleColor: null,
  },
}

export default {
  namespaced: true,
  state: {
    settings: defaultSettings,
  },
  mutations: {
    SET_THEME_SETTINGS(state, data) {
      state.settings = data
    },
  },
  actions: {
    fetchThemeSettings({ commit }) {
      return new Promise((resolve, reject) => {
        axios.get('/theme/theme_settings/')
          .then(res => {
            const resData = res.data

            const settings = cloneDeep(defaultSettings)

            if (resData?.logo_light_mode) {
              settings.light.logo = `${getEnv('VUE_APP_BACKEND_URL')}${resData.logo_light_mode}`
            }

            if (resData?.logo_dark_mode) {
              settings.dark.logo = `${getEnv('VUE_APP_BACKEND_URL')}${resData.logo_dark_mode}`
            }

            if (resData?.header_color_light_mode) {
              settings.light.headerColor = resData.header_color_light_mode
            }

            if (resData?.header_color_dark_mode) {
              settings.dark.headerColor = resData.header_color_dark_mode
            }

            if (resData?.header_text_color_light_mode) {
              settings.light.headerTextColor = resData.header_text_color_light_mode
            }

            if (resData?.header_text_color_dark_mode) {
              settings.dark.headerTextColor = resData.header_text_color_dark_mode
            }

            if (resData?.favicon) {
              settings.favicon = `${getEnv('VUE_APP_BACKEND_URL')}${resData.favicon}`
            }

            if (resData?.app_title) {
              settings.appTitle = resData.app_title
            }

            if (resData?.app_title_color_light_mode) {
              settings.light.appTitleColor = resData.app_title_color_light_mode
            }

            if (resData?.app_title_color_dark_mode) {
              settings.dark.appTitleColor = resData.app_title_color_dark_mode
            }

            commit('SET_THEME_SETTINGS', settings)
            resolve()
          })
          .catch(error => {
            const message = error?.response?.data?.detail || 'Error fetching theme settings'
            reject(new Error(message))
          })
      })
    },
  },
  getters: {
    settings(state) {
      return state.settings
    },
  },
}
