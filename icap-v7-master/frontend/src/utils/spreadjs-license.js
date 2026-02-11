import axios from '@/libs/axios'
import * as GC from '@grapecity/spread-sheets'
import * as ExcelIO from '@grapecity/spread-excelio'

let licenseKey = null
let licensePromise = null

/**
 * Fetches the SpreadJS license key from the backend API.
 * The license is cached after the first fetch.
 * @returns {Promise<string>} The license key
 */
export async function fetchSpreadJSLicense() {
  if (licenseKey !== null) {
    return licenseKey
  }

  if (licensePromise !== null) {
    return licensePromise
  }

  licensePromise = axios
    .get('/pipeline/get_spreadjs_license/')
    .then(response => {
      licenseKey = response.data.license_key || ''
      return licenseKey
    })
    .catch(() => {
      // console.error('Failed to fetch SpreadJS license:', error)
      licenseKey = ''
      return licenseKey
    })
    .finally(() => {
      licensePromise = null
    })

  return licensePromise
}

/**
 * Initializes the SpreadJS license by fetching it from the backend
 * and applying it to both GC.Spread.Sheets and ExcelIO.
 * @returns {Promise<string>} The license key
 */
export async function initSpreadJSLicense() {
  const key = await fetchSpreadJSLicense()
  GC.Spread.Sheets.LicenseKey = key
  ExcelIO.LicenseKey = key
  return key
}

/**
 * Gets the cached license key synchronously.
 * Returns null if the license hasn't been fetched yet.
 * @returns {string|null} The cached license key or null
 */
export function getCachedLicense() {
  return licenseKey
}
