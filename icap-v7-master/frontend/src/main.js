/**
 * Organization: AIDocbuilder Inc.
 * File: main.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *   - Ali: Code optimization
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   The main entry point for the Vue.js application. This file sets up
 *   the core dependencies, configurations, and plugins, and initializes
 *   the Vue instance, rendering the root component.
 *
 * Dependencies:
 *   - Vue.js
 *   - Bootstrap-Vue (ToastPlugin, ModalPlugin)
 *   - Vue Composition API
 *   - Axios
 *   - Portal Vue
 *   - Toastification
 *   - Vue Konva
 *
 * Main Features:
 *   - Configures Vue with essential plugins and libraries.
 *   - Registers global components and custom validation rules.
 *   - Imports core and custom SCSS styles for consistent theming.
 *   - Creates and mounts the Vue instance with router and store integration.
 *
 * Core Components:
 *   - Root component: App.vue
 *   - Router: Manages navigation within the application.
 *   - Store: Centralized state management.
 *
 * Notes:
 *   - Custom validations and global components are registered for application-wide use.
 *   - Vue Composition API enables Composition API features in Vue 2.
 *   - Includes third-party libraries for enhanced functionalities like toast notifications,
 *     canvas rendering, and DOM manipulation.
 *   - Production tips are disabled for cleaner console output in production environments.
 */

import Vue from 'vue'
// Import Bootstrap-Vue plugins for toast and modal functionalities
import { ToastPlugin, ModalPlugin } from 'bootstrap-vue'
// Import Vue Composition API for using composition functions in Vue 2
import VueCompositionAPI from '@vue/composition-api'

// Import the router and store instances for managing routes and state
import router from './router'
import store from './store'
// Import the root application component
import App from './App.vue'

// Global Components
// Registers global components that can be used across the app
import './global-components'

// Custom Validations
// Registers custom form validation rules
import './custom-validations'

// Third-party plugins
// Axios setup for HTTP requests
import '@axios'
// Portal Vue for DOM manipulation in Vue
import '@/libs/portal-vue'
// Toastification for toast notifications
import '@/libs/toastification'
// Vue Konva for canvas rendering
import '@/libs/vue-konva'
// Ensures nextTick works correctly in specific scenarios
import '@/libs/vue-force-next-tick'

// BootstrapVue Plugin Registration
// Enables Toast and Modal plugins globally
Vue.use(ToastPlugin)
Vue.use(ModalPlugin)

// Composition API
// Enables the use of Vue Composition API with Vue 2
Vue.use(VueCompositionAPI)

// Feather font icon
// Includes Feather Icons specifically for form-wizard features
// * Can be removed if feather-icons are not required
require('@core/assets/fonts/feather/iconfont.css') // For form-wizard

// Core SCSS styles
// Imports core styles for the application
require('@core/scss/core.scss')

// Custom application SCSS styles
// Includes custom styling specific to the project
require('@/assets/scss/style.scss')

// Prevent Vue from displaying production tips in the console
Vue.config.productionTip = false

// Create and mount the Vue instance
new Vue({
  router, // Injects the router instance for navigation
  store, // Injects the store instance for state management
  render: h => h(App), // Renders the root application component
}).$mount('#app') // Mounts the Vue instance to the DOM element with id 'app'
