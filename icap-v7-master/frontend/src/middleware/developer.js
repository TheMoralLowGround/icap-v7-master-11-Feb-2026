import store from '../store'
import waitForAuthChecked from './utils'

/**
 * Developer middleware for developer-only routes.
 * Waits for auth to be checked with server before making redirect decisions.
 */

export default async function developer(to, from, next) {
  await waitForAuthChecked()

  // Now check if developer
  if (!store.getters['developerSettings/isDeveloper']) {
    next({ name: 'error-403' })
  } else {
    next()
  }
}
