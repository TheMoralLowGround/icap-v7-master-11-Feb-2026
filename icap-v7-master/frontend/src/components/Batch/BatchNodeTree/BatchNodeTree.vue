<!--
 Organization: AIDocbuilder Inc.
 File: BatchNodeTree.vue
 Version: 6.1

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization
   - Updated for new grouped node structure

 Last Updated By: Updated for grouped nodes
 Last Updated At: 2024-12-02

 Description:
   - A Vue component that renders a tree of batch nodes with dynamic expansion and collapse functionality.
   - Updated to support new grouped node structure with Auto Extraction Keys and Process Keys parent nodes.
   - The component uses a virtual scroller for efficient rendering of a large number of nodes.
   - It handles the display of various node types and supports expanding and collapsing nodes.
   - Includes functionality for expanding or collapsing all nodes based on eligibility.

 Features:
   - Renders a flat list of nodes from Vuex store.
   - Supports dynamic styling of nodes based on their depth in the tree.
   - Integrates `BatchNode` component to handle individual node rendering.
   - Provides methods to expand or collapse all nodes of a certain type (e.g., non-root nodes or document nodes).
   - Handles new grouped node types: auto_extraction_parent and process_keys_parent

 Dependencies:
   - vue-virtual-scroller - For efficient rendering of large lists.
   - Vuex - For state management and accessing the list of nodes.
-->

<template>
  <!-- Main container for a node, styled with scroller classes -->
  <div class="scroller-container">
    <div
      v-if="!isProfileLoading"
      class="scroller"
    >
      <!-- Render all nodes, but handle grouped parents differently -->
      <div
        v-for="node in visibleNodes"
        :key="node.id"
      >
        <!-- Regular nodes that are NOT children of grouped parents -->
        <template v-if="!isChildOfGroupedParent(node)">
          <div :style="{ 'margin-left': (node.depth * 25) + 'px' }">
            <BatchNode
              :id="node.id"
              :label="node.label"
              :title="node.title"
              :expandable="node.expandable"
              :expanded="node.expanded"
              :test="node.test"
              :highlighted="node.highlighted"
              :is-profile-key-found="node.isProfileKeyFound"
              :search-match="node.searchMatch"
              :type="node.type"
              :badge-variant="node.badgeVariant"
              :nested-label="node.nestedLabel"
              :key-id="node.keyId"
              :config-data="node.configData"
              :collapse-all-eligibility="collapseAllEligibility"
              :expand-all-eligibility="expandAllEligibility"
              :node-item="node"
              @to-collapse-all="toCollapseAll"
              @to-expand-all="toExpandAll"
            />
            <!-- Below is the flage for accuracy badge  -->
            <!-- :transaction-node-tree="batchDocumentNodes" -->
          </div>
        </template>

        <!-- Grouped parent nodes with their paginated children -->
        <template v-if="groupedParentTypes.includes(node.type) && node.expanded">
          <!-- Always show the parent node -->
          <div :style="{ 'margin-left': (node.depth * 25) + 'px' }">
            <BatchNode
              :id="node.id"
              :label="node.label"
              :title="node.title"
              :expandable="node.expandable"
              :expanded="node.expanded"
              :test="node.test"
              :highlighted="node.highlighted"
              :is-profile-key-found="node.isProfileKeyFound"
              :search-match="node.searchMatch"
              :type="node.type"
              :badge-variant="node.badgeVariant"
              :nested-label="node.nestedLabel"
              :key-id="node.keyId"
              :config-data="node.configData"
              :collapse-all-eligibility="collapseAllEligibility"
              :expand-all-eligibility="expandAllEligibility"
              :node-item="node"
              :transaction-node-tree="fullFlatNodes"
              @to-collapse-all="toCollapseAll"
              @to-expand-all="toExpandAll"
            />
          </div>

          <draggable
            :filter="'.undraggable'"
            :prevent-on-filter="false"
            :sort="false"
            @start="onDragStart($event, node)"
            @end="onDragEnd"
            @move="onMove"
          >
            <!-- Render paginated children -->
            <div
              v-for="(child, index) in getPaginatedChildren(node.id)"
              :key="child.id"
              :style="{ 'margin-left': (child.depth * 25) + 'px' }"
              :class="{
                'mr-1': child.nestedLabel.includes('auto_extraction_keys'),
                'undraggable': !child.draggable,
              }"
              @dragover.prevent
              @drop="onDrop($event, child, index)"
            >
              <BatchNode
                :id="child.id"
                :label="child.label"
                :title="child.title"
                :expandable="child.expandable"
                :expanded="child.expanded"
                :test="child.test"
                :highlighted="child.highlighted"
                :is-profile-key-found="child.isProfileKeyFound"
                :search-match="child.searchMatch"
                :type="child.type"
                :badge-variant="child.badgeVariant"
                :nested-label="child.nestedLabel"
                :key-id="child.keyId"
                :config-data="child.configData"
                :collapse-all-eligibility="collapseAllEligibility"
                :expand-all-eligibility="expandAllEligibility"
                :node-item="child"
                :transaction-node-tree="fullFlatNodes"
                @to-collapse-all="toCollapseAll"
                @to-expand-all="toExpandAll"
              />
            </div>
          </draggable>

          <b-pagination
            v-if="hasPagination(node)"
            :value="getCurrentPage(node.type, node.id)"
            :total-rows="getGroupedChildrenCount(node)"
            :per-page="pageSize"
            size="sm"
            class="pagination-controls"
            :style="{ 'margin-left': ((node.depth + 1) * 25) + 'px' }"
            @input="setCurrentPage(node.type, node.id, $event)"
          />
        </template>
      </div>
    </div>

    <!-- Confirmation Modal for Mapping Keys to Project via Drag and Drop -->
    <confirm-key-mapping
      v-if="showConfirmationModal"
      :dragged-item-lable="draggedItem ? draggedItem.label : ''"
      :drop-target-label="dropTarget ? dropTarget.item.label : ''"
      @confirmed="handleCustomDropAction()"
      @modal-closed="resetDragState()"
      @cancel="resetDragState()"
      @close="resetDragState()"
    />
  </div>
</template>

<script>
import axios from 'axios'
import { cloneDeep } from 'lodash'
import draggable from 'vuedraggable' // Draggable component for drag-and-drop functionality
import {
  BPagination,
} from 'bootstrap-vue'
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import ConfirmKeyMapping from '@/components/UI/ConfirmKeyMapping.vue'
import BatchNode from './BatchNode.vue'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

export default {
  components: {
    BatchNode,
    BPagination,
    draggable,
    ConfirmKeyMapping,
  },
  data() {
    return {
      fullFlatNodes: [],
      batchDocumentNodes: [],
      paginations: {},
      pageSize: 10,
      groupedParentTypes: ['auto_extraction_parent', 'process_keys_parent'],
      draggedItem: null,
      draggedIndex: null,
      dropTarget: null,
      showConfirmationModal: false,
      isExpanding: false, // Flag to prevent multiple expansion operations
      isClickHandling: false, // Flag to prevent route watcher during click operations
    }
  },
  computed: {
    isCombinedView() {
      return this.$store.state.batch.isCombineView
    },
    isProfileLoading() {
      return this.$store.getters['batch/isProfileLoadig']
    },
    isAutoExtractedKeys() {
      return this.$store.getters['dataView/getAutoExtractedKeys']
    },
    isKeyRecognized() {
      return this.$store.getters['batch/isKeyRecognized']
    },
    transactionBatches() {
      return this.$store.getters['batch/transactionBatches']
    },
    flatNodes() {
      return this.$store.getters['batch/flatNodes']
    },
    transaction() {
      return this.$store.getters['batch/transaction']
    },
    collapseAllEligibility() {
      return this.flatNodes.some(element => element.expanded && !['root', 'batch'].includes(element.type))
    },
    expandAllEligibility() {
      return this.flatNodes.some(element => !element.expanded)
    },
    getProfileDetails() {
      return this.$store.getters['batch/profileDetails']
    },
    // profileKeys() {
    //   return this.$store.getters['batch/profileKeys']
    // },
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    project() {
      return this.$store.getters['project/project']
    },
    undoKeyMappingData() {
      return this.$store.getters['batch/undoKeyMappingData']
    },
    visibleNodes() {
      const allowedTypes = ['transaction', 'batch', 'document', 'vendor', 'root']
      const groupedParentTypes = ['auto_extraction_parent', 'process_keys_parent']

      // Base visible nodes (non combined view filtering)
      const getBaseVisibleNodes = () => {
        if (this.mainMode !== 'verification') {
          const nodeMap = new Map()
          const expandedNodeIds = new Set()
          const groupedParentIds = new Set()

          // Build maps for lookups
          this.flatNodes.forEach(node => {
            nodeMap.set(node.nodeId, node)
            if (node.expanded) expandedNodeIds.add(node.nodeId)
            if (groupedParentTypes.includes(node.type)) groupedParentIds.add(node.nodeId)
          })

          const shouldNodeBeVisible = node => {
            if (allowedTypes.includes(node.type)) return true
            if (groupedParentTypes.includes(node.type)) {
              if (node.type === 'auto_extraction_parent') return this.isAutoExtractedKeys
              if (node.type === 'process_keys_parent') return !this.isAutoExtractedKeys && !this.isKeyRecognized
              return false
            }
            if (node.isPureAutoextraction === true && node.isProfileKeyFound === true) return true
            return false
          }

          const hasExpandedVisibleAncestor = node => {
            let parentId = node.parentNodeId
            while (parentId) {
              const parentNode = nodeMap.get(parentId)
              if (!parentNode) break

              // Skip grouped parents - their children are handled separately
              if (!groupedParentTypes.includes(parentNode.type)) {
                if (shouldNodeBeVisible(parentNode)) {
                  return true
                }
              }

              parentId = parentNode.parentNodeId
            }
            return false
          }

          return this.flatNodes.filter(node => {
            //  CRITICAL FIX: Exclude ALL descendants of grouped parents
            // Check if this node has any grouped parent as an ancestor
            let parentId = node.parentNodeId
            while (parentId) {
              if (groupedParentIds.has(parentId)) {
                return false // This node is a descendant of a grouped parent - exclude it
              }
              const parentNode = nodeMap.get(parentId)
              if (!parentNode) break
              parentId = parentNode.parentNodeId
            }

            // Filter out empty keys based on document-level hide setting
            // Apply to all green/red badge keys (isProfileKeyFound = true)
            if (node.isProfileKeyFound === true && node.type !== 'vendor') {
              const { documentId } = node
              if (documentId) {
                const hideEmptyKeys = this.hideEmptyAutoExtrationKeys?.[documentId] ?? true
                if (hideEmptyKeys) {
                  const titleValue = node.title ?? ''
                  if (titleValue.toString().trim() === '') {
                    return false // Hide this empty key
                  }
                }
              }
            }

            // Include the node if it should be visible
            if (shouldNodeBeVisible(node)) return true

            // Check ancestors for visibility
            return hasExpandedVisibleAncestor(node)
          })
        }
        return this.flatNodes
      }

      const baseVisibleNodes = getBaseVisibleNodes()

      // Apply combine view logic
      if (this.isCombinedView) {
        const nodeMap = new Map()
        baseVisibleNodes.forEach(node => nodeMap.set(node.nodeId, node))

        return baseVisibleNodes
        // remove vendor, document, and grouped parents
          .filter(node => node.type !== 'vendor'
        && node.type !== 'document'
        && !groupedParentTypes.includes(node.type))
        // also remove children of grouped parents
          .filter(node => {
            let parentId = node.parentNodeId
            while (parentId) {
              const parent = nodeMap.get(parentId)
              if (parent && groupedParentTypes.includes(parent.type)) {
                return false // child of grouped parent → remove
              }
              parentId = parent ? parent.parentNodeId : null
            }
            return true
          })
        // re-map children of documents directly to batch
          .map(node => {
            const parentNode = nodeMap.get(node.parentNodeId)
            if (parentNode && parentNode.type === 'document') {
              const batchParent = nodeMap.get(parentNode.parentNodeId)
              if (batchParent && batchParent.type === 'batch') {
                return {
                  ...node,
                  parentNodeId: batchParent.nodeId,
                }
              }
            }
            return node
          })
      }

      return baseVisibleNodes
    },

    batchId() {
      return this.$store.getters['batch/batch'].id
    },
    hideEmptyAutoExtrationKeys() {
      return this.$store.getters['batch/hideEmptyAutoExtrationKeys']
    },
    // Get batch-id from route query parameter
    routeBatchId() {
      return this.$route.query['batch-id']
    },
  },
  watch: {
    getProfileDetails(newVal) {
      if (newVal && newVal.project_id) {
        this.$store.dispatch('project/fetchProjectDetail', newVal.project_id)
        this.$store.dispatch('batch/fetchProjectKeys')
        this.$store.dispatch('batch/fetchProfileKeys')
      }
    },
    batchId(newVal, oldVal) {
      if (newVal) {
        this.$store.commit('batch/SET_SHOW_HIDE_RECOGNIZED_KEYS', false)
        this.$store.commit('dataView/AUTO_EXTRACTED_KEY', false)

        const routeBatchId = this.$route.query['batch-id']
        if (oldVal !== newVal && !this.isExpanding && routeBatchId !== newVal) {
          // Route will be updated by BatchSelector, so routeBatchId watcher will handle expansion
          // But if route wasn't updated for some reason, expand here as fallback
          this.$nextTick(() => {
            this.expandNodeByBatchId(newVal)
          })
        }
      }
    },
    // Watch route batch-id changes - this is the primary trigger for node expansion
    routeBatchId(newVal, oldVal) {
      // Skip expansion if click handler is active (prevents flickering)
      if (this.isClickHandling) {
        return
      }

      if (newVal && newVal !== oldVal && !this.isExpanding) {
        this.$nextTick(() => {
          if (!this.isExpanding && !this.isClickHandling) {
            this.expandNodeByBatchId(newVal)
          }
        })
      } else if (!newVal && oldVal && !this.isExpanding) {
        // If batch-id is removed from route, expand all as fallback
        this.$nextTick(() => {
          this.toExpandAll()
        })
      }
    },
    isCombinedView(newVal, oldVal) {
      if (oldVal === true && newVal === false) {
        this.toExpandAll()

        // Initialize group parents expansion state after initial expansion
        this.$nextTick(() => {
          this.autoExpandGroupParents()
        })
      }
      // NEW FIX: When enabling combine view, ensure all document nodes are expanded
      // so their children are available for remapping to batch
      if (newVal === true) {
        this.$nextTick(() => {
          const documentNodes = this.flatNodes.filter(node => node.type === 'document')
          documentNodes.forEach(docNode => {
            if (!docNode.expanded) {
              this.$store.commit('batch/EXPAND_NODE', docNode.id)
            }
          })
        })
      }
    },
    // isAllExtractionTrue: {
    //   handler(newVal) {
    //     this.$store.commit('dataView/AUTO_EXTRACTED_KEY', newVal)
    //   },
    //   immediate: true,
    // },
  },
  mounted() {
    this.$store.dispatch('batch/getProfileDetails')
    this.fullFlatNodes = cloneDeep(this.flatNodes)
    // this.batchDocumentNodes = this.fullFlatNodes.filter(
    //   node => node.type === 'batch' || node.type === 'document',
    // )

    // Expand only the node matching route batch-id, or expand all if no batch-id in route
    // Use nextTick to ensure flatNodes are ready
    this.$nextTick(() => {
      const routeBatchId = this.$route.query['batch-id']
      if (routeBatchId && this.flatNodes.length > 0) {
        this.expandNodeByBatchId(routeBatchId)
      } else if (this.flatNodes.length > 0) {
        // Fallback to expand all if no batch-id in route
        this.toExpandAll()
        // Initialize group parents expansion state after initial expansion
        this.$nextTick(() => {
          this.autoExpandGroupParents()
        })
      }
    })
  },
  created() {
    bus.$on('batch/undoKeyMapping', this.undoKeyMapping)
    bus.$on('getNewTrainingLinkedBatch', this.toExpandAll)
  },
  destroyed() {
    // Removes event listeners when the component is destroyed to avoid memory leaks.
    bus.$off('batch/undoKeyMapping', this.updateStatus)
    bus.$off('getNewTrainingLinkedBatch', this.toExpandAll)
  },
  methods: {
    // Get current page for a node
    getCurrentPage(nodeType, nodeId) {
      const key = `${nodeType}_${nodeId}`
      return this.paginations[key] || 1
    },

    // Set page for a node
    setCurrentPage(nodeType, nodeId, page) {
      const key = `${nodeType}_${nodeId}`
      this.$set(this.paginations, key, page)
    },
    isChildOfGroupedParent(node) {
      // Filter parent too when expended
      if (this.groupedParentTypes.includes(node.type) && node.expanded) return true

      if (!node.parentNodeId) return false

      const parent = this.flatNodes.find(n => n.nodeId === node.parentNodeId)
      return parent && this.groupedParentTypes.includes(parent.type)
    },

    getPaginatedChildren(parentId) {
      const hideEmptyKeys = this.hideEmptyAutoExtrationKeys?.[parentId] ?? true
      const parentNode = this.flatNodes.find(n => n.id === parentId)
      if (!parentNode) return []

      let children = this.flatNodes.filter(n => n.parentNodeId === parentNode.nodeId)

      if (hideEmptyKeys && parentNode.type === 'auto_extraction_parent') {
        children = children.filter(n => n.title.trim() !== '')
      }

      const pType = parentNode.type
      const page = this.getCurrentPage(pType, parentNode.id)
      const start = (page - 1) * this.pageSize
      const end = start + this.pageSize
      const paginatedChildren = children.slice(start, end)

      // fix: if child has its own children (like shipper/consignee), include them if expanded
      const withNested = []
      paginatedChildren.forEach(child => {
        withNested.push(child)
        if (child.expandable && child.expanded) {
          const nestedChildren = this.getNestedChildren(child.nodeId)
          withNested.push(...nestedChildren)
        }
      })

      return withNested
    },

    getNestedChildren(parentNodeId) {
      const children = this.flatNodes.filter(n => n.parentNodeId === parentNodeId)
      const result = []
      children.forEach(child => {
        result.push(child)
        if (child.expandable && child.expanded) {
          result.push(...this.getNestedChildren(child.nodeId))
        }
      })
      return result
    },

    hasPagination(node) {
      return this.groupedParentTypes.includes(node.type) && this.getGroupedChildrenCount(node) > this.pageSize
    },

    getGroupedChildrenCount(node) {
      const hideEmptyKeys = this.hideEmptyAutoExtrationKeys?.[node.id] ?? true
      const parentNode = this.flatNodes.find(n => n.type === node.type && n.id === node.id)

      let children = this.flatNodes.filter(n => n.parentNodeId === parentNode?.nodeId)
      if (hideEmptyKeys && parentNode.type === 'auto_extraction_parent') {
        children = children.filter(n => n.title.trim() !== '')
      }
      return children.length
    },

    createFlatNodeMap(nodes = this.flatNodes) {
      return nodes.reduce((acc, node) => {
        if (node?.nodeId) acc[node.nodeId] = node
        return acc
      }, {})
    },

    autoExpandGroupParents(selectedBatchNodeId = null, suppressGroupedExpansion = false) {
      this.$nextTick(() => {
        const flatNodeMap = this.createFlatNodeMap()
        this.flatNodes.forEach(node => {
          // If a batch node ID is provided, check if this node belongs to that batch
          let belongsToSelectedBatch = false
          if (selectedBatchNodeId) {
            let parentId = node.parentNodeId
            while (parentId) {
              const parentNode = flatNodeMap[parentId]
              if (!parentNode) break
              if (parentNode.nodeId === selectedBatchNodeId
                  || (parentNode.type === 'batch' && parentNode.nodeId === selectedBatchNodeId)) {
                belongsToSelectedBatch = true
                break
              }
              parentId = parentNode.parentNodeId
            }
          }

          if (node.type === 'auto_extraction_parent') {
            if (suppressGroupedExpansion && belongsToSelectedBatch) {
              // Explicitly keep auto extraction collapsed on batch selection
              this.$store.commit('batch/COLLAPSE_NODE', node.id)
            } else if (this.isAutoExtractedKeys) {
              if (!node.expanded) {
                this.$store.commit('batch/EXPAND_NODE', node.id)
              }
            } else if (!belongsToSelectedBatch) {
              this.$store.commit('batch/COLLAPSE_NODE', node.id)
            }
          }

          if (node.type === 'process_keys_parent') {
            if (suppressGroupedExpansion && belongsToSelectedBatch) {
              // Explicitly keep process keys collapsed on batch selection
              this.$store.commit('batch/COLLAPSE_NODE', node.id)
            } else if (this.isKeyRecognized) {
              if (!node.expanded) {
                this.$store.commit('batch/EXPAND_NODE', node.id)
              }
            } else if (!belongsToSelectedBatch) {
              this.$store.commit('batch/COLLAPSE_NODE', node.id)
            }
          }
        })
      })
    },

    toCollapseAll() {
      let nodesToCollapse
      if (this.isCombinedView) {
        // In combine view, collapse batch-level nodes only (documents are gone)
        nodesToCollapse = this.visibleNodes.filter(node => node.expanded && node.type === 'batch')
      } else {
        // Normal view: collapse everything except root & batch
        nodesToCollapse = this.visibleNodes.filter(node => node.expanded && !['root', 'batch'].includes(node.type))
      }
      nodesToCollapse.forEach(node => this.$store.commit('batch/COLLAPSE_NODE', node.id))
    },

    toExpandAll() {
      let nodesToExpand
      if (this.isCombinedView) {
        // In combine view, expand batch-level nodes only
        nodesToExpand = this.visibleNodes.filter(node => node.expandable && !node.expanded && node.type === 'batch')
      } else {
        // Normal view: expand everything that is expandable
        nodesToExpand = this.visibleNodes.filter(node => node.expandable && !node.expanded)
      }
      nodesToExpand.forEach(node => this.$store.commit('batch/EXPAND_NODE', node.id))
    },

    // Expand only the node matching the batch-id and its ancestors
    expandNodeByBatchId(batchId) {
      if (this.isExpanding) return // Prevent concurrent expansion operations
      if (!this.flatNodes || this.flatNodes.length === 0) return // Ensure flatNodes are ready

      this.isExpanding = true

      try {
        // Find the batch node matching the batchId
        const targetBatchNode = this.flatNodes.find(
          node => node.type === 'batch' && node.id === batchId,
        )

        if (!targetBatchNode) {
          // If batch node not found, fallback to expand all
          this.toExpandAll()
          this.isExpanding = false
          return
        }

        // Build a map for efficient parent lookup
        const nodeMap = new Map()
        this.flatNodes.forEach(node => {
          nodeMap.set(node.nodeId, node)
        })

        // Build the path from root to target batch node
        const expandPath = []
        let currentNode = targetBatchNode

        while (currentNode) {
          expandPath.unshift(currentNode)

          // Find parent node
          if (currentNode.parentNodeId) {
            currentNode = nodeMap.get(currentNode.parentNodeId)
          } else {
            currentNode = null
          }
        }

        // Find all document nodes under this batch
        // Try multiple methods to find documents
        const documentNodes = this.flatNodes.filter(node => {
          if (node.type !== 'document') return false

          // Method 1: Check parentNodeId
          if (node.parentNodeId === targetBatchNode.nodeId) return true

          // Method 2: Check if document ID starts with batch ID (e.g., M20251007.US200031.01 starts with M20251007.US200031)
          if (node.id && node.id.startsWith(`${batchId}.`)) return true

          // Method 3: Check batchId property
          if (node.batchId === batchId || node.currentBatchId === batchId) return true

          return false
        })

        // Intentionally DO NOT auto-expand grouped parents (auto extraction/process keys)
        // when batch is selected from selector

        // Create a Set of node IDs that should be expanded (for quick lookup)
        const pathNodeIds = new Set(expandPath.map(node => node.nodeId))

        // Add document nodes to the set of nodes to expand
        documentNodes.forEach(doc => {
          pathNodeIds.add(doc.nodeId)
        })

        // Note: skip adding grouped parent nodes to expansion set

        // Check if we need to make any changes
        let needsCollapse = false
        let needsExpand = false

        // Check for nodes that need collapsing
        const nodesToCollapse = this.flatNodes.filter(node => {
          if (!node.expanded) return false
          if (['root', 'transaction'].includes(node.type)) return false
          if (!pathNodeIds.has(node.nodeId)) {
            needsCollapse = true
            return true
          }
          return false
        })

        // Check for nodes that need expanding (path + documents)
        const allNodesToExpand = [...expandPath, ...documentNodes]
        allNodesToExpand.forEach(node => {
          if (node.expandable && !node.expanded) {
            needsExpand = true
          }
        })

        // Only perform operations if needed to reduce twitching
        if (needsCollapse || needsExpand) {
          // Collapse nodes not in path first (to reduce visual flicker)
          if (needsCollapse) {
            nodesToCollapse.forEach(node => {
              this.$store.commit('batch/COLLAPSE_NODE', node.id)
            })
          }

          // Then expand nodes in path, documents, and grouped parents
          if (needsExpand) {
            // Expand path nodes first
            expandPath.forEach(node => {
              if (node.expandable && !node.expanded) {
                this.$store.commit('batch/EXPAND_NODE', node.id)
              }
            })

            // Then expand document nodes (after a small delay to ensure batch is expanded)
            this.$nextTick(() => {
              // Expand all document nodes
              documentNodes.forEach(doc => {
                if (doc.expandable && !doc.expanded) {
                  this.$store.commit('batch/EXPAND_NODE', doc.id)
                }
              })

              // After documents expand, explicitly collapse grouped parent nodes under this batch
              setTimeout(() => {
                // Re-find document nodes after expansion (in case flatNodes updated)
                const updatedDocumentNodes = this.flatNodes.filter(node => {
                  if (node.type !== 'document') return false
                  if (node.parentNodeId === targetBatchNode.nodeId) return true
                  if (node.id && node.id.startsWith(`${batchId}.`)) return true
                  if (node.batchId === batchId || node.currentBatchId === batchId) return true
                  return false
                })

                // Also expand any documents that weren't found initially but now exist
                updatedDocumentNodes.forEach(doc => {
                  if (doc.expandable && !doc.expanded) {
                    this.$store.commit('batch/EXPAND_NODE', doc.id)
                  }
                })

                // Find grouped parents under these documents and collapse them
                const groupedParentsAfterDocs = this.flatNodes.filter(node => this.groupedParentTypes.includes(node.type))
                const parentsToCollapse = []
                const refreshedNodeMap = this.createFlatNodeMap()
                groupedParentsAfterDocs.forEach(groupedNode => {
                  let currentParentId = groupedNode.parentNodeId
                  while (currentParentId) {
                    const parentNode = refreshedNodeMap[currentParentId]
                    if (!parentNode) break
                    if (updatedDocumentNodes.some(doc => doc.nodeId === parentNode.nodeId) || parentNode.nodeId === targetBatchNode.nodeId) {
                      parentsToCollapse.push(groupedNode)
                      break
                    }
                    currentParentId = parentNode.parentNodeId
                  }
                })
                parentsToCollapse.forEach(grouped => {
                  if (grouped.expanded) {
                    this.$store.commit('batch/COLLAPSE_NODE', grouped.id)
                  }
                })
              }, 300) // Increased delay to 300ms for document expansion to complete and flatNodes to update
            })
          }
        }

        // Store the batch node ID for reference in autoExpandGroupParents
        const selectedBatchNodeId = targetBatchNode.nodeId

        // Initialize group parents expansion state after expansion
        // Use a longer delay to ensure all expansions are complete before auto-expanding grouped parents
        this.$nextTick(() => {
          setTimeout(() => {
            // Keep grouped parents collapsed for the selected batch during selection
            this.autoExpandGroupParents(selectedBatchNodeId, true)
          }, 100)
        })
      } finally {
        // Reset flag after a short delay to allow DOM updates
        this.$nextTick(() => {
          setTimeout(() => {
            this.isExpanding = false
          }, 150)
        })
      }
    },
    onDragStart(event, node) {
      const draggedIndex = event.oldIndex
      const childNodeList = this.getPaginatedChildren(node.id)
      this.draggedItem = { ...childNodeList[draggedIndex] }
      this.draggedIndex = draggedIndex
    },

    async onDragEnd() {
      if (!this.dropTarget || !this.draggedItem) return

      if (!this.dropTarget.item.draggableTarget || this.dropTarget.item.id === this.draggedItem.id) return

      const { batchId, documentId } = this.extractIds(this.draggedItem.id)
      const targetItemIds = this.extractIds(this.dropTarget.item?.id)

      if (targetItemIds.batchId !== batchId || !batchId || !documentId) return

      this.showConfirmationModal = true
    },

    onMove() {
      // Prevent actual sorting/moving
      return false
    },

    onDrop(event, targetItem, targetIndex) {
      event.preventDefault()

      if (this.draggedItem && targetItem.id !== this.draggedItem.id) {
        this.dropTarget = {
          item: targetItem,
          index: targetIndex,
        }
      }
    },

    async handleCustomDropAction() {
      try {
        const { batches } = this.transactionBatches
        if (!batches) return

        const { batchId, documentId } = this.extractIds(this.draggedItem.id)

        const batch = batches.find(e => e.id === batchId)
        if (!batch) return

        const dataJson = batch.data_json

        if (!dataJson) return

        const document = dataJson?.nodes.find(e => e.id === documentId)
        if (!document) return

        const keyNodeItems = document.children?.find(e => e.type === 'key')
        if (!keyNodeItems) return

        const actualDraggedItem = keyNodeItems.children?.find(e => e.id === this.draggedItem.id)
        if (!actualDraggedItem || !this.dropTarget?.item?.label) return

        const undoKeyMappingData = {
          draggedItem: cloneDeep(actualDraggedItem),
          targetedItem: null,
        }

        let actualTargetedItemIndex = -1

        const actualTargetedItem = keyNodeItems.children?.find(e => e.id === this.dropTarget.item.id)
        if (actualTargetedItem) {
          actualTargetedItemIndex = keyNodeItems.children.findIndex(e => e.id === this.dropTarget.item.id)
          undoKeyMappingData.targetedItem = {
            actualTargetedItemIndex,
            item: cloneDeep(actualTargetedItem),
          }
        }

        if (actualDraggedItem.v.trim() !== '') {
          // Update the item (standard JavaScript assignment)
          actualDraggedItem.is_profile_key_found = true
          actualDraggedItem.is_label_mapped = true
          actualDraggedItem.label = this.dropTarget.item.label

          // Delete empty procees key that has been mapped
          if (actualTargetedItemIndex !== -1) {
            keyNodeItems.children.splice(actualTargetedItemIndex, 1)
          }
        }

        this.$store.commit('batch/SET_UNDO_KEY_MAPPING_DATA', undoKeyMappingData)

        await this.syncMappedKey(this.draggedItem.label, this.dropTarget.item.label, batchId, dataJson)

        await this.$store.dispatch('batch/loadTransaction', this.transactionBatches)
      } catch (error) {
        // console.error('Error in handleCustomDropAction:', error)
      } finally {
        this.resetDragState()
      }
    },

    async syncMappedKey(mappedKey, keyLabel, batchId, dataJson, undo = false) {
      try {
        await axios.patch(`/dashboard/projects/${this.project.id}/sync_mapped_keys/`, {
          key_label: this.camelToNormal(keyLabel),
          mapped_key: this.camelToNormal(mappedKey),
          batch_id: batchId,
          data_json: dataJson,
          undo,
        })

        this.$toast({
          component: ToastificationContent,
          props: {
            title: `Mapped key '${mappedKey}' successfully ${undo ? 'removed' : 'added'}`,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
      } catch (error) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error while mapping keys',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },

    undoKeyMapping() {
      const { batches } = this.transactionBatches
      if (!batches) return

      const { draggedItem, targetedItem } = this.undoKeyMappingData

      if (!draggedItem || !targetedItem?.item) return

      const { batchId, documentId } = this.extractIds(draggedItem?.id)

      const batch = batches.find(e => e.id === batchId)
      if (!batch) return

      const dataJson = batch.data_json

      if (!dataJson) return

      const document = dataJson?.nodes.find(e => e.id === documentId)
      if (!document) return

      const keyNodeItems = document.children?.find(e => e.type === 'key')
      if (!keyNodeItems) return

      const actualDraggedItem = keyNodeItems.children?.find(e => e.id === draggedItem.id)
      if (actualDraggedItem) {
        actualDraggedItem.is_profile_key_found = false
        actualDraggedItem.is_label_mapped = false
        actualDraggedItem.label = draggedItem.label
      }

      if (targetedItem) {
        keyNodeItems.children.splice(targetedItem.index, 0, targetedItem.item)
      }

      this.$store.commit('batch/SET_UNDO_KEY_MAPPING_DATA', null)
      this.syncMappedKey(draggedItem.label, targetedItem.item.label, batchId, dataJson, true)
      this.$store.dispatch('batch/loadTransaction', this.transactionBatches)
    },

    resetDragState() {
      this.showConfirmationModal = false
      this.draggedItem = null
      this.draggedIndex = null
      this.dropTarget = null
    },

    extractIds(inputString) {
      const parts = inputString.split('.')

      // batchId: first two parts
      const batchId = parts.length >= 2 ? parts.slice(0, 2).join('.') : null

      // documentId: first three parts, but only if length >= 3
      const documentId = parts.length >= 3 ? parts.slice(0, 3).join('.') : null

      return { batchId, documentId }
    },
    camelToNormal(str) {
      if (!str) return str

      if (str.length === 1) return str.toUpperCase()

      return str.replace(/([A-Z])/g, ' $1').replace(/^./, char => char.toUpperCase())
    },
  },
}
</script>

<style scoped>
.scroller-container {
    height:100%;
    position:relative;
}
.scroller {
    position: absolute;
    left: 0px;
    top: 0px;
    width: 100%;
    height: 100%;
    overflow-y: auto;
}
.pagination-controls {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  margin-bottom: 8px;
  align-items: center;
  font-size: 12px;
}
.pagination-controls button {
  padding: 2px 8px;
  font-size: 12px;
  border: 1px solid #ddd;
  background: #f5f5f5;
  border-radius: 3px;
  cursor: pointer;
}
.pagination-controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.undraggable:hover {
  transform: none !important;
  box-shadow: none !important;
}
/* no-op: removed header toggle */
</style>
