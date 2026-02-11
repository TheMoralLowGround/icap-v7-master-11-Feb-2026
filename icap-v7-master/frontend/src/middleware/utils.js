import store from '../store'

/**
 * Shared middleware utility functions.
 *
 * This file provides common helpers used across multiple middleware files
 * to avoid code duplication.
 */

/**
 * Wait until auth has been checked with the server (or timeout).
 *
 * This is necessary for cookie-based authentication where auth state
 * is fetched from the server on page load via /api/access_control/me/.
 *
 * Middleware should wait for this check before making routing decisions
 * to avoid race conditions during initial page load.
 *
 * @returns {Promise<void>} Resolves when auth is checked or after timeout
 */
function waitForAuthChecked() {
  const maxWait = 5000 // Maximum wait time in milliseconds
  const interval = 50 // Check interval in milliseconds
  const start = Date.now()

  return new Promise(resolve => {
    function check() {
      if (store.getters['auth/authChecked'] || Date.now() - start >= maxWait) {
        resolve()
      } else {
        setTimeout(check, interval)
      }
    }

    check()
  })
}

export default waitForAuthChecked
