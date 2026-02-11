<!--
 Organization: AIDocbuilder Inc.
 File: src/App.vue
 Version: 1.0

 Authors:
   - Initial implementation: Vinay
   - Ali: Enhanced app initialization and metadata handling

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   The main application component for the Vue.js app. This component handles layout
   rendering, dynamic metadata updates (such as document title and favicon),
   authentication management, and WebSocket connection handling.
   It also integrates theme and configuration settings with Vuex, manages loading
   states, and reacts to route changes.

 Dependencies:
   - vue-toastification: For toast notifications.
   - axios: For API requests.
   - @vue/composition-api: For composition API features in Vue 2.
   - @core/app-config/useAppConfig: For managing app configurations.
   - @themeConfig: For theme color and breakpoint settings.
   - @core/components/toastification/ToastificationContent: For custom toast content.

 Main Features:
   - Dynamically loads layouts based on route metadata.
   - Handles app title and favicon updates based on Vuex store state.
   - Initializes WebSocket connection and refreshes authentication token.
   - Provides a loading state during app initialization.
   - Refreshes authentication data and tracks user login activity.
   - Manages window size and applies responsive configurations.

 Core Components:
   - LayoutHorizontal: Horizontal layout component.
   - LayoutFull: Full-screen layout component.
   - ToastificationContent: Custom component for toast notifications.

 Notes:
   - The component is responsible for the global initialization of the app, including
     theme settings, WebSocket management, and authentication state.
   - Axios response interceptors handle global 401 errors for authentication.
   - WebSocket error handling is implemented via event bus with persistent toast messages.
   - The component also manages skin classes, which define the layout appearance.
-->

<template>
  <div
    id="app"
    class="h-100"
    :class="[skinClasses]"
  >
    <component
      :is="layout"
      v-if="!loading"
    >
      <router-view />
    </component>
  </div>
</template>

<script>
/**
 * Vue 2 main app component script.
 * This script sets up layouts, global configurations, and handles dynamic updates
 * for app metadata like document title and favicon.
 */

// Importing theme configurations and utilities
// This will be populated in `beforeCreate` hook
import { $themeColors, $themeBreakpoints, $themeConfig } from '@themeConfig'
import { provideToast } from 'vue-toastification/composition'
import { watch } from '@vue/composition-api'
import useAppConfig from '@core/app-config/useAppConfig'

// Utility hooks for window size and CSS variable manipulation
import { useWindowSize, useCssVar } from '@vueuse/core'

import store from '@/store'
import axios from 'axios'

import WS from '@/utils/ws'
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

// Lazy-loading layout components for better performance
const LayoutHorizontal = () => import('@/layouts/horizontal/LayoutHorizontal.vue')
const LayoutFull = () => import('@/layouts/full/LayoutFull.vue')

export default {
  // Registering layout components
  components: {
    // Layouts
    LayoutHorizontal,
    LayoutFull,
  },
  data() {
    return {
      loading: true, // Indicates whether the app is in a loading state
    }
  },
  // ! We can move this computed: layout & contentLayoutType once we get to use Vue 3
  // Currently, router.currentRoute is not reactive and doesn't trigger any change
  // Computed properties for layout and metadata
  computed: {
    // Determines the layout component based on route metadata
    layout() {
      if (this.$route.meta.layout === 'full') return 'layout-full'
      return `layout-${this.contentLayoutType}`
    },
    // Retrieves the layout type from Vuex store
    contentLayoutType() {
      return this.$store.state.appConfig.layout.type
    },
    // Check if user is authenticated (client-side check)
    // Note: Actual auth is validated server-side via HttpOnly cookie
    isAuthenticated() {
      return this.$store.getters['auth/isAuthenticated']
    },
    // Username of the authenticated user
    userName() {
      return this.$store.getters['auth/userName']
    },
    // Application title from Vuex store
    appTitle() {
      return this.$store.getters['theme/settings'].appTitle
    },
    // Current page title from Vuex store
    pageTitle() {
      return this.$store.getters['app/currentPageTitle']
    },
    // Constructs the document title from page title and app title
    documentTitle() {
      const { pageTitle, appTitle } = this
      const title = pageTitle ? `${pageTitle} - ${appTitle}` : appTitle
      return title
    },
    // Retrieves the URL for the favicon from Vuex store
    faviconUrl() {
      return this.$store.getters['theme/settings'].favicon
    },
  },
  watch: {
    // Reacts to changes in auth state and refreshes WebSocket connection
    isAuthenticated() {
      this.refreshWebSocketConnection()
    },
    // Updates the document title when it changes
    documentTitle() {
      this.updateDocumentTitle()
    },
    // Updates the favicon when its URL changes
    faviconUrl() {
      this.updateFavicon()
    },
    // Watches for route changes and updates the current route name in Vuex
    $route(to/* , from */) {
      this.$store.commit('app/SET_CURRENT_ROUTE_NAME', to.name)
    },

  },
  beforeCreate() {
    // Set colors in theme
    const colors = ['primary', 'secondary', 'success', 'info', 'warning', 'danger', 'light', 'dark']

    // eslint-disable-next-line no-plusplus
    for (let i = 0, len = colors.length; i < len; i++) {
      $themeColors[colors[i]] = useCssVar(`--${colors[i]}`, document.documentElement).value.trim()
    }

    // Set Theme Breakpoints
    const breakpoints = ['xs', 'sm', 'md', 'lg', 'xl']

    // eslint-disable-next-line no-plusplus
    for (let i = 0, len = breakpoints.length; i < len; i++) {
      $themeBreakpoints[breakpoints[i]] = Number(useCssVar(`--breakpoint-${breakpoints[i]}`, document.documentElement).value.slice(0, -2))
    }

    // Set RTL
    const { isRTL } = $themeConfig.layout
    document.documentElement.setAttribute('dir', isRTL ? 'rtl' : 'ltr')
  },
  setup() {
    const { skin, skinClasses } = useAppConfig()

    // If skin is dark when initialized => Add class to body
    if (skin.value === 'dark') document.body.classList.add('dark-layout')

    // Provide toast for Composition API usage
    // This for those apps/components which uses composition API
    // Demos will still use Options API for ease
    provideToast({
      hideProgressBar: true,
      closeOnClick: false,
      closeButton: false,
      icon: false,
      timeout: 3000,
      transition: 'Vue-Toastification__fade',
    })

    // Set Window Width in store
    store.commit('app/UPDATE_WINDOW_WIDTH', window.innerWidth)
    const { width: windowWidth } = useWindowSize()
    watch(windowWidth, val => {
      store.commit('app/UPDATE_WINDOW_WIDTH', val)
    })

    return {
      skinClasses,
    }
  },
  created() {
    // Initialize the application when the component is created
    this.initApp()

    // Listen for WebSocket error events on the event bus
    bus.$on('wsError', this.onWsError)
    bus.$on('onRefreshAuthData', this.onRefreshAuthData)

    // Set the current route name in the Vuex store
    this.$store.commit('app/SET_CURRENT_ROUTE_NAME', this.$route.name)
  },
  destroyed() {
    // Clean up the WebSocket error listener when the component is destroyed
    bus.$off('wsError', this.onWsError)
    bus.$off('onRefreshAuthData', this.onRefreshAuthData)
  },
  methods: {
    /**
     * Initializes the application.
     * Fetches theme settings, updates metadata, and sets up authentication and WebSocket.
     */
    async initApp() {
      this.loading = true

      try {
        // Fetch and apply theme settings from the store
        await this.$store.dispatch('theme/fetchThemeSettings')
      } catch (error) {
        // Show an error toast if fetching theme settings fails
        this.$toast({
          component: ToastificationContent,
          props: {
            title: error.message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }

      // Update document title
      this.updateDocumentTitle()

      // Clear any legacy auth data from localStorage/sessionStorage
      // This ensures old auth data doesn't interfere with new HttpOnly cookie approach
      this.clearLegacyAuthData()

      // Add an Axios response interceptor to handle 401 (unauthorized) errors globally
      // This must be set up before fetchCurrentUser to handle auth failures
      axios.interceptors.response.use(undefined, error => {
        if (error.response && error.response.status === 401) {
          this.$store.dispatch('auth/clearAuthData') // Clear auth data
          // Only redirect to login if not already on login page and not from /me endpoint
          // The /me endpoint 401 is expected when not logged in
          const isFromMeEndpoint = error.config?.url?.includes('/access_control/me')
          if (this.$route.name !== 'login' && !isFromMeEndpoint) {
            this.$router.push({ name: 'login', query: { redirect: this.$route.fullPath } })
          }
        }
        return Promise.reject(error)
      })

      // Fetch current user from server using HttpOnly cookie
      // Always fetch - server is the source of truth
      // The middleware will wait for authChecked before making redirect decisions
      await this.fetchCurrentUser()

      // Hide the loading screen after initialization
      this.loading = false
      this.$nextTick(() => {
        const appLoading = document.getElementById('loading-bg')
        if (appLoading) {
          appLoading.style.display = 'none'
        }
      })
    },
    // Note: No need for refreshAxiosToken - browser automatically sends HttpOnly cookie
    /**
     * Refreshes the WebSocket connection based on the authentication state.
     * Opens a connection if authenticated, closes it otherwise.
     */
    refreshWebSocketConnection() {
      if (this.isAuthenticated) {
        WS.createConnection()
      } else {
        WS.closeConnection()
      }
    },
    /**
     * Fetches current user data from server using HttpOnly cookie.
     * This is called on every page load - server is the source of truth.
     * No client-side storage (localStorage/sessionStorage) is used.
     */
    async fetchCurrentUser() {
      try {
        // Call /me endpoint - server validates HttpOnly cookie and returns user data
        const res = await axios.get('/access_control/me/')
        const { data } = res

        // Update the authentication state in the Vuex store (in-memory only)
        // This also sets authChecked = true
        await this.$store.dispatch('auth/setAuthData', data)

        // Refresh WebSocket connection now that we're authenticated
        this.refreshWebSocketConnection()

        // Update the last login timestamp
        const params = { username: data.user.username }
        await axios.post('/access_control/update_last_login/', null, { params })
      } catch (error) {
        // Mark auth as checked even on failure - user is not authenticated
        await this.$store.dispatch('auth/setAuthChecked', true)

        // For non-401 errors, log them
        if (error.response?.status !== 401) {
          // console.error('Failed to fetch current user:', error.message)
        }
        // Close WebSocket if not authenticated
        WS.closeConnection()
      }
    },
    /**
     * Handles WebSocket error events by displaying a persistent error message.
     * Suggests refreshing the page to re-establish the WebSocket connection.
     */
    onWsError(message) {
      this.$toast({
        component: ToastificationContent,
        props: {
          title: message,
          icon: 'AlertTriangleIcon',
          variant: 'danger',
          text: 'Refresh the page to re-establish websocket connection.',
        },
      }, {
        timeout: false, // Keeps the toast visible until user interaction
      })
    },
    /**
     * Updates the document's title based on the current page and app title.
     */
    updateDocumentTitle() {
      document.title = this.documentTitle
    },
    /**
     * Updates the page's favicon dynamically based on the current theme or configuration.
     */
    updateFavicon() {
      const favicon = document.getElementById('favicon')
      favicon.href = this.faviconUrl
    },
    onRefreshAuthData() {
      // Re-fetch user data from server
      this.fetchCurrentUser()
    },
    /**
     * Clears legacy auth data from localStorage and sessionStorage.
     * This ensures old auth data doesn't interfere with the new HttpOnly cookie approach.
     * Called once on app initialization.
     */
    clearLegacyAuthData() {
      // Clear legacy auth data from localStorage
      localStorage.removeItem('vuex') // Old vuex-persistedstate data
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('userData')
      localStorage.removeItem('v7-auth-username')

      // Clear legacy auth data from sessionStorage
      sessionStorage.removeItem('accessToken')
      sessionStorage.removeItem('refreshToken')
      sessionStorage.removeItem('userData')
      sessionStorage.removeItem('v7-auth-username')
    },
  },
}
</script>
