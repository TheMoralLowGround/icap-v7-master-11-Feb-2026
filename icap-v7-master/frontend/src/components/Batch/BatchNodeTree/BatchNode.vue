<!--
 Organization: AIDocbuilder Inc.
 File: BatchNode.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   The `BatchNode.vue` component is a flexible and expandable node component designed to display
   a batch node with various states and actions. The component supports different modes (e.g., edit, verification)
   and includes features such as expandable nodes, badges, and editable fields.
   It is often used to represent nodes in a batch processing system, where each node can have configurable properties,
   expandable content, and actions associated with it.

 Features:
   - Displays a batch node with expandable/collapsible functionality.
   - Supports different node types, including "root" and other custom types.
   - Conditionally renders additional elements such as batch version, configuration, and editor fields.
   - Handles node interactivity with click and double-click events.
   - Provides dynamic badge variants based on the node's status and properties.

 Dependencies:
   - `BatchDefintionVersion`: A child component displaying batch definition version for root nodes.
   - `BatchNodeConfig`: A child component for configuring the batch node in edit mode.
   - `NodeEditor`: A child component for editing node details in verification mode.
   - `BBadge`: A Bootstrap Vue badge component used for displaying labels and statuses.

 Notes:
   - The component renders differently based on the `type` prop, allowing for unique handling of root and non-root nodes.
   - The `expandable` prop and `expanded` state control the collapsible behavior of nodes.
   - The `mode` prop and `mainMode` prop define whether the node is in edit or verification mode, affecting the rendering of editable fields and components.
   - The component is part of a larger batch processing system where nodes represent individual tasks or batches.
-->

<template>
  <!-- Main container for a node, styled with utility classes -->
  <div
    class="node d-flex align-items-center"
    :class="{
      highlighted: highlighted,
      'search-match': searchMatch,
    }"
    @click="clickHandler"
    @dblclick="dbClickHandler"
  >
    <!-- Main content container with flexible width -->
    <div class="flex-grow-1">
      <!-- Displays a toggle symbol ('-' or '+') if the node is expandable -->
      <span v-if="expandable">
        {{ expanded ? '-' : '+' }}
      </span>

      <!-- Displays a badge if the node has a label -->
      <b-badge
        v-if="label !== ''"
        :variant="localBadgeVariant"
      >
        {{ label }}
      </b-badge>

      <!-- Displays the node title in non-editable mode -->
      <span v-if="mainMode !== 'verification' || !editableNode || editableNode.id !== id">
        &nbsp;
        <span
          v-if="type==='root'"
          style="white-space: pre-wrap"
        >{{ label !== '' ? `- ${title}`: title }}</span>
        <span
          v-if="type==='batch'"
          style="white-space: pre-wrap"
        >{{ label !== '' ? `- ${title}`: title }} - {{ nodeItem.documentType }}</span>
        <span
          v-if="type==='document'"
          style="white-space: pre-wrap"
        >{{ id }} - {{ nodeItem.vendorName }}</span>
        <span
          v-if="!['root', 'batch', 'document'].includes(type)"
          style="white-space: pre-wrap"
        >- {{ title }}</span>
      </span>

      <!-- Document-level hide empty keys switch -->
      <b-form-checkbox
        v-if="mode === 'edit' && mainMode !== 'verification' && type === 'document'"
        v-model="documentHideEmptyKeys"
        v-b-tooltip.hover
        name="hide-empty-keys"
        :title="documentHideEmptyKeys ? 'Hide Empty Keys' : 'Show Empty Keys'"
        switch
        class="d-inline-block ml-2 mb-0"
        style="vertical-align: middle;"
      />
    </div>
    <!-- <div v-if="(['document', 'batch'].includes(type) && profileKeys.length > 0) || (type === 'batch' && findBatchAccuracy !== null)">
      <AccuracyProgressor :percentage="type === 'batch' ? findBatchAccuracy : findAccuracy" />

    </div> -->
    <!-- Editable node value -->
    <node-editor
      v-if="mainMode === 'verification' && editableNode && editableNode.id === id"
      class="ml-1"
    />

    <!-- Conditional rendering for root nodes -->
    <div
      v-if="type === 'root'"
      class="d-flex"
    >
      <!-- This functinality will applied later -->
      <b-form-checkbox
        v-model="isCombineView"
        v-b-tooltip.hover
        name="check-button"
        :title="isCombineView ? 'Combined View On' : 'Single View On'"
        switch
      />
      <div
        v-if="expandAllEligibility && !collapseAllEligibility"
        class="badge badge-primary mr-1"
        @click.stop="toExpandAll"
      >
        <feather-icon
          icon="ChevronsDownIcon"
          size="12"
        />
      </div>

      <!-- 'Collapse All' button for root nodes, visible if allowed -->
      <div
        v-if="collapseAllEligibility"
        class="badge badge-primary mr-1"
        @click.stop="toCollapseAll"
      >
        <feather-icon
          icon="ChevronsUpIcon"
          size="12"
        />
      </div>

      <!-- Document sort order toggle -->
      <div
        v-b-tooltip.hover
        class="badge badge-light-primary mr-1"
        :title="documentSortOrder === 'asc' ? 'Documents: Ascending (click to switch)' : 'Documents: Descending (click to switch)'"
        @click.stop="$store.commit('batch/TOGGLE_DOCUMENT_SORT_ORDER')"
      >
        <feather-icon
          :icon="documentSortOrder === 'asc' ? 'ArrowUpIcon' : 'ArrowDownIcon'"
          size="12"
        />
      </div>

      <!-- Batch definition version component for root nodes -->
      <batch-defintion-version />
    </div>

    <!-- Conditional rendering for non-root nodes -->
    <div v-else>
      <!-- Displays a test property if available -->
      <span
        v-if="test"
        class="d-inline-block mx-1 text-primary"
      >{{
        test
      }}</span>

      <!-- Batch node configuration for editable nodes in edit mode -->
      <batch-node-config
        v-if="mode === 'edit' && mainMode !== 'verification' && label.toLowerCase() !== 'block'"
        :node-id="id"
        :nested-label="nestedLabel"
        :key-id="keyId"
        :config-data="configData"
        :is-profile-key-found="!['root', 'batch', 'document'].includes(type) && !isProfileKeyFound"
        :is-label-mapped="nodeItem && nodeItem.isLabelMapped"
        :is-key-from-table="nodeItem && nodeItem.isKeyFromTable"
        :original-key-label="nodeItem && nodeItem.OriginalKeyLabel"
        :label="label"
        :type="type"
        :batch-id="nodeItem.currentBatchId"
        :document-id="nodeItem.documentId"
        :is-address-block-partial="nodeItem.isAddressBlockPartial"
      />
    </div>

  </div>
</template>

<script>
import bus from '@/bus'
import { BBadge, BFormCheckbox, VBTooltip } from 'bootstrap-vue'
import BatchDefintionVersion from '@/components/Batch/BatchDefinitionVersion.vue'
import BatchNodeConfig from './BatchNodeConfig.vue'
import NodeEditor from '../NodeEditor.vue'
// import AccuracyProgressor from './AccuracyProgressor.vue'
// import toCamelCase from '../utils/convertCase'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BBadge,
    BatchNodeConfig,
    NodeEditor,
    BatchDefintionVersion,
    // AccuracyProgressor,
    BFormCheckbox,
  },
  props: {
    // Unique identifier for the component instance
    id: {
      required: true, // This prop must be provided
      type: String, // Expects a string
    },
    // Title text for the component
    title: {
      type: [String, Number], // Expects a string
      required: true, // This prop must be provided
    },
    // Indicates whether the component can be expanded
    expandable: {
      type: Boolean, // Expects a boolean
      required: true, // This prop must be provided
    },
    // Indicates whether the component is currently expanded
    expanded: {
      type: Boolean, // Expects a boolean
      required: true, // This prop must be provided
    },
    // Optional test string for debugging or other purposes
    test: {
      type: String, // Expects a string
      required: false, // Not mandatory
      default() {
        return null // Default value is `null` if not provided
      },
    },
    // Indicates if the component is highlighted
    highlighted: {
      type: Boolean, // Expects a boolean
      requred: true, // Typo in "required", should be "required: true"
    },
    isProfileKeyFound: {
      type: Boolean,
      default: () => false,
    },
    // Indicates if there is a search match for this component
    searchMatch: {
      type: Boolean, // Expects a boolean
      required: true, // This prop must be provided
    },
    // Type of the component, e.g., "node" or "item"
    type: {
      type: String, // Expects a string
      required: true, // This prop must be provided
    },
    // Label for display purposes
    label: {
      type: String, // Expects a string
      required: true, // This prop must be provided
    },
    // Style variant for a badge, e.g., "primary" or "warning"
    badgeVariant: {
      type: String, // Expects a string
      required: true, // This prop must be provided
    },
    // Optional secondary label for nested items
    nestedLabel: {
      type: String, // Expects a string
      required: false, // Not mandatory
      default() {
        return null // Default value is `null` if not provided
      },
    },
    // Optional key identifier
    keyId: {
      type: String, // Expects a string
      required: false, // Not mandatory
      default() {
        return null // Default value is `null` if not provided
      },
    },
    // Configuration object containing additional settings or data
    configData: {
      type: Object, // Expects an object
      required: true, // This prop must be provided
    },
    // Determines whether the item is eligible for collapsing all
    collapseAllEligibility: {
      type: Boolean, // Expects a boolean
      default: false, // Default value is `true`
    },
    // Determines whether the item is eligible for expanding all
    expandAllEligibility: {
      type: Boolean, // Expects a boolean
      default: false, // Default value is `true`
    },
    nodeItem: {
      type: Object,
      default: () => {},
    },
    transactionNodeTree: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    documentSortOrder() {
      return this.$store.getters['batch/documentSortOrder']
    },
    documentHideEmptyKeys: {
      get() {
        const settings = this.$store.getters['batch/hideEmptyAutoExtrationKeys']
        return settings?.[this.id] ?? true
      },
      set(value) {
        const current = this.$store.getters['batch/hideEmptyAutoExtrationKeys']
        const updated = { ...current, [this.id]: value }
        this.$store.commit('batch/SET_HIDE_EMPTY_AUTO_EXTRACTION_KEYS', updated)
      },
    },
    isCombineView: {
      get() {
        return this.$store.state.batch.isCombineView
      },
      set(value) {
        this.$store.commit('batch/SET_COMBINE_VIEW', value)
      },
    },
    localBadgeVariant() {
      const nodeItem = this.nodeItem || {}
      const nodeStatus = nodeItem.Status
      const isProfileKeyFound = nodeItem.isProfileKeyFound === true
      const isPureAutoextraction = nodeItem.isPureAutoextraction === true

      // ✅ If label  is block then label will be gray
      if (this.label.toLowerCase() === 'block') {
        return ''
      }
      if (isProfileKeyFound && nodeStatus === -1000) {
        return 'danger'
      }

      if (nodeStatus === -1) {
        return 'warning'
      }

      // ✅ If it's a vendor node, show 'success'
      if (nodeItem.type === 'vendor') {
        return 'dark'
      }

      if (nodeItem.notInUse) {
        return ''
      }

      if (nodeStatus === 1) {
        return 'success'
      }

      // ✅ If both profileKeyFound and autoextracted, show 'success'
      if (isProfileKeyFound && isPureAutoextraction) {
        return 'success'
      }

      // ✅ If neither profileKeyFound nor autoextracted, show ''
      if ((!isProfileKeyFound && !isPureAutoextraction)) {
        return ''
      }

      // Default badge variant
      return 'primary'
    },
    // Retrieves the main mode of the data view from the Vuex store
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    // Retrieves the batch mode from the Vuex store
    mode() {
      return this.$store.getters['batch/mode']
    },
    // Checks if the current batch is an Excel batch
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    // Retrieves the ID of the currently selected document
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },
    // Retrieves the editable node from the Vuex store
    editableNode() {
      return this.$store.getters['batch/editableNode']
    },
    // Checks if manual validation is enabled
    manualValidation() {
      return this.$store.getters['batch/manualValidation']
    },
    // Retrieves the verification status from the Vuex store
    verificationStatus() {
      return this.$store.getters['batch/verificationStatus']
    },
    // Retrieves detailed verification information
    verificationDetails() {
      return this.$store.getters['batch/verificationDetails']
    },
    getProfileDetails() {
      return this.$store.getters['batch/profileDetails']
    },
    batchId() {
      return this.$store.getters['batch/batch'].id
    },
    // profileKeys() {
    //   return this.$store.getters['batch/profileKeys']
    // },
    // findBatchAccuracy() {
    //   if (this.type !== 'batch' || !this.nodeItem.batchId) {
    //     return null
    //   }

    //   const documentsInBatch = this.transactionNodeTree.filter(node => node.type === 'document' && node.batchId === this.id)

    //   if (documentsInBatch.length === 0) return 0

    //   const documentAccuracies = documentsInBatch.map(doc => {
    //     if (!doc.allKeys || !this.profileKeys || this.profileKeys.length === 0) {
    //       return 0
    //     }

    //     const profileKeys = this.profileKeys.map(key => toCamelCase(key.keyLabel))
    //     const matchedKeys = profileKeys.filter(key => doc.allKeys.includes(toCamelCase(key)))
    //     return Math.round((matchedKeys.length / this.profileKeys.length) * 100)
    //   })

    //   const totalAccuracy = documentAccuracies.reduce((sum, acc) => sum + acc, 0)
    //   return Math.round(totalAccuracy / documentAccuracies.length)
    // },

    // Update your existing findAccuracy to handle both document and batch
    // findAccuracy() {
    //   if (this.type === 'batch') {
    //     return this.findBatchAccuracy
    //   }

    //   // Existing document accuracy calculation
    //   const profileKeys = this.profileKeys.map(key => toCamelCase(key.keyLabel))
    //   const matchedKeys = profileKeys.filter(key => this.nodeItem?.allKeys?.includes(toCamelCase(key)))
    //   const percentage = (matchedKeys.length / this.profileKeys.length) * 100
    //   return Math.round(percentage)
    // },
  },
  methods: {
    // Handles the click event on a node
    async clickHandler() {
      if (this.type === 'root') {
        if (this.expandAllEligibility && !this.collapseAllEligibility) {
          this.toExpandAll()
        } else if (this.collapseAllEligibility) {
          this.toCollapseAll()
        }
        return
      }

      // Dispatch an action to set the currently selected node ID in the Vuex store
      await this.$store.dispatch('batch/setSelectedNodeId', this.id)

      // Handle expandable nodes (toggle expand/collapse) - but skip for document nodes when batch will change
      // This prevents flickering when clicking documents that trigger batch changes
      if (this.expandable && this.type !== 'root' && this.type !== 'document') {
        // If the node is not expanded, expand it
        if (!this.expanded) {
          this.$store.commit('batch/EXPAND_NODE', this.id)
        } else {
          // Otherwise, collapse it
          this.$store.commit('batch/COLLAPSE_NODE', this.id)
        }
      }

      // Handle batch node clicks: switch to that batch (which auto-loads first document)
      if (this.type === 'batch') {
        const currentBatchId = this.$store.getters['batch/selectedBatchId']
        const batchIdFromNode = this.id // Batch ID is the node ID itself

        if (currentBatchId !== batchIdFromNode) {
          // Update route query parameter to trigger route watcher (like BatchSelector does)
          await this.$router.replace({
            name: this.$route.name,
            params: this.$route.params,
            query: {
              ...this.$route.query,
              'batch-id': batchIdFromNode,
            },
          })

          const currentMode = this.$store.getters['dataView/mainMode']
          if (currentMode === 'verification') {
            this.$store.commit('batch/SET_SELECTED_BATCH_ID', batchIdFromNode)
            const batch = this.$store.getters['batch/verificationDetails'].find(e => e.id === batchIdFromNode)
            if (batch) {
              const batchData = {
                id: batch.id,
                vendor: batch.vendor || batch.data_json?.Vendor || '',
                type: batch.document_types || batch.data_json?.DocumentType || '',
                nameMatchingText: batch.name_matching_text || batch.data_json?.NameMatchingText || 'test',
                definitionId: batch.profile || batch.data_json?.DefinitionID || '',
                mode: batch.mode || '',
                subPath: batch.sub_path || '',
                definitionVersion: batch.data_json?.definition_version || '1.0',
                isExcel: batch.data_json?.batch_type === '.xlsx',
                project: batch.data_json?.Project || '',
                isDatasetBatch: batch.is_dataset_batch || false,
              }
              this.$store.commit('batch/SET_BATCH', batchData)
              this.$store.commit('batch/SET_BATCH_NODES', [{ type: 'batch', id: batch.id, children: batch.data_json?.nodes || [] }])
              // Load first document in verification mode
              await this.$store.dispatch('batch/selectFirstDocument')
              await this.$store.dispatch('batch/loadDocumentData')
            }
          } else {
            // changeBatch automatically calls selectFirstDocument and loadDocumentData
            await this.$store.dispatch('batch/changeBatch', batchIdFromNode)
          }
          // Reset flag after a delay to allow route watcher to work again
          setTimeout(() => {
            if (this.$parent) {
              this.$parent.isClickHandling = false
            }
          }, 300)
        } else {
          // Same batch clicked - only update route if batch-id in query is different
          const currentRouteBatchId = this.$route.query['batch-id']
          if (currentRouteBatchId !== batchIdFromNode) {
            await this.$router.replace({
              name: this.$route.name,
              params: this.$route.params,
              query: {
                ...this.$route.query,
                'batch-id': batchIdFromNode,
              },
            })
          }

          // Ensure first document is loaded
          await this.$store.dispatch('batch/selectFirstDocument')
          await this.$store.dispatch('batch/loadDocumentData')

          if (this.$parent) {
            this.$parent.isClickHandling = false
          }
        }
        // Collapse grouped sections for clean UI
        const currentDocumentId = this.$store.getters['batch/selectedDocumentId']
        if (currentDocumentId) {
          const autoExtractionNodeId = `${currentDocumentId}.auto_extraction`
          const processKeysNodeId = `${currentDocumentId}.process_keys`
          this.$store.commit('batch/COLLAPSE_NODE', autoExtractionNodeId)
          this.$store.commit('batch/COLLAPSE_NODE', processKeysNodeId)
        }
      } else {
        // Handle document and sub-document node clicks: always resolve the target document
        // Prefer the canonical document id provided by flatNode builder
        const resolvedDocumentId = this.nodeItem?.documentId
          || (() => {
            // Fallback: derive from this.id assuming first two parts are batch
            const parts = (this.id || '').split('.')
            if (parts.length >= 3) return `${parts[0]}.${parts[1]}.${parts[2]}`
            return null
          })()

        if (resolvedDocumentId) {
          const currentMode = this.$store.getters['dataView/mainMode']
          const currentBatchId = this.$store.getters['batch/selectedBatchId']
          const batchIdFromNode = this.nodeItem?.currentBatchId
            || resolvedDocumentId.split('.').slice(0, 2).join('.')

          // Check if batch will change - if so, don't toggle expand/collapse to avoid flicker
          const batchWillChange = currentBatchId !== batchIdFromNode

          // Only toggle expand/collapse if batch won't change (to avoid conflict with route watcher)
          if (!batchWillChange && this.expandable && this.type !== 'root') {
            // If the node is not expanded, expand it
            if (!this.expanded) {
              this.$store.commit('batch/EXPAND_NODE', this.id) // Commit a Vuex mutation to expand the node
            } else {
              // Otherwise, collapse it
              this.$store.commit('batch/COLLAPSE_NODE', this.id) // Commit a Vuex mutation to collapse the node
            }
          }

          // If clicking a document from a different batch, switch batch first
          // Set flag to prevent route watcher from running during click
          if (batchWillChange) {
            // Set flag in parent to prevent route watcher
            if (this.$parent && this.$parent.$set) {
              this.$parent.$set(this.$parent, 'isClickHandling', true)
            }

            if (currentMode === 'verification') {
              this.$store.commit('batch/SET_SELECTED_BATCH_ID', batchIdFromNode)
              const batch = this.$store.getters['batch/verificationDetails'].find(e => e.id === batchIdFromNode)
              if (batch) {
                const batchData = {
                  id: batch.id,
                  vendor: batch.vendor || batch.data_json?.Vendor || '',
                  type: batch.document_types || batch.data_json?.DocumentType || '',
                  nameMatchingText: batch.name_matching_text || batch.data_json?.NameMatchingText || 'test',
                  definitionId: batch.profile || batch.data_json?.DefinitionID || '',
                  mode: batch.mode || '',
                  subPath: batch.sub_path || '',
                  definitionVersion: batch.data_json?.definition_version || '1.0',
                  isExcel: batch.data_json?.batch_type === '.xlsx',
                  project: batch.data_json?.Project || '',
                  isDatasetBatch: batch.is_dataset_batch || false,
                }
                this.$store.commit('batch/SET_BATCH', batchData)
                this.$store.commit('batch/SET_BATCH_NODES', [{ type: 'batch', id: batch.id, children: batch.data_json?.nodes || [] }])
              }
            } else {
              await this.$store.dispatch('batch/changeBatch', batchIdFromNode)
            }

            // Manually expand nodes since route watcher is disabled
            this.$nextTick(() => {
              if (this.$parent && this.$parent.expandNodeByBatchId) {
                this.$parent.expandNodeByBatchId(batchIdFromNode)
              }

              // Reset flag after expansion completes
              setTimeout(() => {
                if (this.$parent && this.$parent.$set) {
                  this.$parent.$set(this.$parent, 'isClickHandling', false)
                }
              }, 400)
            })
          }

          // Update selected document if different
          const currentDocumentId = this.$store.getters['batch/selectedDocumentId']
          if (currentDocumentId !== resolvedDocumentId) {
            // Only reload document data if we're switching to a different document
            this.$store.commit('batch/SET_SELECTED_DOCUMENT_ID', resolvedDocumentId)
            await this.$store.dispatch('batch/loadDocumentData')

            // Don't collapse grouped sections if batch changed - let route watcher handle expansion
            // Only collapse if we're staying on the same batch (to avoid flicker with route watcher)
            if (!batchWillChange) {
              // Collapse grouped sections for the selected document (keep UI focused)
              // Only do this when batch didn't change to avoid conflict with route watcher expansion
              const autoExtractionNodeId = `${resolvedDocumentId}.auto_extraction`
              const processKeysNodeId = `${resolvedDocumentId}.process_keys`
              this.$store.commit('batch/COLLAPSE_NODE', autoExtractionNodeId)
              this.$store.commit('batch/COLLAPSE_NODE', processKeysNodeId)
            }
          }
          // If clicking on sub-sections of the same document, just update selected node (already done above)
          // No need to reload document data
        }
      }

      // Perform actions based on the node type
      if (this.type === 'table') {
        // If the type is "table", set the view to "table" in the Vuex store
        this.$store.commit('batch/SET_VIEW', 'table')
      } else if (this.isExcelBatch) {
        // If the batch is an Excel batch, emit an event to go to the selected node cell
        bus.$emit('goToSelectedNodeCell')
      } else {
        // Otherwise, emit an event to scroll to the highlighted node
        this.$nextTick(() => {
          bus.$emit('scrollToHighlightedNode')
        })
      }
    },

    // Handles the double-click event on a node
    async dbClickHandler() {
      // Prevent further action if conditions are not met (e.g., wrong mode, non-expandable node, etc.)
      if (this.mainMode !== 'verification' || this.expandable || this.verificationStatus !== 'ready' || !this.manualValidation) {
        return
      }

      // Dispatch an action to set the node as editable in the Vuex store
      await this.$store.dispatch('batch/setEditableNode', { id: this.id, v: this.title })
    },

    // Emits an event to collapse all nodes
    toCollapseAll() {
      this.$emit('to-collapse-all') // Emit a custom event to notify the parent component
    },

    // Emits an event to expand all nodes
    toExpandAll() {
      this.$emit('to-expand-all') // Emit a custom event to notify the parent component
    },
  },
}
</script>

<style lang="scss" scoped>
.node {
    border: 1px solid #ebe9f1;
    border-radius: 5px;
    padding: 5px;
    margin-bottom: 5px;
    cursor: pointer;

    &.highlighted {
        border: 2px solid red !important;
    }

    &.search-match {
        border: 2px solid orange !important;
    }

    &.highlighted.search-match {
        border: 2px solid #d37523 !important;
    }
}

.dark-layout .node {
    border-color:#3b4253;
}
</style>
