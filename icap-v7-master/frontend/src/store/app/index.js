/**
 * Organization: AIDocbuilder Inc.
 * File: app/index.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Code optimization and enhancement
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   This Vuex store module manages global application state, including:
 *     - Window dimensions and breakpoints
 *     - Overlay visibility
 *     - Current page title and route name
 *
 * Dependencies:
 *   - @themeConfig: For accessing theme breakpoint configurations
 *
 * Main Features:
 *   - **State Management**:
 *       - Tracks window dimensions for responsive design.
 *       - Manages overlay visibility across the application.
 *       - Stores and retrieves current page titles and route names.
 *   - **Getters**:
 *       - Compute the current breakpoint dynamically based on window width.
 *       - Provide access to the current page title and route name for components.
 *   - **Mutations**:
 *       - Update state properties synchronously, including:
 *           - `windowWidth`: Reflects the current window width for layout adjustments.
 *           - `shallShowOverlay`: Controls overlay visibility.
 *           - `currentPageTitle`: Sets the current page title.
 *           - `currentRouteName`: Updates the current route name for navigation tracking.
 *   - **Actions**:
 *       - Reserved for future asynchronous operations, currently unused.
 *
 * Notes:
 *   - This module is namespaced to ensure modularity and avoid state conflicts.
 *   - Includes dynamic breakpoint determination for responsive UI components.
 */

// Import theme breakpoints configuration
import { $themeBreakpoints } from '@themeConfig'

export default {
  // Enable Vuex module namespacing for better modularity
  namespaced: true,

  // Define the state of the module
  state: {
    windowWidth: 0, // Tracks the current width of the window
    shallShowOverlay: false, // Determines whether an overlay should be displayed
    currentPageTitle: null, // Stores the title of the current page
    currentRouteName: '', // Stores the name of the current route
  },

  // Define getters for computed state properties
  getters: {
    // Determine the current breakpoint based on window width
    currentBreakPoint: state => {
      const { windowWidth } = state
      if (windowWidth >= $themeBreakpoints.xl) return 'xl'
      if (windowWidth >= $themeBreakpoints.lg) return 'lg'
      if (windowWidth >= $themeBreakpoints.md) return 'md'
      if (windowWidth >= $themeBreakpoints.sm) return 'sm'
      return 'xs' // Default to 'xs' for the smallest screens
    },
    // Getter to access the current page title
    currentPageTitle(state) {
      return state.currentPageTitle
    },
    // Getter to access the current route name
    currentRouteName(state) {
      return state.currentRouteName
    },
  },

  // Define mutations for updating state
  mutations: {
    // Update the windowWidth property
    UPDATE_WINDOW_WIDTH(state, val) {
      state.windowWidth = val
    },
    // Toggle or set the value of shallShowOverlay
    TOGGLE_OVERLAY(state, val) {
      state.shallShowOverlay = val !== undefined ? val : !state.shallShowOverlay
    },
    // Set the current page title
    SET_CURRENT_PAGE_TITLE(state, val) {
      state.currentPageTitle = val
    },
    // Set the current route name
    SET_CURRENT_ROUTE_NAME(state, val) {
      state.currentRouteName = val
    },
  },

  // Define actions (currently empty, can be used for asynchronous operations)
  actions: {},
}
