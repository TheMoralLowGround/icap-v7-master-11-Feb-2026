import store from '../store'
import waitForAuthChecked from './utils'

/**
 * Guest middleware for public routes (like login).
 * Redirects to home if user is already authenticated.
 * Waits for auth to be checked with server before making redirect decisions.
 */

export default async function guest(to, from, next) {
  await waitForAuthChecked()

  // Now check if authenticated
  if (store.getters['auth/isAuthenticated']) {
    next({ name: 'home' })
  } else {
    next()
  }
}
