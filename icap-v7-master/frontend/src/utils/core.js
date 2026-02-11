/**
 * Organization: AIDocbuilder Inc.
 * File: utils/core.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-23
 *
 * Description:
 *   This module provides utility functions to manage data storage in `localStorage` with
 *   expiration handling. It includes methods to set and retrieve items from `localStorage`
 *   while ensuring that expired items are automatically removed.
 *
 * Dependencies:
 *   - none
 *
 * Main Features:
 *   - Setting items in `localStorage` with an expiration time (TTL).
 *   - Retrieving items from `localStorage` with expiration validation.
 *   - Automatically removing expired items from `localStorage`.
 *
 * Core Components:
 *   - `setItemWithExpiration`: Stores a value in `localStorage` with an expiration time.
 *   - `getItemWithExpiration`: Retrieves a value from `localStorage`, validating the expiration.
 *
 * Notes:
 *   - Expired items are automatically removed from `localStorage` during retrieval.
 *   - The `ttl` (time-to-live) for items is in milliseconds.
 */

export const setItemWithExpiration = (key, value, ttl) => {
  const now = new Date()

  const item = {
    value,
    expiry: now.getTime() + ttl,
  }

  localStorage.setItem(key, JSON.stringify(item))
}

export const getItemWithExpiration = key => {
  const itemStr = localStorage.getItem(key)

  if (!itemStr) {
    return null
  }

  const item = JSON.parse(itemStr)
  const now = new Date()

  if (now.getTime() > item.expiry) {
    localStorage.removeItem(key)

    return null
  }

  return item.value
}
