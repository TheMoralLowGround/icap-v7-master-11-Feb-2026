<!--
 Organization: AIDocbuilder Inc.
 File: imageViewToolbar.vue
 Version: 1.0

 Authors:
   - Initial implementation: Ali

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   The imageViewToolbar.vue component serves as a versatile toolbar for the
   image viewer area in the application. It dynamically adjusts its content
   based on the current mode, viewer context, and batch state, providing tools
   for navigating, interacting with, and managing document pages and metadata.

 Dependencies:
   - Vue: JavaScript framework for building UI.
   - BootstrapVue: Provides directives like tooltips.
   - Vuex: Manages state for batch data, lookup initialization, and viewer settings.
   - Various toolbar subcomponents: Zoom, Selectors, Batch Status, and more.

 Main Features:
   - Displays loading progress for pages, dynamically showing loaded and total file counts.
   - Includes selectors for definitions, batches, and documents, adjusted for the current mode.
   - Offers tools like zooming, fit-to-width, and selector functionalities for the image viewer.
   - Integrates timeline and batch status components for better tracking and state visualization.
   - Provides query tools, data import/export options, and custom template creation in specific contexts.
   - Adapts visibility of elements based on the main mode, viewer content, and route.

 Core Components:
   - `<zoom-in>` and `<zoom-out>`: Tools for zooming the image viewer.
   - `<batch-selector>` and `<document-selector>`: Dropdowns for selecting batches and documents.
   - `<view-selector>`: Allows users to switch views within the image viewer.
   - `<timeline>`: Displays historical changes related to the current batch.
   - `<clear-anchor-highlights>`: Clears highlights for key anchors in the document.

 Notes:
   - Props `imageViewerAreaContent`, `loadedFiles`, and `totalFiles` control the loading state and determine displayed elements.
   - Computed properties interact with Vuex to retrieve dynamic states like `batchId`, `manualValidation`, and `verificationStatus`.
   - The toolbar ensures seamless functionality across multiple modes, such as 'verification', 'query-results', and standard viewing.
-->

<template>
  <!-- Main container with flexbox styling for layout -->
  <div
    class="d-flex justify-content-end align-items-center wrapper"
    style="position: relative;"
  >
    <!-- Show a loader section when pages are still loading -->
    <template v-if="isPageLoading">
      <div
        class="d-flex align-items-center flex-grow-1 doc-load"
      >
        <!-- Display the number of loaded pages out of the total -->
        <span
          class="font-weight-bold"
        >
          Loaded Pages: {{ loadedFiles }} / {{ totalFiles }}
        </span>
      </div>
    </template>

    <!-- Wrapper for various selectors and tools -->
    <div class="d-flex wrapper flex-grow-1 font-0-95">
      <!-- Placeholder for a definition selector, currently disabled -->
      <div
        v-if="false"
        class="definition-selector-wrapper"
      >
        <definition-selector />
      </div>

      <!-- Placeholder for a definition type selector, currently disabled -->
      <div
        v-if="false"
        class="definition-type-selector-wrapper"
      >
        <definition-type-selector />
      </div>

      <!-- Batch selector, displayed only when imageViewerAreaContent is 'image-viewer' -->
      <div class="batch-selector-wrapper">
        <batch-selector />
      </div>

      <!-- Always display document selector -->
      <div class="document-selector-wrapper">
        <document-selector />
      </div>

      <!-- Definition version selector, hidden in verification mode -->
      <div
        v-if="mainMode !== 'verification'"
        class="definition-version-selector-wrapper"
      >
        <definition-version-selector />
      </div>

      <div
        v-if="!templatesRoute && mainMode !== 'verification' && batch.view !== 'table'"
        class="my-auto"
      >
        <PopoverTestOptions />
      </div>
    </div>

    <!-- Show query result selectors and search tools if content is 'query-results' -->
    <template v-if="imageViewerAreaContent === 'query-results'">
      <div class="query-result-selector font-0-95">
        <query-result-selector />
      </div>
      <div class="query-result-search font-0-95">
        <query-result-search />
      </div>
    </template>

    <!-- Additional tools for query results, only shown if lookup is initialized -->
    <template v-if="lookupInitialized && imageViewerAreaContent === 'query-results'">
      <div>
        <download-data />
      </div>
      <div>
        <import-data />
      </div>
      <div>
        <add-record />
      </div>
    </template>

    <div v-if="undoKeyMappingData && mainMode !== 'verification' && batch.view !== 'table'">
      <undo-key-mapping
        @click="showUndoConfirmationModal = true"
      />
    </div>

    <div
      v-if=" !templatesRoute && mainMode !== 'verification' && batch.view !== 'table'"
      class="d-flex align-items-center"
    >
      <Popover>
        <div>
          <b-form-checkbox
            v-model="showBottomPanel"
            v-b-tooltip.hover
            switch
            :disabled="batch.view === 'table'"
          >
            <!-- :title="showBottomPanel ? 'Hide Keys Panel' : 'Show Keys Panel'" -->
            View Keys Panel
          </b-form-checkbox>
        </div>
      </Popover>
    </div>

    <!-- Create template option, hidden for templatesRoute or in verification/query-results modes -->
    <div v-if="!templatesRoute && mainMode !== 'verification' && imageViewerAreaContent !== 'query-results'">
      <create-template />
    </div>

    <!-- Copy definition data option, hidden in verification/query-results modes -->
    <div v-if="mainMode !== 'verification' && imageViewerAreaContent !== 'query-results'">
      <copy-definition-data />
    </div>
    <!-- <div>
        <save-config />
      </div> -->
    <!-- <div>
        <highlight-root-nodes />
      </div> -->

    <!-- Image viewer tools like zoom and selector -->
    <template v-if="imageViewerAreaContent === 'image-viewer' || isExcelBatch">
      <div v-if="mainMode !== 'verification'">
        <zoom-in />
      </div>
      <div v-if="mainMode !== 'verification'">
        <zoom-out />
      </div>
      <!-- Fit-to-width option, not available in 'analyzer' view -->
      <div v-if="view !== 'analyzer' && mainMode !== 'verification'">
        <fit-to-width />
      </div>
      <!-- Selector tool, hidden in verification mode -->
      <div v-if="mainMode !== 'verification'">
        <selector />
      </div>
    </template>

    <!-- View selector, hidden in 'analyzer' view -->
    <div
      v-if="view !== 'analyzer'"
      class="view-selector-wrapper"
    >
      <view-selector :image-viewer-area-content="imageViewerAreaContent" />
    </div>
    <!-- <template v-if="view === 'analyzer'">
      <div v-if="!isExcelBatch">
        <highlight-key-blocks />
      </div>
      <div v-if="!isExcelBatch">
        <measure />
      </div>
      <div>
        <download-docbuilder-payload />
      </div>
    </template> -->
    <div v-if="mainMode !== 'verification'">
      <timeline
        :batch-id="batchId"
        placement="bottom"
        icon-size="20"
        auto-initialize
      />
    </div>
    <!-- Download Extraction Data Button -->
    <div v-if="mainMode !== 'verification'">
      <feather-icon
        v-b-tooltip.hover
        icon="DownloadIcon"
        size="20"
        title="Download Extraction Data"
        class="cursor-pointer"
        @click="$emit('download-extraction-data')"
      />
    </div>
    <!-- <div class="mode-selector-wrapper">
      <mode-selector />
    </div> -->

    <!-- Clear anchor highlights tool -->
    <div v-if="displayKeyAnchors">
      <clear-anchor-highlights />
    </div>

    <!-- Batch status display, hidden in verification mode -->
    <div v-if="mainMode !== 'verification'">
      <batch-status />
    </div>

    <!-- Verification actions, displayed only when in verification mode and ready status -->
    <div v-if="mainMode === 'verification' && verificationStatus === 'ready' && manualValidation">
      <verification-actions />
    </div>
    <!-- <div class="flex-grow-1" /> -->
    <!-- <div>
      <submit-definition-data />
    </div> -->
    <confirm-key-mapping
      v-if="showUndoConfirmationModal"
      undo
      :dragged-item-lable="undoKeyMappingData ? undoKeyMappingData.draggedItem.label : ''"
      :drop-target-label="undoKeyMappingData ? undoKeyMappingData.targetedItem.item.label : ''"
      @confirmed="confirmUndoKeyMapping()"
      @modal-closed="showUndoConfirmationModal = false"
      @cancel="showUndoConfirmationModal = false"
      @close="showUndoConfirmationModal = false"
    />
  </div>
</template>

<script>
import { VBTooltip, BFormCheckbox } from 'bootstrap-vue'
import { mapState } from 'vuex'
// import SaveConfig from './SaveConfig.vue'
// import HighlightRootNodes from './HighlightRootNodes.vue'
import bus from '@/bus'
import ZoomIn from '@/components/Batch/ImageViewToolbar/ZoomIn.vue'
import ZoomOut from '@/components/Batch/ImageViewToolbar/ZoomOut.vue'
import Selector from '@/components/Batch/ImageViewToolbar/Selector.vue'
// import Measure from './Measure.vue'
import FitToWidth from '@/components/Batch/ImageViewToolbar/FitToWidth.vue'
import ViewSelector from '@/components/Batch/ImageViewToolbar/ViewSelector.vue'
import VerificationActions from '@/components/Batch/ImageViewToolbar/VerificationActions.vue'
// import ModeSelector from './ModeSelector.vue'
import Timeline from '@/components/UI/Timeline/Timeline.vue'
import BatchStatus from '@/components/Batch/ImageViewToolbar/BatchStatus.vue'
// import SubmitDefinitionData from './SubmitDefinitionData.vue'
// import HighlightKeyBlocks from './HighlightKeyBlocks.vue'
import ClearAnchorHighlights from '@/components/Batch/ImageViewToolbar/ClearAnchorHighlights.vue'
// import DownloadDocbuilderPayload from './DownloadDocbuilderPayload.vue'
import CopyDefinitionData from '@/components/Batch/ImageViewToolbar/CopyDefinitionData/CopyDefinitionData.vue'
import CreateTemplate from '@/components/Batch/ImageViewToolbar/CreateTemplate/CreateTemplate.vue'

import UndoKeyMapping from '@/components/Batch/ImageViewToolbar/UndoKeyMapping.vue'
import ConfirmKeyMapping from '@/components/UI/ConfirmKeyMapping.vue'

import ImportData from '@/components/Batch/ImageViewToolbar/Lookup/ImportDataOption.vue'
import DownloadData from '@/components/Batch/ImageViewToolbar/Lookup/DownloadDataOption.vue'
import AddRecord from '@/components/Batch/ImageViewToolbar/Lookup/AddRecordOption.vue'

import DefinitionSelector from '@/components/Batch/SelectorToolbar/DefinitionSelector.vue'
import DefinitionTypeSelector from '@/components/Batch/SelectorToolbar/DefinitionTypeSelector.vue'
import BatchSelector from '@/components/Batch/SelectorToolbar/BatchSelector.vue'
import DocumentSelector from '@/components/Batch/SelectorToolbar/DocumentSelector.vue'
import DefinitionVersionSelector from '@/components/Batch/SelectorToolbar/DefinitionVersionSelector.vue'

import QueryResultSelector from '@/components/Batch/SelectorToolbar/Lookup/QueryResultSelector.vue'
import QueryResultSearch from '@/components/Batch/SelectorToolbar/Lookup/QueryResultSearch.vue'
import Popover from './Popover.vue'
import PopoverTestOptions from './PopoverTestOptions.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    // SaveConfig,
    BFormCheckbox,
    ZoomIn,
    ZoomOut,
    Selector,
    FitToWidth,
    ViewSelector,
    VerificationActions,
    // ModeSelector,
    Timeline,
    BatchStatus,
    // SubmitDefinitionData,
    // HighlightKeyBlocks,
    // Measure,
    ClearAnchorHighlights,
    // DownloadDocbuilderPayload,
    CopyDefinitionData,
    ImportData,
    DownloadData,
    AddRecord,
    DefinitionSelector,
    DefinitionTypeSelector,
    BatchSelector,
    DocumentSelector,
    DefinitionVersionSelector,
    QueryResultSelector,
    QueryResultSearch,
    CreateTemplate,
    Popover,
    PopoverTestOptions,
    UndoKeyMapping,
    ConfirmKeyMapping,
  },
  props: {
    // Property to determine the content type of the image viewer area
    imageViewerAreaContent: {
      type: String, // Must be a string
      required: true, // This prop is mandatory
    },
    // Tracks the number of files currently loaded
    loadedFiles: {
      type: Number, // Must be a number
      default: 0, // Defaults to 0 if not provided
    },
    // Total number of files to be loaded
    totalFiles: {
      type: Number, // Must be a number
      default: 0, // Defaults to 0 if not provided
    },
  },
  data() {
    return {
      showUndoConfirmationModal: false,
      downloadingJson: false,
      downloadingExtractionData: false,
    }
  },
  computed: {
    ...mapState(['batch']),
    // isAutoExtractedKeys: {
    //   get() {
    //     return this.$store.getters['dataView/getAutoExtractedKeys']
    //   },
    //   set(value) {
    //     this.$store.commit('dataView/AUTO_EXTRACTED_KEY', value)
    //   },
    // },
    showBottomPanel: {
      get() {
        return this.$store.state.batch.showBottomPanel
      },
      set(value) {
        this.$store.commit('batch/SET_SHOW_BOTTOM_PANEL', value)
      },
    },
    // Determines if the current route is the template batch view
    templatesRoute() {
      return this.$route.name === 'template-batch'
    },
    // Retrieves the current batch ID from the Vuex store
    batchId() {
      return this.$store.getters['batch/batch'].id
    },
    // Checks if manual validation is enabled for the current batch
    manualValidation() {
      return this.$store.getters['batch/manualValidation']
    },
    // Retrieves the verification status of the batch
    verificationStatus() {
      return this.$store.getters['batch/verificationStatus']
    },
    // Determines the main mode of the application (e.g., 'verification', 'editing')
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    // Gets the current view type of the batch (e.g., 'analyzer', 'viewer')
    view() {
      return this.$store.getters['batch/view']
    },
    // Checks if key anchors should be displayed
    displayKeyAnchors() {
      return this.$store.getters['batch/displayKeyAnchors']
    },
    // Retrieves the mode of the data view (e.g., 'table', 'form')
    dataViewMode() {
      return this.$store.getters['dataView/mode']
    },
    // Checks if the lookup module is initialized
    lookupInitialized() {
      return this.$store.getters['lookup/initialized']
    },
    // Checks if the current batch is an Excel batch
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    // Determines if pages are still being loaded based on total and loaded files
    isPageLoading() {
      return this.totalFiles && this.loadedFiles < this.totalFiles
    },
    undoKeyMappingData() {
      return this.$store.getters['batch/undoKeyMappingData']
    },
  },
  methods: {
    confirmUndoKeyMapping() {
      this.showUndoConfirmationModal = false
      bus.$emit('batch/undoKeyMapping')
    },
  },
}
</script>

<style scoped lang="scss">
.font-0-95 {
  font-size: 0.90rem !important;
  input {
    font-size: 0.90rem !important;
    height: 2.5rem;
  }
}
.wrapper {
  column-gap: .65rem !important;
}
.mode-selector-wrapper {
  flex-basis: 149px;
}
.mode-selector-wrapper {
  flex-basis: 149px;
}
.definition-selector-wrapper {
  flex-basis: 178px;
}
.definition-type-selector-wrapper, .batch-selector-wrapper {
  min-width: 187px;
}
.document-selector-wrapper {
  min-width: 186px;
}
.definition-version-selector-wrapper {
  min-width: 89px;
}
.query-result-selector {
  min-width: 162px;
}
.query-result-search {
  min-width: 155px;
}
.doc-load {
  position: absolute;
  top: 4rem;
  left: 10px;
  z-index: 2;
  font-weight: 700;
}
</style>
