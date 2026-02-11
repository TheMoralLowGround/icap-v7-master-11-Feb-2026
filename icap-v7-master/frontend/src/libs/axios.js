import Vue from 'vue'
// axios
import axios from 'axios'

import getEnv from '@/utils/env'
import store from '@/store'
import router from '@/router'

const apiBaseUrl = `${getEnv('VUE_APP_BACKEND_URL')}/api`

axios.defaults.baseURL = apiBaseUrl
// Include credentials (cookies) with all requests for HttpOnly cookie auth
axios.defaults.withCredentials = true

// Admin-only API endpoints that require superuser/staff access
// If a 403 is received on these endpoints, it indicates the user's admin status was tampered
const ADMIN_ONLY_ENDPOINTS = [
  '/application-settings/',
  '/dashboard/developer-settings/',
  '/dashboard/create_default_dev_settings/',
  '/dashboard/import_developer_settings/',
  '/dashboard/template/',
  '/dashboard/export_templates/',
  '/dashboard/import_templates/',
  '/dashboard/clone_template/',
  '/dashboard/template_upload_document/',
  '/dashboard/get_template_definition/',
  '/dashboard/update_template_definition_by_version/',
  '/dashboard/admin/projects/',
  '/pipeline/batch_path_content/',
  '/pipeline/download_batch_zip/',
  '/pipeline/upload_batch_zip/',
  '/pipeline/remove_not_in_use_batches/',
]

/**
 * Check if the request URL matches any admin-only endpoint
 */
function isAdminOnlyEndpoint(url) {
  if (!url) return false
  return ADMIN_ONLY_ENDPOINTS.some(endpoint => url.includes(endpoint))
}

const axiosIns = axios.create({
  // You can add your headers here
  // ================================
  baseURL: apiBaseUrl,
  // Include credentials (cookies) with all requests for HttpOnly cookie auth
  withCredentials: true,
  // timeout: 1000,
  // headers: {'X-Custom-Header': 'foobar'}
})

/**
 * Handle 403 response - reset isAdmin and redirect
 * This catches cases where user tampered with is_superuser in client
 */
function handle403Response(config, response) {
  // Check if this is an admin-only endpoint OR any 403 from backend middleware
  const isAdminEndpoint = isAdminOnlyEndpoint(config?.url)

  if (response?.status === 403 && isAdminEndpoint) {
    // Reset admin status in the store (user likely tampered with it)
    if (store.getters['auth/isAdmin']) {
      store.commit('auth/SET_AUTH_DATA', {
        token: store.getters['auth/token'],
        userName: store.getters['auth/userName'],
        isAdmin: false,
        projectCountries: store.getters['auth/projectCountries'],
      })

      // Redirect to 403 error page
      router.push({ name: 'error-403' })
    }
  } else if (response?.status === 403) {
    // Generic 403 (from middleware checking Referer) - just redirect
    router.push({ name: 'error-403' })
  }
}

// Response interceptor to handle 403 on admin endpoints
axiosIns.interceptors.response.use(
  response => response,
  error => {
    handle403Response(error.config, error.response)
    return Promise.reject(error)
  },
)

// Also add interceptor to the default axios instance
axios.interceptors.response.use(
  response => response,
  error => {
    handle403Response(error.config, error.response)
    return Promise.reject(error)
  },
)

Vue.prototype.$http = axiosIns

export default axiosIns
