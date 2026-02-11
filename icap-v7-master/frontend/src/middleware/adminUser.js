import store from '../store'
import waitForAuthChecked from './utils'

/**
 * Admin user middleware for admin-only routes.
 * Waits for auth to be checked with server before making redirect decisions.
 */

export default async function adminUser(to, from, next) {
  await waitForAuthChecked()

  // Now check if admin
  if (!store.getters['auth/isAdmin']) {
    next({ name: 'error-403' })
  } else {
    next()
  }
}
