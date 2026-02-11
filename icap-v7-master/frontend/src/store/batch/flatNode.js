// Get the children of a node, considering possible property names.
const getNodeChildren = node => node.children || []

// Get the label of a node, considering possible property names.
const getNodeLabel = node => node.label || node.key || ''

// Get the value of a node, considering possible property names.
const getNodeValue = node => node.v || node.value || ''

// Determine whether the label key is 'label' or 'key'.
const getNodeLabelKey = node => (node.label ? 'label' : 'key')

// Generate a title for a node based on its type and index.
// Parameters:
// - node: The node object.
// - nodeIndex: Index of the node.
// Returns:
// - A string representing the node's title.
const getKeyNodeTitle = (node, nodeIndex) => {
  let title

  if (node.type === 'root') {
    title = node.id // Use the ID for root nodes.
  } else if (node.type === 'batch') {
    title = `${node.id}`
    // Combine ID and document type.
  } else if (node.type === 'document') {
    // Get document type from either DocType or DocumentType field
    const docType = node.DocType || (node.data_json && node.data_json.DocumentType) || ''
    title = docType ? `${node.id} - ${docType}` : node.id
  } else if (['key_detail', 'key_detail_robot', 'key_detail_static'].includes(node.type)) {
    // For specific key detail types, check for a child node with the label 'name'.
    const childNameNode = node.children?.find(e => e[getNodeLabelKey(e)] === 'name')
    title = childNameNode ? getNodeValue(childNameNode) : getNodeValue(node)
  } else if (['keyTextDetail', 'keyTextDetailRobot', 'keyTextDetailStatic'].includes(node.type)) {
    // Use the node's value for text detail types.
    title = getNodeValue(node)
  } else {
    // Default title for other types.
    title = `${node.type.charAt(0).toUpperCase() + node.type.slice(1)} - ${nodeIndex}`
  }

  return title
}

// Generate data for adding a node to the database.
// Parameters:
// - node: The node object.
// - nestedLabel: Label for grouping database entries.
// Returns:
// - An object containing the record and table name for the database.
const getAddToDBData = (node, nestedLabel) => {
  const nodeDetails = {}
  getNodeChildren(node).forEach(childNode => {
    const childNodeLabel = getNodeLabel(childNode) // Get the label for the child node.
    const childNodeValue = getKeyNodeTitle(childNode) // Get the title for the child node.
    nodeDetails[childNodeLabel] = childNodeValue // Map label to value.
  })

  const record = {}
  const tablePrefix = nestedLabel.toUpperCase() // Prefix for table fields.
  const tableName = `${tablePrefix}_MASTER` // Table name based on the label.
  const fields = ['name', 'addressLine1', 'addressLine2', 'city'] // Predefined fields.

  // Map node details to database fields.
  fields.forEach(field => {
    const key = `${tablePrefix}${field.toUpperCase()}`
    if (nodeDetails[field]) {
      record[key] = nodeDetails[field]
    }
  })

  return {
    record,
    tableName,
  }
}

// Generate configuration data for a node.
// Parameters:
// - node: The node object.
// - nestedLabel: Label for configuration grouping.
// - addressBlockKeys: Array of labels that support adding to the database.
// Returns:
// - An object containing configuration options and optionally database data.
const getNodeConfigData = (node, nestedLabel, addressBlockKeys) => {
  let options = []
  let addToDBData = null

  // If no nested label is provided, return default configuration.
  if (!nestedLabel) {
    return { options }
  }

  options = options.concat(['rules', 'notInUse']) // Default options.

  // Determine if lookup option should be enabled.
  const enableLookup = node.qualifierParent !== 'references' && getNodeChildren(node).length === 0
  if (enableLookup) {
    options.push('lookup')
  }

  // Determine if add-to-database option should be enabled.
  const enableAddToDB = addressBlockKeys.includes(nestedLabel)

  if (enableAddToDB) {
    options.push('addToDB')
    addToDBData = getAddToDBData(node, nestedLabel) // Generate database data.
  }

  const result = {
    options,
  }

  // Include database data if applicable.
  if (addToDBData) {
    result.addToDBData = addToDBData
  }

  return result
}

/**
 * Parse vendors from nodes structure.
 *
 * @param {Array} nodes - The nodes to extract vendors from.
 * @param {String} parentDocumentId - Parent document ID for context.
 * @param {String} batchDocumentType - Parent document ID for context.
 * @returns {Array} - Array of vendor objects with document association.
 */
const parseVendors = (nodes, parentDocumentId = null, parentBatchId = null) => {
  let vendors = []
  nodes.forEach(node => {
    let documentId = parentDocumentId
    let batchId = parentBatchId
    let documentType = null // Declare documentType properly

    // Update IDs based on node type
    if (node.type === 'document') {
      documentId = node.id
    } else if (node.type === 'batch') {
      batchId = node.id
      documentType = node.document_types || (node.data_json && node.data_json.DocumentType) || ''
    }

    // Extract vendor information if available
    if (node.type === 'vendor') {
      vendors.push({
        documentId,
        batchId,
        documentType, // Add documentType to vendor object if needed
        vendor: node.value || node.v || '',
        page_id: node.pageId || '',
        vendor_position: node.position || node.pos || '',
        is_profile_key_found: node.is_profile_key_found !== false,
      })
    }

    // Process children recursively
    if (node.children && node.children.length > 0) {
      const childVendors = parseVendors(node.children, documentId, batchId)
      vendors = vendors.concat(childVendors)
    }
  })

  return vendors
}

// Helper function to collect all keys except table keys
const collectAllKeysExceptTables = (node, isInsideTable = false) => {
  if (!node) return []

  let allKeys = []

  // Check if we're entering a table structure
  const currentlyInsideTable = isInsideTable
    || node.type === 'table'
    || node.type === 'row'
    || node.type === 'cell'
    || node.type === 'tableHeader'
    || node.type === 'tableBody'
    || node.type === 'tableFooter'

  // Only collect keys if we're NOT inside a table
  if (!currentlyInsideTable) {
    const currentKey = node?.label || node?.key || ''
    if (currentKey && currentKey.trim() !== '') {
      allKeys.push(currentKey)
    }
  }

  // Recursively collect from children, passing the table context
  if (node?.children && Array.isArray(node.children)) {
    node.children.forEach(child => {
      const childKeys = collectAllKeysExceptTables(child, currentlyInsideTable)
      allKeys = allKeys.concat(childKeys)
    })
  }

  return allKeys
}

// Helper function to recursively collect categorizable nodes from within 'key' type nodes only
const collectCategorizableNodesFromKeys = nodes => {
  const categorizableNodes = []
  const categorizableNodeTypes = [
    'key_detail',
    'keyTextDetail',
    'key_detail_robot',
    'keyTextDetailRobot',
    'key_detail_static',
    'keyTextDetailStatic',
  ]

  const searchInNode = (node, parentIds = new Set()) => {
    // If this is a categorizable node type
    if (categorizableNodeTypes.includes(node.type)) {
      // Only add if none of its parents are already categorizable
      if (parentIds.size === 0) {
        categorizableNodes.push(node)

        // Don't search children if this node is categorizable
        // This prevents children from being collected separately
        return
      }
    }

    // Recursively search in children, tracking this node as a parent
    if (node.children && Array.isArray(node.children)) {
      const newParentIds = new Set(parentIds)
      if (categorizableNodeTypes.includes(node.type)) {
        newParentIds.add(node.id)
      }

      node.children.forEach(child => searchInNode(child, newParentIds))
    }
  }

  // Only search within 'key' type nodes
  nodes.forEach(node => {
    if (node.type === 'key') {
      searchInNode(node)
    }
  })

  return categorizableNodes
}

// Helper function to filter nodes for Auto Extraction Keys
// These are nodes that get 'primary' badge (purple) - exactly one flag is true
const filterAutoExtractionNodes = documentChildren => {
  // First, collect only the categorizable nodes from within 'key' type nodes
  const categorizableNodes = collectCategorizableNodesFromKeys(documentChildren)

  return categorizableNodes.filter(node => {
    // Skip nodes with special status
    // if (node.STATUS === -1000) {
    //   return false
    // }

    const isPureAutoextraction = node.is_pure_autoextraction === true
    const isProfileKeyFound = node.is_profile_key_found === true

    // Skip green nodes (both flags true) - these remain as siblings to vendor
    if (isProfileKeyFound && isPureAutoextraction) {
      return false
    }

    // Auto Extraction Keys: exactly one flag is true (gets 'primary' badge)
    // This means: (!isProfileKeyFound && isPureAutoextraction)
    return (!isProfileKeyFound && isPureAutoextraction)
  })
}

// Helper function to filter nodes for Process Keys
// These are nodes that get '' badge (grey) - both flags are false ONLY
const filterProcessKeyNodes = documentChildren => {
  // First, collect only the categorizable nodes from within 'key' type nodes
  const categorizableNodes = collectCategorizableNodesFromKeys(documentChildren)

  return categorizableNodes.filter(node => {
    // Skip nodes with special status
    // if (node.STATUS === -1000) {
    //   return false
    // }

    const isPureAutoextraction = node.is_pure_autoextraction === true
    const isProfileKeyFound = node.is_profile_key_found === true

    // Skip green nodes (both flags true) - these remain as siblings to vendor
    if (isProfileKeyFound && isPureAutoextraction) {
      return false
    }

    // Process Keys: ONLY nodes with both flags false (gets '' badge - grey)
    return !isProfileKeyFound && !isPureAutoextraction
  })
}

// Helper function to remove grouped nodes from the original hierarchy
const removeGroupedNodesFromHierarchy = (documentChildren, groupedNodeIds) => {
  const removeFromNode = node => {
    // Create a copy to avoid mutating original
    const nodeCopy = { ...node }

    if (nodeCopy.children) {
      // Filter out grouped nodes from children and recursively clean remaining children
      nodeCopy.children = nodeCopy.children
        .filter(child => !groupedNodeIds.has(child.id))
        .map(child => removeFromNode(child))
    }

    return nodeCopy
  }

  return documentChildren.map(node => removeFromNode(node))
}

/**
 * Flattens a hierarchical node structure into an array with proper parent-child relationships
 *
 * @param {Array} nodes - The nodes to flatten
 * @param {Array} expandedNodes - Array of node IDs that are currently expanded
 * @param {Array} matchedNodes - Array of node IDs that match search criteria
 * @param {Object} selectedNode - Currently selected node
 * @param {Boolean} highlightRootNodes - Whether to highlight root nodes
 * @param {Array} addressBlockKeys - Keys that support DB operations
 * @param {Number} depth - Current depth in hierarchy (default: 0)
 * @param {String} parentNestedLabel - Label from parent node (default: null)
 * @param {String} parentKeyId - Key ID from parent node (default: null)
 * @param {String} transactionId - Current transaction ID (default: null)
 * @param {String} parentNodeId - Parent node ID (default: null)
 * @param {Boolean} draggable - Whether node is draggable (default: false)
 * @param {Boolean} draggableTarget - Whether node is draggable target (default: false)
 * @param {String} documentId - Current document ID (default: null)
 * @param {String} batchId - Current batch ID (default: null)
 * @returns {Array} - Flattened array of nodes
 */
const flatNodes = (nodes, expandedNodes, matchedNodes, selectedNode, highlightRootNodes, addressBlockKeys, depth = 0, parentNestedLabel = null, parentKeyId = null, transactionId = null, parentNodeId = null, draggable = false, draggableTarget = false, documentId = null, batchId = null, documentSortOrder = 'asc') => {
  let flatenNodes = [] // Array to hold the flattened nodes

  // Define allowed node types to process
  const allowedNodeTypes = ['root', 'batch', 'document', 'vendor', 'key', 'key_detail', 'keyTextDetail', 'key_detail_robot', 'keyTextDetailRobot', 'key_detail_static', 'keyTextDetailStatic']

  // Dynamically determine expandable node types by checking which nodes actually have children
  const getExpandableNodeTypes = nodesToCheck => {
    const expandableTypes = new Set()

    const checkNodeRecursively = nodeList => {
      nodeList.forEach(node => {
        // Check if this node has children of allowed types
        if (node.children && node.children.length > 0) {
          const hasAllowedChildren = node.children.some(child => allowedNodeTypes.includes(child.type))
          if (hasAllowedChildren) {
            expandableTypes.add(node.type)
          }
          // Recursively check children
          checkNodeRecursively(node.children)
        }
      })
    }

    checkNodeRecursively(nodesToCheck)
    return Array.from(expandableTypes)
  }

  // Get expandable node types dynamically (only calculate once at the top level)
  const expandableNodeTypes = depth === 0 ? getExpandableNodeTypes(nodes) : []

  // Reorder ONLY document nodes while keeping non-document nodes in-place.
  // This makes the effect visible even when documents are interleaved with other node types.
  const docKey = id => {
    // Expect formats like MYYYYMMDD.USNNNNNN, fallback to string
    const m = String(id).match(/^M(\d{8})\.US(\d{1,})/i)
    if (!m) return { raw: String(id), date: 0, seq: 0 }
    return { raw: String(id), date: Number(m[1]), seq: Number(m[2]) }
  }

  const sortByNaturalId = arr => [...arr].sort((a, b) => {
    const ak = docKey(a.id)
    const bk = docKey(b.id)
    if (ak.date !== bk.date) return documentSortOrder === 'desc' ? bk.date - ak.date : ak.date - bk.date
    if (ak.seq !== bk.seq) return documentSortOrder === 'desc' ? bk.seq - ak.seq : ak.seq - bk.seq
    const s = ak.raw.localeCompare(bk.raw)
    return documentSortOrder === 'desc' ? -s : s
  })

  const documentNodes = nodes.filter(n => n.type === 'document')
  const batchNodes = nodes.filter(n => n.type === 'batch')
  const sortedDocuments = sortByNaturalId(documentNodes)
  const sortedBatches = sortByNaturalId(batchNodes)
  // Rebuild the nodes array: for each original element, if it's a document, pull next from sortedDocuments
  const nodesSortedForDisplay = nodes.map(n => {
    if (n.type === 'document') {
      return sortedDocuments.shift() || n
    }
    if (n.type === 'batch') {
      return sortedBatches.shift() || n
    }
    return n
  })

  // Map to track occurrences of node types for indexing
  const counts = {}
  const nodeIndexes = nodesSortedForDisplay.map(item => {
    const nodeType = item.type
    if (counts[nodeType] === undefined) {
      counts[nodeType] = 0
    } else {
      counts[nodeType] += 1
    }

    return counts[nodeType]
  })

  // First collect all key labels for documents (collect from ANY node with label/key)
  const documentKeyLabels = {}

  // First pass: collect all key labels for each document (respecting display order)
  for (let index = 0; index < nodesSortedForDisplay.length; index += 1) {
    const node = nodesSortedForDisplay[index]

    if (node?.type === 'document') {
      // Use function that excludes table keys but includes all other nested keys
      const allKeys = collectAllKeysExceptTables(node)
      // Remove duplicates and filter empty
      documentKeyLabels[node.id] = [...new Set(allKeys)].filter(key => key && key.trim() !== '')
    }
  }

  // Iterate over the sorted nodes for display
  for (let index = 0; index < nodesSortedForDisplay.length; index += 1) {
    const node = nodesSortedForDisplay[index]

    // Skip nodes that are not in the allowed types
    if (!allowedNodeTypes.includes(node.type)) {
      // eslint-disable-next-line no-continue
      continue
    }

    // If the node is of type 'key', recursively flatten its children
    if (node.type === 'key') {
      const searchResult = flatNodes(node.children, expandedNodes, matchedNodes, selectedNode, highlightRootNodes, addressBlockKeys, depth, parentNestedLabel, parentKeyId, transactionId, node.id, false, false, documentId, batchId, documentSortOrder)
      flatenNodes = flatenNodes.concat(searchResult)
    } else {
      // Determine if the node is expandable based on:
      // 1. Whether its type is in the dynamically determined expandable types, OR
      // 2. Whether it actually has children of allowed types (fallback check)
      const hasAllowedChildren = !!(node.children && node.children.filter(childNode => allowedNodeTypes.includes(childNode.type)).length > 0)
      const expandable = (depth === 0 && expandableNodeTypes.includes(node.type)) || hasAllowedChildren

      const expanded = expandable && expandedNodes.includes(node.id)
      const nodeIndex = nodeIndexes[index]

      // Generate the node's label and title
      const label = getNodeLabel(node)
      const title = getKeyNodeTitle(node, nodeIndex)

      // Track transaction ID for hierarchy
      let currentTransactionId = transactionId
      if (node.type === 'root') {
        currentTransactionId = node.id
      }

      // Track batch ID for vendor nodes (original logic for backward compatibility)
      let currentBatchId = null
      if (node.type === 'batch') {
        currentBatchId = node.id
      }

      // Track inherited batch ID for all child nodes
      let inheritedBatchId = batchId
      if (node.type === 'batch') {
        inheritedBatchId = node.id
      }

      // Track document ID for hierarchy
      let currentDocumentId = documentId
      if (node.type === 'document') {
        currentDocumentId = node.id
      }

      // Determine badge variant based on node status
      const nodeStatus = node.STATUS || 0
      let badgeVariant = ''
      if (nodeStatus === 0) {
        badgeVariant = 'info'
      } else if (nodeStatus === -2) {
        badgeVariant = 'danger'
      } else if (nodeStatus === -1) {
        badgeVariant = 'warning'
      } else if (nodeStatus === 1) {
        badgeVariant = 'success'
      } else if (nodeStatus === 2) {
        badgeVariant = 'secondary'
      } else if (nodeStatus === 200) {
        badgeVariant = 'dark'
      } else if (nodeStatus === 111) {
        badgeVariant = 'primary'
      }

      // Determine if the node is highlighted or matches a search query
      const highlighted = !!(selectedNode && selectedNode.highlight && !highlightRootNodes && selectedNode.id === node.id)
      const searchMatch = matchedNodes.includes(node.id)

      // Create a nested label if applicable
      let nestedLabel = null
      if (label) {
        if (parentNestedLabel) {
          nestedLabel = `${parentNestedLabel}.${label}`
        } else {
          nestedLabel = label
        }
      }

      // Retrieve additional configuration data for the node
      const configData = getNodeConfigData(node, nestedLabel, addressBlockKeys)
      const keyId = node.unique_id || parentKeyId || null

      // Create the node object with basic properties
      const flatNode = {
        id: node.id,
        title,
        draggable,
        draggableTarget,
        expandable,
        expanded,
        test: node.test,
        depth,
        highlighted,
        searchMatch,
        type: node.type,
        label,
        badgeVariant,
        nestedLabel,
        keyId,
        configData,
        transactionId: currentTransactionId,
        batchId: currentBatchId || node.batchId || null,
        currentBatchId: inheritedBatchId,
        documentId: currentDocumentId,
        isProfileKeyFound: node.type === 'vendor' ? true : node.is_profile_key_found,
        parentNodeId, // Add parentNodeId to track parent-child relationships
        nodeId: node.id, // Add nodeId for hierarchical visibility logic
        isAutoExtracted: node.is_auto_extracted,
        isLabelMapped: node.is_label_mapped,
        isKeyFromTable: node.is_key_from_table,
        OriginalKeyLabel: node.original_key_label,
        qualifierParent: node.qualifier_parent,
        isDataExceptionDone: node.is_data_exception_done,
        isPureAutoextraction: node.is_pure_autoextraction,
        isAddressBlockPartial: node.is_address_block_partial || false,
        Status: node.STATUS || 0,
        notInUse: node.notInUse || false,
      }

      // Add documentType flag for batch nodes
      if (node.type === 'batch') {
        // Extract document type from batch node
        // Based on your structure: batch.document_types or batch.data_json.DocumentType
        flatNode.documentType = node.document_types
                                || (node.data_json && node.data_json.DocumentType) || ''
      }

      // Add vendorName flag for document nodes
      if (node.type === 'document') {
        // Extract vendor name from document node
        // Based on your structure: document.Vendor
        flatNode.vendorName = node.Vendor || ''
      }

      // For vendor nodes, add value, pageId, and position
      if (node.type === 'vendor') {
        flatNode.value = node.value || node.v || ''
        flatNode.pageId = node.pageId || ''
        flatNode.position = node.position || node.pos || ''
      }

      // Add allKeys property for document nodes using collected keys
      if (node.type === 'document') {
        flatNode.allKeys = documentKeyLabels[node.id] || []
      }

      // Add the node to the flattened array
      flatenNodes.push(flatNode)

      // Process children if the node is expanded
      if (expanded) {
        // Special processing for document nodes to create grouped structure
        if (node.type === 'document') {
          // 1. Create vendor node
          let vendorName = node.Vendor || ''
          const vendorPageId = node.vendor?.page_id || ''
          const vendorPosition = node.vendor?.vendor_position || ''
          let vendorProfileFound = node.vendor?.is_profile_key_found !== false

          if (!vendorName) {
            vendorName = ''
            vendorProfileFound = false
          }

          // Create vendor node for documents
          const vendorNodeId = `${node.id}_vendor`
          const vendorNode = {
            id: vendorNodeId,
            title: vendorName,
            draggable: false,
            draggableTarget: false,
            expandable: false,
            expanded: false,
            depth: depth + 1,
            highlighted: false,
            searchMatch: false,
            type: 'vendor',
            label: 'Document Issuer',
            badgeVariant: vendorProfileFound ? 'success' : 'warning',
            nestedLabel: 'vendor',
            keyId: null,
            configData: { options: ['rules', 'notInUse'] },
            transactionId: currentTransactionId,
            batchId: currentBatchId || node.batchId || null,
            currentBatchId: inheritedBatchId,
            documentId: currentDocumentId,
            value: vendorName,
            pageId: vendorPageId,
            position: vendorPosition,
            isProfileKeyFound: vendorProfileFound,
            parentNodeId: node.id,
            nodeId: vendorNodeId,
          }
          flatenNodes.push(vendorNode)

          // 2. Get nodes that will be grouped
          const autoExtractionChildren = filterAutoExtractionNodes(node.children || [])
          // .sort((a, b) => a.label.localeCompare(b.label)) // Sort auto-extraction nodes by label

          const processKeyChildren = filterProcessKeyNodes(node.children || [])
            .sort((a, b) => a.label.localeCompare(b.label)) // Sort process-key nodes by label

          // Create a set of IDs for nodes that will be grouped
          const groupedNodeIds = new Set([
            ...autoExtractionChildren.map(n => n.id),
            ...processKeyChildren.map(n => n.id),
          ])

          // Helper function to recursively sort key children
          // const sortKeyChildren = item => {
          //   if ((item.type === 'key' || item.type === 'key_detail') && item.children?.length) {
          //     return {
          //       ...item,
          //       children: [...item.children]
          //         .sort((a, b) => a.label.localeCompare(b.label))
          //         .map(sortKeyChildren), // Recursively sort nested children
          //     }
          //   }
          //   return item
          // }

          // 3. Process all remaining nodes first (including green, red, tables, etc.)
          // Remove the grouped nodes from the hierarchy and process the rest normally
          // Apply sorting to cleanedChildren
          const cleanedChildren = removeGroupedNodesFromHierarchy(node.children || [], groupedNodeIds)

          if (cleanedChildren.length > 0) {
            const remainingFlattened = flatNodes(
              cleanedChildren,
              expandedNodes,
              matchedNodes,
              selectedNode,
              highlightRootNodes,
              addressBlockKeys,
              depth + 1,
              nestedLabel,
              keyId,
              currentTransactionId,
              node.id,
              false,
              false,
              currentDocumentId,
              inheritedBatchId,
              documentSortOrder,
            )
            flatenNodes = flatenNodes.concat(remainingFlattened)
          }

          // 4. Create Auto Extraction Keys group (only if has children) - positioned after individual nodes
          if (autoExtractionChildren.length > 0) {
            const autoExtractionNodeId = `${node.id}.auto_extraction`
            const autoExtractionParentNode = {
              id: autoExtractionNodeId,
              title: 'Auto Extraction Keys',
              draggable: false,
              draggableTarget: false,
              expandable: true,
              expanded: expandedNodes.includes(autoExtractionNodeId),
              depth: depth + 1,
              highlighted: false,
              searchMatch: false,
              type: 'auto_extraction_parent',
              label: 'Auto Extraction Keys',
              badgeVariant: 'primary',
              nestedLabel: nestedLabel ? `${nestedLabel}.auto_extraction_keys` : 'auto_extraction_keys',
              keyId: null,
              configData: { options: ['hideEmptyAutoExtrationKeys'] },
              transactionId: currentTransactionId,
              batchId: currentBatchId || node.batchId || null,
              currentBatchId: inheritedBatchId,
              documentId: currentDocumentId,
              isProfileKeyFound: false,
              isAddressBlockPartial: node.is_address_block_partial || false,
              isPureAutoextraction: true,
              parentNodeId: node.id,
              nodeId: autoExtractionNodeId,
            }
            flatenNodes.push(autoExtractionParentNode)

            // Add children if expanded
            if (autoExtractionParentNode.expanded) {
              const autoExtractionFlattened = flatNodes(
                autoExtractionChildren,
                expandedNodes,
                matchedNodes,
                selectedNode,
                highlightRootNodes,
                addressBlockKeys,
                depth + 2,
                autoExtractionParentNode.nestedLabel,
                keyId,
                currentTransactionId,
                autoExtractionNodeId,
                true,
                false,
                currentDocumentId,
                inheritedBatchId,
                documentSortOrder,
              )
              flatenNodes = flatenNodes.concat(autoExtractionFlattened)
            }
          }

          // 5. Create Process Keys group (only if has children) - positioned last
          if (processKeyChildren.length > 0) {
            const processKeysNodeId = `${node.id}.process_keys`
            const processKeysParentNode = {
              id: processKeysNodeId,
              title: 'Process Keys',
              draggable: false,
              draggableTarget: false,
              expandable: true,
              expanded: expandedNodes.includes(processKeysNodeId),
              depth: depth + 1,
              highlighted: false,
              searchMatch: false,
              type: 'process_keys_parent',
              label: 'Process Keys',
              badgeVariant: 'secondary',
              nestedLabel: nestedLabel ? `${nestedLabel}.process_keys` : 'process_keys',
              keyId: null,
              configData: { options: [] },
              transactionId: currentTransactionId,
              batchId: currentBatchId || node.batchId || null,
              currentBatchId: inheritedBatchId,
              documentId: currentDocumentId,
              isAddressBlockPartial: node.is_address_block_partial || false,
              isProfileKeyFound: false,
              parentNodeId: node.id,
              nodeId: processKeysNodeId,
            }
            flatenNodes.push(processKeysParentNode)

            // Add children if expanded
            if (processKeysParentNode.expanded) {
              const processKeysFlattened = flatNodes(
                processKeyChildren,
                expandedNodes,
                matchedNodes,
                selectedNode,
                highlightRootNodes,
                addressBlockKeys,
                depth + 2,
                processKeysParentNode.nestedLabel,
                keyId,
                currentTransactionId,
                processKeysNodeId,
                false,
                true,
                currentDocumentId,
                inheritedBatchId,
                documentSortOrder,
              )
              flatenNodes = flatenNodes.concat(processKeysFlattened)
            }
          }
        } else {
          // For non-document nodes, process children normally
          const searchResult = flatNodes(
            node.children || [],
            expandedNodes,
            matchedNodes,
            selectedNode,
            highlightRootNodes,
            addressBlockKeys,
            depth + 1,
            nestedLabel,
            keyId,
            currentTransactionId,
            node.id,
            false,
            false,
            currentDocumentId,
            inheritedBatchId,
            documentSortOrder,
          )
          flatenNodes = flatenNodes.concat(searchResult)
        }
      }
    }
  }
  return flatenNodes
}

export {
  parseVendors,
  flatNodes,
  getNodeChildren,
  getKeyNodeTitle,
  getNodeLabel,
}
