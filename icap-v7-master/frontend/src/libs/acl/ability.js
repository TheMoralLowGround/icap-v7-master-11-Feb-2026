import { Ability } from '@casl/ability'
import { initialAbility } from './config'

/**
 * CASL Ability instance for access control
 * 
 * SECURITY: No client-side storage
 * - Abilities start with initialAbility (guest permissions)
 * - User abilities are updated after fetching user data from server
 * - Server is the source of truth via HttpOnly cookie authentication
 * - No localStorage/sessionStorage is used
 */
export default new Ability(initialAbility)
