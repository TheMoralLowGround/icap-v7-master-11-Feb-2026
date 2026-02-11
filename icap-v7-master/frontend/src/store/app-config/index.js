/**
 * Organization: AIDocbuilder Inc.
 * File: app-config/index.js
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
 *   This Vuex store module manages the layout configuration of the application, including:
 *     - Layout settings such as text direction (RTL/LTR), themes (skins), and transitions.
 *     - Configurations for the menu, navbar, and footer components.
 *     - Persistent storage of user preferences like skin settings using `localStorage`.
 *
 * Dependencies:
 *   - @themeConfig: Provides default configuration values for the layout.
 *   - localStorage: For persisting skin preferences across sessions.
 *
 * Main Features:
 *   - **State Management**:
 *       - Tracks layout properties, including skin, menu visibility, and navbar/footer configurations.
 *       - Allows dynamic updates to the text direction and skin.
 *   - **Getters**:
 *       - Retrieve the current layout configuration for use in components.
 *   - **Mutations**:
 *       - Modify the layout settings, including:
 *           - `TOGGLE_RTL`: Toggles text direction and updates the DOM accordingly.
 *           - `UPDATE_SKIN`: Changes the theme and applies corresponding CSS classes.
 *           - `UPDATE_ROUTER_TRANSITION`: Updates the route transition effect.
 *           - `UPDATE_LAYOUT_TYPE`: Changes the layout type (e.g., vertical or horizontal).
 *           - `UPDATE_CONTENT_WIDTH`: Adjusts the content width (e.g., full-width or boxed).
 *           - Navbar and footer settings can also be dynamically updated.
 *   - **Actions**:
 *       - Reserved for future asynchronous operations, currently unused.
 *
 * Notes:
 *   - The module is namespaced for better modularity and scope isolation.
 *   - Includes dynamic DOM updates (e.g., text direction and body classes for themes).
 */

// Import theme configuration from the specified module
import { $themeConfig } from '@themeConfig'

export default {
  // Enable Vuex module namespacing for better modularity
  namespaced: true,

  // Define the initial state of the layout module
  state: {
    layout: {
      // Determines if the layout should use right-to-left (RTL) text direction
      isRTL: $themeConfig.layout.isRTL,

      // Sets the skin (theme) for the application, either from localStorage or themeConfig
      skin: localStorage.getItem('vuexy-skin') || $themeConfig.layout.skin,

      // Specifies the type of transition used between routes
      routerTransition: $themeConfig.layout.routerTransition,

      // Sets the layout type (e.g., vertical, horizontal)
      type: $themeConfig.layout.type,

      // Specifies the content width (e.g., full-width or boxed)
      contentWidth: $themeConfig.layout.contentWidth,

      // Menu configuration
      menu: {
        hidden: $themeConfig.layout.menu.hidden, // Determines if the menu should be hidden
      },

      // Navbar configuration
      navbar: {
        type: $themeConfig.layout.navbar.type, // Type of navbar (e.g., floating, static)
        backgroundColor: $themeConfig.layout.navbar.backgroundColor, // Background color of the navbar
      },

      // Footer configuration
      footer: {
        type: $themeConfig.layout.footer.type, // Footer type (e.g., sticky, static)
      },
    },
  },

  // Getters for computed properties based on the state
  getters: {
    // Returns the complete layout configuration
    getlayout(state) {
      return state.layout
    },
  },

  // Mutations for directly modifying the state
  mutations: {
    // Toggles the text direction between RTL and LTR
    TOGGLE_RTL(state) {
      state.layout.isRTL = !state.layout.isRTL
      // Update the `dir` attribute on the root HTML element
      document.documentElement.setAttribute('dir', state.layout.isRTL ? 'rtl' : 'ltr')
    },

    // Updates the application's skin (theme) and persists it to localStorage
    UPDATE_SKIN(state, skin) {
      state.layout.skin = skin
      // Update value in localStorage
      localStorage.setItem('vuexy-skin', skin)

      // Add or remove the `dark-layout` class from the body element
      if (skin === 'dark') {
        document.body.classList.add('dark-layout')
      } else if (document.body.className.match('dark-layout')) {
        document.body.classList.remove('dark-layout')
      }
    },

    // Updates the type of router transition
    UPDATE_ROUTER_TRANSITION(state, val) {
      state.layout.routerTransition = val
    },

    // Updates the layout type (e.g., vertical or horizontal)
    UPDATE_LAYOUT_TYPE(state, val) {
      state.layout.type = val
    },

    // Updates the content width (e.g., full-width or boxed)
    UPDATE_CONTENT_WIDTH(state, val) {
      state.layout.contentWidth = val
    },

    // Toggles the visibility of the navigation menu
    UPDATE_NAV_MENU_HIDDEN(state, val) {
      state.layout.menu.hidden = val
    },

    // Updates navbar configuration with new values
    UPDATE_NAVBAR_CONFIG(state, obj) {
      Object.assign(state.layout.navbar, obj)
    },

    // Updates footer configuration with new values
    UPDATE_FOOTER_CONFIG(state, obj) {
      Object.assign(state.layout.footer, obj)
    },
  },

  // Actions for asynchronous or complex state modifications (currently unused)
  actions: {},
}
