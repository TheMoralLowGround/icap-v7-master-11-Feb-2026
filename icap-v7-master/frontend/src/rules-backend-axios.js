/**
 * Organization: AIDocbuilder Inc.
 * File: rules-backend-api.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *
 * Last Updated By: Vinay
 * Last Updated At: 2023-11-01
 *
 * Description:
 *   Configures and exports an Axios instance for making API requests
 *   to the Rules Backend service.
 *
 * Dependencies:
 *   - Axios: HTTP client for making API requests.
 *   - getEnv: Utility function for retrieving environment variables.
 *
 * Main Features:
 *   - Dynamically sets the base URL for the API using the environment variable
 *     `VUE_APP_RULES_BACKEND_URL`.
 *   - Creates a reusable Axios instance pre-configured with the backend's base URL.
 *
 * Core Components:
 *   - Axios instance: Configured with the Rules Backend API base URL.
 *
 * Notes:
 *   - The base URL is retrieved dynamically to support different environments (e.g., dev, staging, prod).
 *   - This file ensures consistent and centralized configuration for API calls to the Rules Backend.
 */

import axios from 'axios'
import getEnv from '@/utils/env'

const apiBaseUrl = `${getEnv('VUE_APP_RULES_BACKEND_URL')}/api`

const axiosIns = axios.create({
  baseURL: apiBaseUrl,
})

export default axiosIns
