/**
 * Organization: AIDocbuilder Inc.
 * File: store/auth/index.js
 * Version: 7.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Enhanced and refined state management for auth
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-07
 *
 * Description:
 * This file defines the Vuex store module for handling authentication and user-related data.
 *
 * SECURITY: HttpOnly Cookie-Based Authentication
 * - Auth token is stored in an HttpOnly cookie (not accessible to JavaScript)
 * - NO client-side storage (localStorage/sessionStorage) is used for auth data
 * - Server is the source of truth - user data is fetched on each page load
 *
 * Dependencies:
 *   - none
 *
 * Main Features:
 *   - In-memory authentication state (not persisted)
 *   - Actions for setting/clearing authentication data
 *   - Getters to retrieve authentication data
 *
 * Notes:
 *   - The module is namespaced for modularity.
 *   - State is NOT persisted - cleared on page refresh
 *   - User data is re-fetched from server on each page load via /api/me endpoint
 */

export default {
  namespaced: true,
  // State: Defines the initial data structure for authentication and user-related information
  // Note: Token is NOT stored here - it's in an HttpOnly cookie for security
  state: {
    userName: null, // User's username
    isAdmin: false, // Whether the user has admin privileges
    projectCountries: [], // List of countries associated with the user's projects
    selectedProjectCountries: [], // List of countries selected by the user
    authChecked: false, // Flag to track if auth has been verified with server
  },
  mutations: {
    // Mutation to update authentication-related data
    SET_AUTH_DATA(state, authData) {
      state.userName = authData.userName
      state.isAdmin = authData.isAdmin
      state.projectCountries = authData.projectCountries || []
      state.authChecked = true // Mark auth as checked
    },
    // Mutation to mark auth as checked (even if not authenticated)
    SET_AUTH_CHECKED(state, checked) {
      state.authChecked = checked
    },
    // Mutation to update the selected project countries
    SET_SELECTED_PROJECT_COUNTRIES(state, data) {
      state.selectedProjectCountries = data
    },
  },
  actions: {
    // Action to process and store authentication data
    // Note: Token is handled by HttpOnly cookie, not stored in state
    setAuthData({ commit, dispatch, getters }, data) {
      const projectCountries = []

      // Process project-country data and format it for easier usage
      data.user.project_countries.forEach(item => {
        item.countries.forEach(country => {
          projectCountries.push({
            countryCode: country.code, // Country code
            country: country.name, // Country name
            project: item.project.name, // Project name associated with the country
          })
        })
      })

      // Sort countries alphabetically by name
      projectCountries.sort((a, b) => a.country.localeCompare(b.country))

      // Construct the authentication data object (no token - it's in HttpOnly cookie)
      // Note: NO client-side storage - data is only in Vuex memory
      const authData = {
        userName: data.user.username, // Username
        isAdmin: data.user.is_superuser, // Admin status
        projectCountries, // Processed project-country data
      }

      // Set selected project countries based on user's choice
      if (data.keepSelectedItems) {
        const { selectedProjectCountries } = getters
        dispatch('setSelectedProjectCountries', selectedProjectCountries)
      } else {
        dispatch('setSelectedProjectCountries', projectCountries)
      }

      // Commit the processed authentication data to the state
      commit('SET_AUTH_DATA', authData)
    },
    // Action to update selected project countries
    setSelectedProjectCountries({ commit }, data) {
      commit('SET_SELECTED_PROJECT_COUNTRIES', data)
    },
    // Action to clear authentication data (e.g., on logout)
    // Note: The HttpOnly cookie is cleared by the server on logout
    clearAuthData({ commit }) {
      // Clear in-memory Vuex state only (no client-side storage to clear)
      commit('SET_AUTH_DATA', {
        userName: null,
        isAdmin: false,
        projectCountries: [],
      })
      commit('SET_SELECTED_PROJECT_COUNTRIES', [])
      // Keep authChecked true - we know the user is not authenticated
    },
    // Action to mark auth as checked
    setAuthChecked({ commit }, checked) {
      commit('SET_AUTH_CHECKED', checked)
    },
  },
  getters: {
    // Getter to check if auth has been verified with server
    authChecked(state) {
      return state.authChecked
    },
    // Getter to check if the user is authenticated (client-side check)
    // Note: Actual auth is validated server-side via HttpOnly cookie
    isAuthenticated(state) {
      return !!state.userName // Returns true if username exists
    },
    // Getter to retrieve the username
    userName(state) {
      return state.userName
    },
    // Getter to check if the user has admin privileges
    isAdmin(state) {
      return state.isAdmin
    },
    // Getter to retrieve the list of project countries
    projectCountries(state) {
      return state.projectCountries
    },
    // Getter to retrieve the list of selected project countries
    selectedProjectCountries(state) {
      return state.selectedProjectCountries
    },
  },
}
