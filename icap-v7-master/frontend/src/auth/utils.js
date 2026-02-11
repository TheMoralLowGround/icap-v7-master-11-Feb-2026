/**
 * Auth utilities for HttpOnly cookie-based authentication
 * 
 * SECURITY: Server-Side Session Management
 * - Auth token is stored in HttpOnly cookie (not accessible to JavaScript)
 * - NO client-side storage (localStorage/sessionStorage) is used
 * - Server is the source of truth
 * - User data is fetched from server on each page load via /api/me endpoint
 * 
 * These utility functions are kept for backward compatibility but most
 * auth state should be accessed via Vuex store getters.
 */

import store from '@/store'

/**
 * Return if user is logged in (checks Vuex store state)
 * Note: This checks in-memory Vuex state populated from server on page load.
 * The actual auth is validated server-side via HttpOnly cookie.
 */
// eslint-disable-next-line arrow-body-style
export const isUserLoggedIn = () => {
  return store.getters['auth/isAuthenticated']
}

/**
 * Get user data from Vuex store (in-memory only)
 */
export const getUserData = () => {
  const userName = store.getters['auth/userName']
  const isAdmin = store.getters['auth/isAdmin']
  if (!userName) return null
  return { userName, isAdmin }
}

/**
 * This function is used for demo purpose route navigation
 * In real app you won't need this function because your app will navigate to same route for each users regardless of ability
 * Please note role field is just for showing purpose it's not used by anything in frontend
 * We are checking role just for ease
 * NOTE: If you have different pages to navigate based on user ability then this function can be useful. However, you need to update it.
 * @param {String} userRole Role of user
 */
export const getHomeRouteForLoggedInUser = userRole => {
  if (userRole === 'admin') return '/'
  if (userRole === 'client') return { name: 'access-control' }
  return { name: 'auth-login' }
}
