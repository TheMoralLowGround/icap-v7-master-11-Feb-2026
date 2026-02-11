/**
 * Organization: AIDocbuilder Inc.
 * File: batch/key-helper.js
 * Version: 6.0
 *
 * Authors:
 *   - Vinay: Initial implementation
 *   - Ali: Code optimization
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 * This file contains utility functions used to create and normalize key items for batch processing in the application.
 * The functions help generate default key structures, normalize key item values, and manage compound key items.
 * It also includes functions to generate default keys based on batch type (Excel or other) and handle compound key items.
 *
 * Main Features/Functions:
 * - getDefaultKey: Creates a default key object, optionally based on whether the batch is Excel-related.
 * - getDefaultKeys: Creates an array of default keys, useful for initializing multiple key items at once.
 * - getDefaultCompoundKeys: Creates default compound key items based on a specific compound key setting name.
 * - normalizeKeyItemValues: Ensures key items conform to a consistent structure, applying defaults and migrating old formats.
 *
 * Dependencies:
 * - `uuidv4`: Used to generate unique IDs for each key.
 * - `store`: Vuex store for accessing shared application state and getters.
 */

// Import the `uuidv4` function to generate unique IDs
import { v4 as uuidv4 } from 'uuid'

// Import the Vuex store to access shared state and getters
import store from '@/store'

// Function to create a default key object
// Takes a parameter `isExcelBatch` to determine the type of key
// Takes an optional `defaultType` parameter to override the default type
const getDefaultKey = (isExcelBatch, defaultType = null) => {
  const defaultKey = {
    id: uuidv4(), // Unique identifier for the key
    keyLabel: '', // Label for the key
    qualifierValue: '', // Qualifier value for the key
    type: defaultType || (isExcelBatch ? 'cellRange' : 'keys'), // Key type based on `defaultType` or `isExcelBatch`
    shape: '', // Shape property (e.g., for positional data)
    definition_prompt: {
      DocClass: '',
      Field_Description: '',
      Rules_Description: '',
    }, // Definition prompt object with three properties for AI extraction
    startPos: '', // Start position (optional)
    topPos: '', // Top position (optional)
    endPos: '', // End position (optional)
    bottomPos: '', // Bottom position (optional)
    pageId: '', // Page identifier
    pageIndex: '', // Page index (optional)
    anchorShapes: null, // Anchor shapes (e.g., for specific data points)
    selector: false, // Whether this key acts as a selector
    extractMultiple: false, // Whether to extract multiple entries
    removeDuplicates: false, // Whether to remove duplicate entries
    singleColumnExtractor: null, // Extractor for single-column data
    regexExtractor: null, // Regex pattern for data extraction
    advanceSettings: {}, // Advanced configuration options
    typeData: {}, // Additional type-specific data
    isCompoundKey: false, // Indicates if this key is part of a compound key
    compoundItems: [], // Items composing a compound key
    isCompoundItem: false, // Indicates if this key is a compound item
    keyItemValues: {
      startPos: '',
      endPos: '',
      topPos: '',
      bottomPos: '',
      pageIndex: '',
      pageId: '',
      selectedText: '',
    }, // Info of value of label field in Keyitems table in case of selector type
    keyItemLabels: {
      startPos: '',
      endPos: '',
      topPos: '',
      bottomPos: '',
      pageIndex: '',
      pageId: '',
      selectedText: '',
    }, // info of label field in Keyitems table in case of selector type
  }
  return defaultKey
}

// Function to create an array of default keys
// Takes `count` (number of keys), `isExcelBatch`, and optional `defaultType` as parameters
const getDefaultKeys = (count, isExcelBatch, defaultType = null) => {
  const keys = []
  for (let i = 0; i < count; i += 1) {
    keys.push(getDefaultKey(isExcelBatch, defaultType)) // Generate and push default keys
  }
  return keys
}

// Function to create default compound key items
// Takes `isExcelBatch` and `compoundKeySettingName` as parameters
const getDefaultCompoundKeys = (isExcelBatch, compoundKeySettingName) => {
  // Retrieve default behavior and compound key settings from the store
  const defaultBehaviour = store.getters['defaultSettings/defaultBehaviour']
  const compoundKeySettings = store.getters['definitionSettings/compoundKeys']

  // Find the compound key settings by name
  const compoundKeySetting = compoundKeySettings.find(item => item.name === compoundKeySettingName)
  const keyItems = compoundKeySetting ? compoundKeySetting.keyItems : []

  // Map through key items to create compound key items
  const compoundKeyItems = keyItems.map(keyItem => {
    const record = getDefaultKey(isExcelBatch) // Create a default key
    record.keyLabel = keyItem.keyValue // Set the key label
    record.isCompoundItem = true // Mark as a compound item

    // Apply default behavior settings for specific compound keys
    if (defaultBehaviour.compoundKeys.includes(compoundKeySettingName)) {
      record.type = 'static' // Static type for predefined compound keys
      record.shape = 'ERROR' // Set a default "error" shape
    }

    return record
  })

  return compoundKeyItems
}

// const toNormalLabel = camelCaseStr => {
//   if (!camelCaseStr) return ''

//   // If the string already contains spaces, assume it's already in normal format
//   if (camelCaseStr.includes(' ')) {
//     return camelCaseStr
//   }

//   // If all lowercase or no camelCase pattern, return as is
//   if (!/[a-z][A-Z]/.test(camelCaseStr)) {
//     return camelCaseStr
//   }

//   return camelCaseStr
//     .replace(/([A-Z])/g, ' $1') // Insert space before capital letters
//     .replace(/^./, s => s.toUpperCase()) // Capitalize first letter
// }
// Function to normalize key item values
// Ensures the key objects have a consistent structure
const normalizeKeyItemValues = (items, optionsKeyItems) => {
  const normalizedItems = items.map(record => {
    // Find matching options for the current record
    const optionsKeyItem = optionsKeyItems.find(e => e.keyLabel === record.keyLabel)

    // Normalize definition_prompt - handle both old string format and new object format
    let normalizedDefinitionPrompt
    if (typeof record.definition_prompt === 'string') {
      // Old format: convert string to object
      normalizedDefinitionPrompt = {
        DocClass: '',
        Field_Description: '',
        Rules_Description: '',
      }
    } else if (record.definition_prompt && typeof record.definition_prompt === 'object') {
      // New format: ensure all required properties exist
      normalizedDefinitionPrompt = {
        DocClass: record.definition_prompt.DocClass || '',
        Field_Description: record.definition_prompt.Field_Description || '',
        Rules_Description: record.definition_prompt.Rules_Description || '',
      }
    } else {
      // Default
      normalizedDefinitionPrompt = {
        DocClass: '',
        Field_Description: '',
        Rules_Description: '',
      }
    }

    // Create a normalized item with default values
    const item = {
      id: record.id || uuidv4(), // Ensure a unique ID
      // keyLabel: toNormalLabel(record.keyLabel || ''), // Normalize key label
      keyLabel: record.keyLabel || '', // Normalize key label
      qualifierValue: String(record.qualifierValue || ''), // Normalize qualifier value
      definition_prompt: normalizedDefinitionPrompt, // Normalize definition_prompt value
      type: record.type !== undefined ? record.type : '', // Preserve or default the type
      shape: String(record.shape || ''), // Normalize shape
      startPos: String(record.startPos || ''), // Normalize start position
      topPos: String(record.topPos || ''), // Normalize top position
      endPos: String(record.endPos || ''), // Normalize end position
      bottomPos: String(record.bottomPos || ''), // Normalize bottom position
      pageId: String(record.pageId || ''), // Normalize page ID
      pageIndex: String(record.pageIndex || ''), // Normalize page index
      anchorShapes: record.anchorShapes !== undefined ? record.anchorShapes : null, // Preserve or default anchor shapes
      selector: record.selector !== undefined ? record.selector : false, // Preserve or default selector status
      export: !!record.export, // Ensure a boolean value for export
      extractMultiple: record.extractMultiple !== undefined ? record.extractMultiple : false, // Preserve or default extractMultiple
      removeDuplicates: record.removeDuplicates !== undefined ? record.removeDuplicates : false, // Preserve or default removeDuplicates
      singleColumnExtractor: record.singleColumnExtractor !== undefined ? record.singleColumnExtractor : null, // Preserve extractor
      excelRegexExtractor: record.excelRegexExtractor !== undefined ? record.excelRegexExtractor : null, // Preserve regex extractor
      regexExtractor: record.regexExtractor !== undefined ? record.regexExtractor : null, // Preserve regex extractor
      advanceSettings: record.advanceSettings !== undefined ? record.advanceSettings : {}, // Preserve or default advanced settings
      typeData: record.typeData !== undefined ? record.typeData : {}, // Preserve or default type data
      isCompoundKey: record.isCompoundKey !== undefined ? record.isCompoundKey : false, // Preserve compound key flag
      compoundItems: record.compoundItems !== undefined ? record.compoundItems : [], // Preserve or default compound items
      isCompoundItem: record.isCompoundItem !== undefined ? record.isCompoundItem : false, // Preserve compound item flag
      keyItemValues: record.keyItemValues !== undefined ? { ...record.keyItemValues } : {
        startPos: '',
        endPos: '',
        topPos: '',
        bottomPos: '',
        pageIndex: '',
        pageId: '',
        selectedText: '',
      },
      keyItemLabels: record.keyItemLabels !== undefined ? { ...record.keyItemLabels } : {
        startPos: '',
        endPos: '',
        topPos: '',
        bottomPos: '',
        pageIndex: '',
        pageId: '',
        selectedText: '',
      },
    }

    // Override export property if it exists in optionsKeyItem
    if (optionsKeyItem && Object.keys(optionsKeyItem).includes('export')) {
      item.export = optionsKeyItem.export
    }

    // Migrate old key formats to the new structure
    if (item.type === '') {
      item.type = item.selector ? 'selector' : 'keys' // Infer type based on selector status
    }

    return item
  })

  return normalizedItems
}

// Export the utility functions
export {
  getDefaultKey, getDefaultKeys, normalizeKeyItemValues, getDefaultCompoundKeys,
}
