/**
 * Utility helpers for normalizing user-provided identifiers.
 */

/**
 * Return a safe process name derived from arbitrary user input.
 *
 * The function trims whitespace, swaps any disallowed character for an
 * underscore, collapses duplicated separators, strips leading/trailing
 * separators, and enforces a maximum length. Throws Error if the
 * result would be empty (e.g., the input only contained punctuation).
 *
 * @param {string} rawName - The raw process name to normalize
 * @param {number} maxLength - Maximum length of the normalized name (default: 128)
 * @returns {string} - Normalized process name
 * @throws {Error} - If the process name is empty or contains no alphanumeric characters
 */
export function normalizeProcessName(rawName, maxLength = 128) {
  if (rawName == null) {
    throw new Error('Process name cannot be empty.')
  }

  let cleaned = String(rawName).trim()

  if (!cleaned) {
    throw new Error('Process name cannot be empty.')
  }

  // Replace any disallowed character (anything not 0-9, A-Z, a-z, _, -) with underscore
  cleaned = cleaned.replace(/[^0-9A-Za-z_-]+/g, '_')

  // Collapse duplicated separators (_ or -)
  cleaned = cleaned.replace(/[_-]{2,}/g, '_')

  // Strip leading/trailing separators
  cleaned = cleaned.replace(/^[_-]+|[_-]+$/g, '')

  if (!cleaned) {
    throw new Error('Process name must contain at least one alphanumeric character.')
  }

  // Enforce maximum length
  if (cleaned.length > maxLength) {
    cleaned = cleaned.substring(0, maxLength)
  }

  return cleaned
}

export default {
  normalizeProcessName,
}
