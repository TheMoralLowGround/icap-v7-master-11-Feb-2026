import jwtDefaultConfig from './jwtDefaultConfig'

/**
 * JWT Service for HttpOnly Cookie-based Authentication
 * 
 * This service has been simplified for HttpOnly cookie-based authentication.
 * The browser automatically handles sending the auth cookie with each request,
 * so we no longer need to manually manage tokens in client-side storage.
 * 
 * Security Benefits:
 * - Token is never accessible to JavaScript (prevents XSS attacks)
 * - Browser automatically includes cookie in requests
 * - Cookie is cleared server-side on logout
 */
export default class JwtService {
  // Will be used by this service for making API calls
  axiosIns = null

  // jwtConfig <= Will be used by this service
  jwtConfig = { ...jwtDefaultConfig }

  constructor(axiosIns, jwtOverrideConfig) {
    this.axiosIns = axiosIns
    this.jwtConfig = { ...this.jwtConfig, ...jwtOverrideConfig }

    // Ensure credentials (cookies) are included with all requests
    this.axiosIns.defaults.withCredentials = true

    // No need for request interceptor to add Authorization header
    // The browser automatically sends the HttpOnly cookie

    // Response interceptor for handling 401 errors
    this.axiosIns.interceptors.response.use(
      response => response,
      error => {
        // Handle 401 Unauthorized - redirect to login
        // Token refresh is handled server-side via Knox AUTO_REFRESH
        if (error.response && error.response.status === 401) {
          // Clear any client-side auth state and redirect to login
          // The cookie will be cleared by the server on logout
          window.location.href = '/login'
        }
        return Promise.reject(error)
      },
    )
  }

  login(...args) {
    return this.axiosIns.post(this.jwtConfig.loginEndpoint, ...args)
  }

  register(...args) {
    return this.axiosIns.post(this.jwtConfig.registerEndpoint, ...args)
  }

  logout() {
    return this.axiosIns.post(this.jwtConfig.logoutEndpoint)
  }

  logoutAll() {
    // Logout from all devices
    return this.axiosIns.post('/access_control/logoutall/')
  }
}
