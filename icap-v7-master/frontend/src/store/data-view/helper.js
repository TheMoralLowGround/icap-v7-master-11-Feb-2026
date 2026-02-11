/**
 * Organization: AIDocbuilder Inc.
 * File: helper.js
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
 *   This file contains utility functions to support view toolbar data operations and enhance reusability across the application.
 *
 * Dependencies:
 *   - None (or specify if any external libraries are used)
 *
 * Main Features:
 *   - Provide reusable helper functions for data manipulation.
 *   - Simplify API response handling and state updates.
 *   - Offer utility methods for toolbar-related computations.
 */

/* eslint-disable import/prefer-default-export */
// Disables the ESLint rule that enforces default exports for modules

import { v4 as uuidv4 } from 'uuid' // Importing the uuid function to generate unique identifiers
// Function to create a new table object with the given settings, table ID, and table name
const getNewTable = (tableSettings, tableId = 0, tableName = 'Main Table', isAuto) => {
  // Create the new table object with default structure
  const newTable = {
    table_id: tableId, // Table ID (defaults to 0 if not provided)
    table_unique_id: uuidv4(), // Generates a unique identifier for the table
    table_name: tableName, // Table name (defaults to 'Main Table' if not provided)
    table_definition_data: { // Contains the structure of the table
      models: {}, // Models for the table (will be populated with fields)
      columns: [], // Columns in the table (empty initially)
      keyItems: [], // Key items (empty initially)
      ruleItems: [], // Rule items (empty initially)
      normalizerItems: [], // Normalizer items (empty initially)
      lookupItems: [], // Lookup items (empty initially)
    },
  }

  // Initialize the 'models' object to store model fields
  const models = {}
  // Retrieve the 'fields' from the provided 'tableSettings'
  const modelFields = tableSettings.model.fields

  // Loop through each field in 'modelFields' and assign a default value
  modelFields.forEach(modelField => {
    let value

    // If a default value is provided for the model field, use it, otherwise set an empty string
    if (modelField.defaultValue !== undefined) {
      value = modelField.defaultValue
    } else {
      value = ''
    }
    // if (modelField.key === 'type' && isAuto === 'auto') {
    //   models[modelField.key] = 'auto'
    // }
    // Add the field to the 'models' object, using the field's 'key' as the key
    models[modelField.key] = value
    // If isAuto is 'auto', override only the 'type' key
    if (isAuto === 'auto' && Object.prototype.hasOwnProperty.call(models, 'type')) {
      models.type = 'auto'
    }
  })

  // Assign the populated 'models' object to the 'newTable' under 'table_definition_data'
  newTable.table_definition_data.models = models

  // Return the newly created table object
  return newTable
}

// Function to extract and structure the 'key' data from a given 'data' object
const getDefinitionKey = data => {
  // Extract the 'key' from the provided data object
  const keyData = data?.key

  // Return an object with properties corresponding to the different parts of the key data
  return ({
    models: keyData?.models || [], // Models (defaults to an empty array if not present)
    items: keyData?.items || [], // Items with prompt field ensured
    ruleItems: keyData?.ruleItems || [], // Rule items (defaults to an empty array if not present)
    sampleBlocks: keyData?.sampleBlocks || [], // Sample blocks (defaults to an empty array if not present)
    notInUseItems: keyData?.notInUseItems || [], // Items not in use (defaults to an empty array if not present)
    lookupItems: keyData?.lookupItems || [], // Lookup items (defaults to an empty array if not present)
  })
}

const generateModelsFromSettings = tableSettings => {
  const models = {}
  const modelFields = tableSettings.model.fields || []

  modelFields.forEach(modelField => {
    if (modelField.key === 'type') {
      models[modelField.key] = 'auto'
    } else if (modelField.defaultValue === undefined) {
      models[modelField.key] = ''
    } else if (modelField.defaultValue === null) {
      models[modelField.key] = ''
    } else {
      models[modelField.key] = modelField.defaultValue
    }
  })
  if (!Object.prototype.hasOwnProperty.call(models, 'sumOfChargeAmount') || typeof models.sumOfChargeAmount !== 'object') {
    models.sumOfChargeAmount = { dty: false, vat: false, oth: false }
  }

  return models
}

// Main vendorDefinition without getNewTable
const vendorDefinition = (tables = [], tableSettings) => ({
  definition_id: '',
  vendor: '',
  type: '',
  name_matching_text: '',
  cw1: false,
  key: {
    items: [],
    models: [],
    ruleItems: [],
    lookupItems: [],
    sampleBlocks: [],
    notInUseItems: [],
    cell_range_permission: '',
  },
  table: tables.map((table, index) => ({
    table_id: index,
    table_name: table.table_name || `Table ${index + 1}`,
    table_unique_id: table.table_unique_id || uuidv4(),
    table_definition_data: {
      models: generateModelsFromSettings(tableSettings), // Your function used here
      columns: [],
      keyItems: [],
      ruleItems: [],
      normalizerItems: [],
      lookupItems: [],
    },
  })),
})

const findTableByName = (tables, tableName) => {
  if (!tables || !Array.isArray(tables)) return null
  return tables.find(table => table.table_name === tableName)
}

// Helper function to find table index by name
const findTableIndexByName = (tables, tableName) => {
  if (!tables || !Array.isArray(tables)) return -1
  return tables.findIndex(table => table.table_name === tableName)
}

// Exporting the functions so they can be used in other parts of the application
export {
  getNewTable, // Function to create a new table object
  getDefinitionKey, // Function to retrieve the structured key data from a given data object
  vendorDefinition,
  findTableByName,
  findTableIndexByName,
}
