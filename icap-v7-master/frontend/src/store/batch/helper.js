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
 *   This file contains utility functions to support batch data operations and enhance reusability across the application.
 *
 * Dependencies:
 *   - env
 *
 * Main Features:
 *   - Provide reusable helper functions for data manipulation.
 *   - Simplify API response handling and state updates.
 *   - Offer utility methods for batch-related computations.
 */

import getEnv from '@/utils/env'
import {
  flatNodes, getKeyNodeTitle, getNodeLabel,
} from './flatNode'
// Custom recursive search function to traverse and search nodes based on a value.
// Parameters:
// - nodes: The array of nodes to search within.
// - searchVal: The value to search for (case-insensitive).
// - parentIds: The array of parent node IDs, used to track the hierarchy during recursion.
// Returns an object containing:
//   - expandedIds: An array of IDs of nodes that need to be expanded to reveal matching nodes.
//   - matchedIds: An array of IDs of nodes that directly match the search value.
const search = (nodes, searchVal, parentIds = []) => {
  let expandedIds = [] // Tracks IDs of nodes to be expanded.
  let matchedIds = [] // Tracks IDs of nodes that match the search value.

  nodes.forEach(node => {
    // Check if the current node is of type 'word' or 'words' and contains the search value.
    if (node.type === 'word' || node.type === 'words') {
      const nodeText = String(node.v)?.toLowerCase() // Convert node value to string and lowercase for comparison.
      if (nodeText.includes(searchVal)) {
        expandedIds = expandedIds.concat(parentIds) // Add parent IDs for expansion.
        expandedIds.push(node.id) // Add current node ID for expansion.
        matchedIds.push(node.id) // Add current node ID as a match.
      }
    }
    // Recursively search child nodes if they exist.
    if (node.children && node.children.length > 0) {
      const searchResult = search(node.children, searchVal, [...parentIds, node.id])

      // Merge results from child nodes.
      expandedIds = expandedIds.concat(searchResult.expandedIds)
      matchedIds = matchedIds.concat(searchResult.matchedIds)
    }
  })

  return {
    expandedIds, // All IDs to expand to reveal matches.
    matchedIds, // All matching node IDs.
  }
}

// Wrapper function to search nodes and retrieve expanded and matched IDs.
// Parameters:
// - nodes: The array of nodes to search within.
// - searchValue: The search term (case-insensitive).
// Returns an object containing:
//   - expandedIds: A unique array of IDs of nodes to expand.
//   - matchedIds: An array of IDs of nodes that directly match the search term.
const searchNodes = (nodes, searchValue) => {
  const searchResult = search(nodes, searchValue?.toLowerCase()) // Convert search value to lowercase for consistency.
  const expandedIds = [...new Set(searchResult.expandedIds)] // Ensure unique IDs in the expanded list.
  return {
    expandedIds, // IDs to expand.
    matchedIds: searchResult.matchedIds, // Matching node IDs.
  }
}

// Recursive function to expand nodes based on specified node types.
// Parameters:
// - nodes: The array of nodes to traverse.
// - nodeTypes: Array of node types to expand.
// - parentIds: Array of parent node IDs for tracking hierarchy (default is an empty array).
// Returns:
// - An array of IDs for nodes to be expanded.
const expandByType = (nodes, nodeTypes, parentIds = []) => {
  let expandedIds = [] // Stores IDs of nodes to be expanded.

  nodes.forEach(node => {
    // Check if the current node's type matches one of the specified node types.
    if (nodeTypes.includes(node.type)) {
      expandedIds = expandedIds.concat(parentIds) // Add parent IDs to the list.
      expandedIds.push(node.id) // Add the current node ID to the list.
    }

    // Recursively process child nodes if they exist.
    if (node.children && node.children.length > 0) {
      expandedIds = expandedIds.concat(expandByType(node.children, nodeTypes, [...parentIds, node.id]))
    }
  })

  return expandedIds
}

// Wrapper function to retrieve unique expanded IDs for nodes of specific types.
// Parameters:
// - nodes: The array of nodes to traverse.
// - nodeTypes: Array of node types to expand.
// Returns:
// - A unique array of IDs for nodes to expand.
const expandNodesByType = (nodes, nodeTypes) => {
  let expandedIds = expandByType(nodes, nodeTypes)
  expandedIds = [...new Set(expandedIds)] // Remove duplicate IDs.
  return expandedIds
}

// Utility functions for backward compatibility with older data formats.
// Provides flexible handling of node properties that may vary between formats.
// Functions for backward compatibility for old data format

// Wrapper function to initiate flattening of nodes
const getFlatNodes = (nodes, expandedNodes, matchedNodes, selectedNode, highlightRootNodes, addressBlockKeys, documentSortOrder = 'asc') => flatNodes(nodes, expandedNodes, matchedNodes, selectedNode, highlightRootNodes, addressBlockKeys, 0, null, null, null, null, false, false, null, null, documentSortOrder)

// Function to parse a hierarchical structure of nodes into a flattened object
// Parameters:
// - nodes: Array of nodes to be parsed.
// - parentPageId: ID of the parent page, default is null.
// - parentDocId: ID of the parent document, default is null.
const parseNodes = (nodes, parentPageId = null, parentDocId = null) => {
  const flattenNodes = {} // Object to store flattened nodes

  nodes.forEach(node => {
    // Determine the pageId and docId based on the node type or parent context
    const pageId = node.type === 'page' ? node.id : (node.pageId ?? parentPageId)
    const docId = (node.type === 'document' || node.type === 'docBuilder') ? node.id : parentDocId

    // Check if the node should be highlighted for Excel or PDF
    const pos = node.pos ?? null // Node position for highlighting in PDF
    const highlightForExcel = Boolean(node.cellRange && node.worksheet_name) // Highlighting for Excel
    const highlightForPdf = Boolean(pos && pageId && node.type !== 'page') // Highlighting for PDF
    const highlight = highlightForPdf || highlightForExcel // Combine both highlighting conditions

    // Add the node to the flattened structure
    flattenNodes[node.id] = {
      docId, // Associated document ID
      pageId, // Associated page ID
      pos, // Position for PDF highlighting
      highlight, // Whether the node is highlighted
      type: node.type, // Type of the node
      label: node.label ?? '', // Label of the node
      cellRange: node.cellRange ?? null, // Cell range for Excel highlighting
      sheetName: node.worksheet_name ?? null, // Worksheet name for Excel highlighting
    }

    // Recursively parse children if any
    if (Array.isArray(node.children) && node.children.length > 0) {
      Object.assign(flattenNodes, parseNodes(node.children, pageId, docId))
    }
  })

  return flattenNodes
}

// Wrapper function to initiate the parsing of nodes
// - nodes: Array of hierarchical nodes to parse
const getNodes = nodes => parseNodes(nodes)
/**
 * Extracts all nodes of type 'word' from the given nodes and their children.
 *
 * @param {Array} nodes - An array of nodes to search.
 * @returns {Array} - An array of word nodes.
 */
const getWordNodes = nodes => {
  let wordNodes = []

  nodes.forEach(node => {
    // Add the node to wordNodes if it is of type 'word'
    if (node.type === 'word') {
      wordNodes.push(node)
    }

    // Recursively search children if they exist
    if (node.children && node.children.length > 0) {
      const searchResult = getWordNodes(node.children)
      wordNodes = wordNodes.concat(searchResult)
    }
  })

  return wordNodes
}

/**
 * Parses a single page node and its children to create a flattened structure.
 *
 * @param {Object} node - The node to parse.
 * @returns {Object} - An object representing the flattened page structure.
 */
const parsePage = node => {
  let flattenedPage = {}

  // Check if the node is a page
  if (node.type === 'page') {
    const pageStyles = {}

    // Parse styles if they exist
    if (node.styles) {
      node.styles.forEach(pageStyle => {
        const styleObject = {}
        const styles = pageStyle.v.split(';')
        styles.forEach(style => {
          const [key, value] = style.split(':')
          if (key) {
            styleObject[key.trim()] = value.trim()
          }
        })
        pageStyles[pageStyle.id] = styleObject
      })
    }

    // Create the page entry with word nodes, imageFile, and styles
    flattenedPage[node.id] = {
      pos: node.pos || null, // Position information of the page, if available
      wordNodes: getWordNodes(node.children).map(wordNode => ({
        id: wordNode.id, // Word node ID
        pos: wordNode.pos, // Position of the word node
        v: wordNode.v, // Value or text of the word node
        styleId: wordNode.s, // Associated style ID
      })),
      imageFile: node.IMAGEFILE, // Associated image file for the page
      styles: pageStyles, // Parsed styles for the page
    }
  }

  // If the node has children, recursively parse them
  if (node.children && node.children.length > 0) {
    node.children.forEach(childNode => {
      const parsedChild = parsePage(childNode)
      flattenedPage = { ...flattenedPage, ...parsedChild }
    })
  }

  return flattenedPage
}

/**
 * Parses an array of nodes to create a flattened structure of pages.
 *
 * @param {Array} nodes - An array of nodes to parse.
 * @returns {Object} - An object containing all flattened pages.
 */
const parsePages = nodes => {
  let flatenPages = {}

  nodes.forEach(node => {
    if (node?.type === 'page') {
      const pageStyles = {}

      // Parse styles if they exist
      if (node.styles) {
        node.styles.forEach(pageStyle => {
          const styleObject = {}
          const styles = pageStyle.v.split(';')
          styles.forEach(style => {
            const [key, value] = style.split(':')
            if (key) {
              styleObject[key.trim()] = value.trim()
            }
          })
          pageStyles[pageStyle.id] = styleObject
        })
      }

      // Create the page entry with word nodes, imageFile, and styles
      flatenPages[node.id] = {
        pos: node.pos || null, // Position information of the page, if available
        wordNodes: getWordNodes(node.children).map(wordNode => ({
          id: wordNode.id, // Word node ID
          pos: wordNode.pos, // Position of the word node
          v: wordNode.v, // Value or text of the word node
          styleId: wordNode.s, // Associated style ID
        })),
        imageFile: node.IMAGEFILE, // Associated image file for the page
        styles: pageStyles, // Parsed styles for the page
      }
    }

    // Recursively parse children if they exist
    if (node?.children && node?.children.length > 0) {
      const searchResult = parsePages(node.children)
      flatenPages = { ...flatenPages, ...searchResult }
    }
  })

  return flatenPages
}

/**
 * Wrapper function to parse and retrieve all pages from the given nodes.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed pages.
 */
const getPages = nodes => parsePages(nodes)

/**
 * Parse document root nodes to create a map of node IDs to their children positions.
 *
 * @param {Array} pageNodes - An array of pageNodes to process.
 * @returns {Object} - An object containing all parsed page nodes.
 */
const parseDocumentRootNodes = pageNodes => {
  const res = {}
  pageNodes.forEach(pageNode => {
    // Map each pageNode's ID to the position of its child nodes
    res[pageNode.id] = pageNode.children.map(childNode => ({ pos: childNode.pos }))
  })
  return res
}

/**
 * Parse document builder nodes to create a map of page IDs to line positions.
 *
 * @param {Array} lineNodes - An array of lineNodes to process.
 * @returns {Object} - An object containing all parsed line nodes.
 */
const parseDocBuilderDocumentRootNodes = lineNodes => {
  const res = {}
  lineNodes.forEach(lineNode => {
    // Initialize the array for pageId if not yet defined
    if (res[lineNode.pageId] === undefined) {
      res[lineNode.pageId] = []
    }
    // Push the line position to the corresponding pageId
    res[lineNode.pageId].push({ pos: lineNode.pos })
  })
  return res
}

/**
 * Recursively parse root nodes and handle both 'document' and 'docBuilder' types.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed nodes.
 */
const parseRootNodes = nodes => {
  let rootNodes = {}
  nodes.forEach(node => {
    // Parse based on node type (document or docBuilder)
    if (node.type === 'document') {
      rootNodes[node.id] = parseDocumentRootNodes(node.children)
    } else if (node.type === 'docBuilder') {
      rootNodes[node.id] = parseDocBuilderDocumentRootNodes(node.children)
    }

    // Recursively process any children nodes
    if (node.children && node.children.length > 0) {
      const result = parseRootNodes(node.children)
      rootNodes = { ...rootNodes, ...result }
    }
  })

  return rootNodes
}

/**
 * Wrapper to start parsing root nodes.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed root nodes.
 */
const getRootNodeList = nodes => parseRootNodes(nodes)

/**
 * Parse a table node by extracting rows and their corresponding cell data.
 *
 * @param {Array} tableNode - An array of tableNode to process.
 * @returns {Object} - An object containing all parsed table rows.
 */
const parseTable = tableNode => {
  const tableRows = tableNode.children.filter(node => node.type === 'row')
  const rows = tableRows.map(tablRowNode => {
    const row = {}
    const rowCells = tablRowNode.children.filter(node => node.type === 'cell')
    rowCells.forEach(rowCell => {
      // Only include cells with labels in the row
      if (rowCell.label) {
        row[rowCell.label] = {
          id: rowCell.id,
          v: rowCell.v,
          pageId: rowCell.pageId,
          pos: rowCell.pos,
          STATUS: rowCell.STATUS,
          cellRange: rowCell.cellRange,
          worksheet_name: rowCell.worksheet_name,
          is_profile_key_found: rowCell.is_profile_key_found || false,
          is_label_mapped: rowCell.is_label_mapped || false,
          original_key_label: rowCell.original_key_label || false,
          is_column_mapped_to_key: rowCell.is_column_mapped_to_key || false,
        }
      }
    })
    return row
  })
  return {
    rows,
  }
}

/**
 * Parse all tables in the given nodes, passing the documentId for each table.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @param {String} documentId - An string of documentId to finding or filter.
 * @returns {Array} - An array containing all parsed tables.
 */
const parseTables = (nodes, documentId) => {
  let tables = []
  nodes.forEach(node => {
    if (node.type === 'table') {
      tables.push({
        id: node.id,
        table_unique_id: node.table_unique_id,
        table_name: node.table_name || '',
        table_id: node.table_id || 0,
        documentId,
        ...parseTable(node),
      })
    } else if (node.children && node.children.length > 0) {
      let newDocumentId = documentId
      if (node.type === 'document') {
        newDocumentId = node.id
      }
      const result = parseTables(node.children, newDocumentId)
      tables = tables.concat(result)
    }
  })
  return tables
}

/**
 * Wrapper to start parsing tables.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed nodes.
 */
const getTables = nodes => parseTables(nodes, '')

/**
 * Recursively parse key blocks, collecting position data for 'keyText' nodes.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @param {String} parentDocumentId - An string of parentDocumentId to finding or filter.
 * @returns {Array} - An array containing all parsed keyBlocks.
 */
const parseKeyBlocks = (nodes, parentDocumentId = null) => {
  let keyBlocks = []

  nodes.forEach(node => {
    let documentId = parentDocumentId
    if (node.type === 'document') {
      documentId = node.id
    }

    // Add keyText nodes to the keyBlocks array
    if (node.type === 'keyText') {
      keyBlocks.push({
        documentId,
        pageId: node.pageId,
        pos: node.pos,
      })
    }

    // Recursively process children nodes
    if (node.children && node.children.length > 0) {
      const searchResult = parseKeyBlocks(node.children, documentId)
      keyBlocks = keyBlocks.concat(searchResult)
    }
  })

  return keyBlocks
}

/**
 * Wrapper to start parsing key blocks.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed nodes.
 */
const getKeyBlocks = nodes => parseKeyBlocks(nodes)

/**
 * Recursively parse key nodes, constructing a label-value map.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @param {String} parentLabel - An string of parentLabel to finding or filter.
 * @returns {Array} - An array containing all parsed keys.
 */
const parseKeyNodes = (nodes, parentLabel = null) => {
  let keys = []

  nodes.forEach(node => {
    let label = getNodeLabel(node)
    label = parentLabel ? `${parentLabel}.${label}` : label
    const value = getKeyNodeTitle(node)

    keys.push({
      label,
      value,
      qualifierParent: node.qualifierParent || null,
    })

    // Recursively process children nodes
    if (node.children && node.children.length > 0) {
      const searchResult = parseKeyNodes(node.children, label)
      keys = keys.concat(searchResult)
    }
  })

  return keys
}

/**
 * Parse all keys in the given nodes, passing the parent document ID.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @param {String} parentDocumentId - An string of parentDocumentId to finding or filter.
 * @returns {Array} - An array containing all parsed keys.
 */
const parseKeys = (nodes, parentDocumentId = null) => {
  let keys = []

  nodes.forEach(node => {
    let documentId = parentDocumentId
    if (node.type === 'document') {
      documentId = node.id
    }

    // Parse 'key' nodes and include them in the keys array
    if (node.type === 'key') {
      let parsedKeys = parseKeyNodes(node.children)
      parsedKeys = parsedKeys.map(keyData => ({
        ...keyData,
        documentId,
      }))
      keys = keys.concat(parsedKeys)
    } else if (node.children && node.children.length > 0) {
      const searchResult = parseKeys(node.children, documentId)
      keys = keys.concat(searchResult)
    }
  })

  return keys
}

/**
 * Wrapper to start parsing keys.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed nodes.
 */
const getKeys = nodes => parseKeys(nodes)

/**
 * Wrapper to start parsing documents.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Array} - An array containing all parsed documents.
 */
const parseDocuments = (nodes, parentBatchId = null, parentTransactionId = null) => {
  let documents = []
  nodes.forEach(node => {
    let bId = parentBatchId
    let txId = parentTransactionId

    // Update IDs based on node type
    if (node.type === 'root') {
      txId = node.id
    } else if (node.type === 'batch') {
      bId = node.id
    }

    if (node.type === 'document') {
      if (!bId) {
        const parts = node.id.split('.')
        bId = parts.slice(0, 2).join('.')
      }
      documents.push({
        id: node.id,
        language: node.Language,
        batchId: bId,
        transactionId: txId,
        Vendor: node.Vendor,
        layoutId: node.layout_id,
      })
    }

    if (node.children && node.children.length > 0) {
      const searchResult = parseDocuments(node.children, bId, txId)
      documents = documents.concat(searchResult)
    }
  })
  return documents
}

/**
 * Get Documents structured by transaction and batch.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all Documents organized by transaction and batch.
 */
const getDocuments = nodes => {
  const documents = parseDocuments(nodes)
  const tables = getTables(nodes)
  const keyBlocks = getKeyBlocks(nodes)
  const keys = getKeys(nodes)
  // const vendors = parseVendors(nodes) // Add this line to extract vendors

  // Group by transaction first, then by batch
  const finalDocuments = {}

  documents.forEach(document => {
    const {
      id, language, batchId: docBatchId, transactionId: docTransactionId, Vendor, layoutId,
    } = document
    // Initialize objects if not exists
    if (!finalDocuments[docTransactionId]) {
      finalDocuments[docTransactionId] = {}
    }
    if (!finalDocuments[docTransactionId][docBatchId]) {
      finalDocuments[docTransactionId][docBatchId] = {}
    }

    // Filter data for this specific document
    const documentTables = tables.filter(table => table.documentId === id)
    const documentKeyBlocks = keyBlocks.filter(keyBlock => keyBlock.documentId === id)
    const documentKeys = keys.filter(key => key.documentId === id)
    // Add vendor filtering
    // const documentVendor = vendors.find(v => v.documentId === id && v.batchId === docBatchId)

    // Format the data as before...
    const formatedTables = documentTables.map(table => {
      const {
        documentId, batchId, transactionId, ...newTable
      } = table
      return newTable
    })

    const formatedKeyBlocks = documentKeyBlocks.map(keyBlock => {
      const {
        documentId, batchId, transactionId, ...newKeyBlock
      } = keyBlock
      return newKeyBlock
    })

    const formatedKeys = documentKeys.map(key => {
      const {
        documentId, batchId, transactionId, ...newKey
      } = key
      return newKey
    })

    // Include the vendor in the document data
    finalDocuments[docTransactionId][docBatchId][id] = {
      language,
      tables: formatedTables,
      keyBlocks: formatedKeyBlocks,
      keys: formatedKeys,
      vendor: Vendor || null, // Add vendor information
      layoutId,
    }
  })

  return finalDocuments
}

const getVerificationDocuments = nodes => {
  const documents = parseDocuments(nodes)
  const tables = getTables(nodes)
  const keyBlocks = getKeyBlocks(nodes)
  const keys = getKeys(nodes)
  // const vendors = parseVendors(nodes)

  const finalDocuments = {}

  documents.forEach(document => {
    const {
      id, language, batchId, Vendor,
    } = document

    if (!finalDocuments[batchId]) {
      finalDocuments[batchId] = {}
    }

    const documentTables = tables.filter(table => table.documentId === id)
    const documentKeyBlocks = keyBlocks.filter(keyBlock => keyBlock.documentId === id)
    const documentKeys = keys.filter(key => key.documentId === id)
    // const documentVendor = vendors.find(v => v.documentId === id && v.batchId === batchId)

    finalDocuments[batchId][id] = {
      language,
      tables: documentTables.map(({
        documentId, batchId: _b1, transactionId, ...t
      }) => t),
      keyBlocks: documentKeyBlocks.map(({
        documentId, batchId: _b2, transactionId, ...k
      }) => k),
      keys: documentKeys.map(({
        documentId, batchId: _b3, transactionId, ...k
      }) => k),
      vendor: Vendor || null,
    }
  })

  return finalDocuments
}

/**
 * Get Excel Data.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing a parsed data.
 */
const getExcelData = nodes => {
  const documentNode = nodes[0]
  return {
    fileName: `${documentNode.sourceFileName}${documentNode.ext}`,
  }
}

/**
 * Modified the URL to get the Tiff file or get batch media URL.
 *
 * @param {String} batchId - An string of batchId to naming folder.
 * @param {String} subPath - An string of subPath to add subpath with URL.
 * @param {String} fileName - An string of fileName to fulfil the url.
 * @returns {String} - An string containing the URL.
 */
const getBatchMediaURL = (batchId, subPath, fileName, isDatasetBatch = false) => {
  let url = `${getEnv('VUE_APP_BACKEND_URL')}/batch-media`
  const isUploadedTraining = batchId.toUpperCase().includes('.U')

  if (isDatasetBatch && !isUploadedTraining) {
    url = `${getEnv('VUE_APP_BACKEND_URL')}/dataset-batch-media`
  }

  if (isDatasetBatch) {
    url = `${getEnv('VUE_APP_BACKEND_URL')}/dataset-batch-media/batches`
  }

  if (subPath && subPath !== '') {
    url += `/${subPath}`
  }

  const folderName = batchId
  url += `/${folderName}/${fileName}`
  return url
}

/**
 * Get classification media URL by filePath.
 *
 * @param {Array} nodes - An array of nodes to process.
 * @returns {Object} - An object containing all parsed nodes.
 */
const getClassificationMediaURL = filePath => {
  const url = `${getEnv('VUE_APP_BACKEND_URL')}/batch-media/${filePath}`
  return url
}

/**
 * Get all keys in the given keyItems, passing the parent key item ID.
 *
 * @param {Array} keyItems - An array of keyItems to process.
 * @param {String} keyItemId - An string of keyItemId to finding or filter.
 * @returns {Array} - An array containing all key items.
 */
const getKeyItemById = (keyItems, keyItemId) => {
  let allKeyItems = []
  keyItems.forEach(keyItem => {
    allKeyItems.push(keyItem)
    allKeyItems = allKeyItems.concat(keyItem.compoundItems)
  })
  return allKeyItems.find(keyItemToCheck => keyItemToCheck.id === keyItemId)
}

/**
 * Split an ID into its component parts: transaction, batch, document, key, etc.
 *
 * @param {String} cellId - A string of cellId to process.
 * @returns {Object} - An object containing all split IDs.
 */
const idSplltier = cellId => {
  const splitedId = cellId.split('.')

  // Handle transaction-based IDs (with prefix like 'T')
  let transactionId; let batchId; let documentId; let keyId; let keyItemId; let
    keyItemChildId

  if (splitedId[0].startsWith('T')) {
    // Transaction-based ID format
    transactionId = `${splitedId[0]}.${splitedId[1]}`
    batchId = `${splitedId[2]}.${splitedId[3]}`
    documentId = `${batchId}.${splitedId[4]}`
    keyId = `${documentId}.${splitedId[5]}`
    keyItemId = `${keyId}.${splitedId[6]}`
    keyItemChildId = splitedId.length === 8 ? `${keyItemId}.${splitedId[7]}` : null
  } else {
    // Legacy ID format without transaction
    transactionId = null
    batchId = `${splitedId[0]}.${splitedId[1]}`
    documentId = `${batchId}.${splitedId[2]}`
    keyId = `${documentId}.${splitedId[3]}`
    keyItemId = `${keyId}.${splitedId[4]}`
    keyItemChildId = splitedId.length === 6 ? `${keyItemId}.${splitedId[5]}` : null
  }

  return {
    transactionId,
    batchId,
    documentId,
    keyId,
    keyItemId,
    keyItemChildId,
  }
}

/**
 * Create a transaction hierarchy from flat data.
 *
 * @param {Object} data - Transaction data with batches.
 * @returns {Array} - An array of transaction nodes with batch children.
 */
// In helper.js, update the createTransactionHierarchy function:

const createTransactionHierarchy = data => {
  if (!data || !data.batches || !Array.isArray(data.batches)) {
    return []
  }

  // Create transaction node
  const transactionNode = {
    type: 'root',
    id: data.transaction_id,
    profile: data.profile,
    children: [],
  }

  // Add batch nodes as children
  data.batches.forEach(batch => {
    // Get vendor directly from batch
    const vendorName = batch.vendor || ''

    // Create batch node
    const batchNode = {
      type: 'batch',
      id: batch.id,
      profile: batch.profile,
      subPath: batch.sub_path,
      vendor: vendorName, // Store vendor at batch level
      document_types: batch.document_types || '',
      children: [],
    }

    // Add nodes to batch
    if (batch.data_json && batch.data_json.nodes) {
      // Attach vendor info to document nodes for easier access in flatNodes
      batchNode.children = batch.data_json.nodes.map(node => {
        if (node.type === 'document') {
          return {
            ...node,
            batchId: batch.id,
            vendor: { vendor: vendorName },
          }
        }
        return node
      })
    }

    transactionNode.children.push(batchNode)
  })

  return [transactionNode]
}

const toCamelCase = str => {
  if (!str) return ''
  const camel = str
    .replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) => (index === 0 ? word.toLowerCase() : word.toUpperCase()))
    .replace(/\s+/g, '')
  return camel.charAt(0).toLowerCase() + camel.slice(1)
}

const toNormalCase = str => {
  if (!str) return ''
  if (str.includes(' ')) return str // Already normal case
  return str
    .replace(/([A-Z])/g, ' $1') // insert space before capital letters
    .replace(/^./, s => s.toUpperCase()) // capitalize first character
    .trim()
}

export {
  searchNodes, expandNodesByType, getNodes, getFlatNodes, getRootNodeList, getWordNodes, getDocuments, getPages, parsePage, getExcelData, getBatchMediaURL, getClassificationMediaURL, getKeyItemById, idSplltier, createTransactionHierarchy, toNormalCase, toCamelCase, getVerificationDocuments,
}
