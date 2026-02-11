import store from '../store'
import waitForAuthChecked from './utils'

/**
 * Auth middleware for protected routes.
 * Waits for auth to be checked with server before making redirect decisions.
 * This is necessary because auth state is fetched from server on page load.
 */

export default async function auth(to, from, next) {
  await waitForAuthChecked()

  // Now check if authenticated
  if (!store.getters['auth/isAuthenticated']) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
}
