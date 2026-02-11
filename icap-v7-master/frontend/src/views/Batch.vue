<template>
  <div class="batch-page">
    <h4 class="m-50">
      {{ pageTitle }}
    </h4>
    <div
      v-if="loading"
      class="text-center"
    >
      <b-spinner
        variant="primary"
      />
    </div>

    <!-- Alert to display errors -->
    <b-alert
      variant="danger"
      :show="!loading && error ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ error }}
        </p>
      </div>
    </b-alert>

    <!-- Display errors -->
    <div
      v-if="!loading && !error"
      :class="{ 'verification-box': dataViewMode === 'verification', 'box-extend': togoleNavbar, 'box': !togoleNavbar }"
    >
      <div
        v-if="dataViewMode !== 'verification' && false"
        style="margin: 0.5rem 0.5rem 1rem 0.5rem"
      >
        <selector-toolbar :image-viewer-area-content="imageViewerAreaContent" />
      </div>
      <splitpanes
        class="default-theme"
      >
        <pane
          v-if="['key', 'explore-lookup'].includes(view)"
          :size="panelSizes.leftPaneSize"
        >
          <b-card
            class="mb-0"
            style="height:100%"
          >
            <div class="node-tree-conent d-flex flex-column">
              <div>
              <!-- <node-tree-toolbar /> -->
              </div>
              <!-- <div class="separator" /> -->
              <div class="flex-grow-1">
                <batch-node-tree />
              </div>
            </div>
          </b-card>
        </pane>
        <pane :size="100 - panelSizes.leftPaneSize">
          <splitpanes
            class="default-theme"
            horizontal
            @resize="updatePanelSizes"
          >
            <pane
              ref="rightTopPane"
              :size="shouldShowBottomPane ? panelSizes.rightTopPaneSize : 100"
            >
              <b-card
                class="mb-0"
                style="height:100%"
              >
                <div
                  v-if="batch"
                  class="section-content"
                >
                  <div class="image-viewer-conent d-flex flex-column">
                    <div>
                      <image-view-toolbar
                        :image-viewer-area-content="imageViewerAreaContent"
                        :loaded-files="loadedFiles"
                        :total-files="totalFiles"
                        @download-extraction-data="downloadExtractionData"
                      />
                    </div>
                    <div class="separator" />
                    <div class="flex-grow-1">
                      <!-- Using v-show below (instead of v-if) for image-viewer and excel-viewer to prevent re-creation (Expensive operation) of components when switching back from query-results view
                          v-if is used (along with v-show) to control when that component should initialzed and when not.
                          i.e. excel viewer should not be rendered/initialized in case of pdf batch -->
                      <image-viewer
                        v-if="!isExcelBatch"
                        v-show="imageViewerAreaContent === 'image-viewer'"
                        @calculate-loaded-files="onCalculateLoadedFiles"
                      />
                      <excel-viewer
                        v-if="isExcelBatch"
                        v-show="imageViewerAreaContent === 'excel-viewer'"
                      />
                      <query-results
                        v-if="imageViewerAreaContent === 'query-results'"
                      />
                    </div>
                  </div>
                </div>
              </b-card>
            </pane>
            <pane
              v-if="shouldShowBottomPane"
              :size="100 - panelSizes.rightTopPaneSize"
            >
              <b-card
                class="mb-0"
                style="height:100%"
              >
                <div class="section-content">
                  <div
                    class="image-viewer-conent d-flex flex-column"
                  >
                    <template v-if="view === 'analyzer' || (!dataViewerLoading && !dataViewerLoadingError)">
                      <div>
                        <data-view-toolbar />
                      </div>
                      <div class="separator" />
                    </template>
                    <div class="flex-grow-1">
                      <data-viewer />
                    </div>
                  </div>
                </div>
              </b-card>
            </pane>
          </splitpanes>
        </pane>
      </splitpanes>
    </div>

    <!-- Record form component to display batch -->
    <record-form
      v-if="addRecordToDB"
      :is-edit="false"
      :default-record="addRecordData.record"
      :default-table-name="addRecordData.tableName"
      @modal-closed="closeAddRecordForm"
    />

  </div>
</template>

<script>
import axios from 'axios'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import {
  BCard, BSpinner, BAlert,
} from 'bootstrap-vue'

import BatchNodeTree from '@/components/Batch/BatchNodeTree/BatchNodeTree.vue'
import ImageViewer from '@/components/Batch/ImageViewer/ImageViewer.vue'
import ExcelViewer from '@/components/Batch/ExcelViewer/ExcelViewer.vue'
// import NodeTreeToolbar from '@/components/Batch/NodeTreeToolbar/NodeTreeToolbar.vue'
import ImageViewToolbar from '@/components/Batch/ImageViewToolbar/ImageViewToolbar.vue'
import SelectorToolbar from '@/components/Batch/SelectorToolbar/SelectorToolbar.vue'
import DataViewer from '@/components/Batch/DataViewer/DataViewer.vue'
import DataViewToolbar from '@/components/Batch/DataViewToolbar/DataViewToolbar.vue'
import QueryResults from '@/components/Lookup/QueryResults/QueryResults.vue'
import RecordForm from '@/components/Lookup/RecordForm.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import bus from '@/bus'
import WS from '@/utils/ws'

export default {
  components: {
    BCard,
    BSpinner,
    BAlert,
    BatchNodeTree,
    ImageViewer,
    ExcelViewer,
    // NodeTreeToolbar,
    ImageViewToolbar,
    SelectorToolbar,
    DataViewer,
    DataViewToolbar,
    Splitpanes,
    Pane,
    QueryResults,
    RecordForm,
  },
  data() {
    return {
      id: this.$route.params.id, // Batch ID derived from the current route's parameters.
      loading: true, // Loading state for the component, e.g., during initialization.
      connection: null, // Stores WebSocket or other connection details.
      panelSizes: { // Sizes for resizable panels in the layout.
        leftPaneSize: 0,
        rightTopPaneSize: 0,
      },
      addRecordToDB: false, // Flag to indicate whether a new record is being added to the database.
      addRecordData: null, // Holds data for the record being added to the database.
      loadedFiles: 0, // Tracks the number of files successfully loaded.
      totalFiles: 0, // Total number of files expected to load.
      togoleNavbar: false, // Toggle state for showing or hiding the navigation bar.
      blinkInterval: null,
    }
  },
  computed: {
    // Retrieves the current batch data from Vuex store.
    batch() {
      return this.$store.getters['batch/batch']
    },
    selectedBatchId() {
      return this.$store.getters['batch/selectedBatchId']
    },
    selectedDocument() {
      return this.$store.getters['batch/selectedDocument']
    },
    showBottomPanel() {
      return this.$store.getters['batch/showBottomPanel']
    },
    shouldShowBottomPane() {
      return (this.dataViewMode !== 'verification' && (this.view !== 'table' && this.showBottomPanel))
      || this.view === 'table' || this.view === 'chunk-data'
    },
    flatNodes() {
      return this.$store.getters['batch/flatNodes']
    },
    // Retrieves selected project countries from the store.
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    // Gets the name of the current route.
    currentRouteName() {
      return this.$route.name
    },
    // Current view mode of the batch (e.g., 'analyzer', 'table').
    view() {
      return this.$store.getters['batch/view']
    },
    // Retrieves the batch mode (e.g., 'edit', 'view').
    mode() {
      return this.$store.getters['batch/mode']
    },
    // Retrieves the current data viewer mode (e.g., 'key-lookup').
    dataViewMode() {
      return this.$store.getters['dataView/mode']
    },
    // Gets the current status of the batch (e.g., 'loading', 'completed').
    status() {
      return this.$store.getters['batch/status']?.status
    },
    // Indicates if the data viewer is in a loading state.
    dataViewerLoading() {
      return this.$store.getters['dataView/loading']
    },
    error: {
      // Retrieves error information for the batch.
      get() {
        return this.$store.getters['batch/error']
      },
      // Sets a new error state for the batch in the store.
      set(value) {
        this.$store.commit('batch/SET_ERROR', value)
      },
    },
    // Indicates if there was an error loading the data viewer.
    dataViewerLoadingError() {
      return this.$store.getters['dataView/loadingError']
    },
    // Retrieves the default version of the definition from settings.
    defaultDefinitionVersion() {
      return this.$store.getters['applicationSettings/defaultDefinitionVersion']
    },
    // Checks if the current batch is an Excel batch.
    isExcelBatch() {
      return this.$store.getters['batch/batch']?.isExcel
    },
    // Determines the content to display in the image viewer area.
    imageViewerAreaContent() {
      let content = 'image-viewer'

      if (this.dataViewMode === 'key-lookup' || this.dataViewMode === 'table-lookup' || this.view === 'explore-lookup') {
        content = 'query-results'
      } else if (this.isExcelBatch) {
        content = 'excel-viewer'
      }
      return content
    },
    // Retrieves the project associated with the batch.
    batchProject() {
      return this.$store.getters['batch/batch']?.project
    },
    // Gets the selected definition for the current data view.
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition']
    },
    // Constructs the page title based on the current batch and view context.
    pageTitle() {
      if (!this.batch) return ''
      if (this.currentRouteName === 'verification') {
        return `Validate Transaction - ${this.id || ''}`
      }
      let title = ''
      const { batchProject, selectedDefinition } = this
      title = `Batch - ${this.batch?.id || ''}`

      if (batchProject) {
        title += ` | ${batchProject}`
      }

      if (this.currentRouteName === 'template-batch') {
        return `${title} | ${this.batch?.definitionId}`
      }

      if (selectedDefinition) {
        title += ` | ${this.batch?.definitionId} ${this.batch?.vendor ? '-' : ''}  ${this.batch?.vendor ?? ''} ${this.batch?.type ? '-' : ''}  ${this.batch?.type}`
      }

      if (selectedDefinition && selectedDefinition.type_seq_no) {
        title += ` ${selectedDefinition.type_seq_no}`
      }

      return title
    },
    // Retrieves the ID of the currently selected document.
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },
    scrollToPos() {
      return this.$store.getters['batch/scrollToPos']
    },
  },
  watch: {
    loadedFiles(newVal) {
      if (!this.scrollToPos || this.totalFiles === 0 || this.totalFiles !== newVal) {
        return
      }

      if (this.scrollToPos.documentId !== this.selectedDocumentId) return

      setTimeout(() => {
        bus.$emit('scrollToPos', this.scrollToPos)
        this.$store.commit('batch/SET_SCROLL_TO_POS', null)
      }, 500)
    },
    shouldShowBottomPane() {
      this.setPanelSizes()
      this.$nextTick(() => {
        if (this.$refs.rightTopPane) {
          this.$refs.rightTopPane.update()
        }
      })
    },
    // Monitor route changes and update view state accordingly
    currentRouteName(newVal, oldVal) {
      // Switch to 'analyzer' view and display additional fields when navigating to 'automated-table-model'
      if (newVal === 'automated-table-model') {
        this.$store.commit('batch/SET_VIEW', 'analyzer')
        this.$store.commit('dataView/SET_DISPLAY_NOT_IN_USE_FIELDS', true)

        // Ensure the route has the transaction ID parameter
        if (!this.$route.params.id && this.id) {
          this.$router.replace({
            name: 'automated-table-model',
            params: { id: this.id },
          })
        }
      }

      // Revert view to 'table' when returning to 'batch' from 'automated-table-model'
      if (newVal === 'batch' && oldVal === 'automated-table-model') {
        this.$store.commit('batch/SET_VIEW', 'table')
      }
    },

    // Handle changes in the batch object
    // selectedBatchId: {
    //   async handler(newVal, oldVal) {
    //     const transactionId = this.$route.params.id

    //     // Prevent navigation when the batch ID remains the same, or the current view/route does not require changes
    //     if (!oldVal || oldVal.id === newVal.id || this.view === 'analyzer' || this.currentRouteName === 'verification') {
    //       return
    //     }

    //     // Both conditions must be met: transaction-type is 'training' AND transactionId starts with 'multi_'
    //     // multi_ check is mandatory - without it no further action should be taken
    //     if (this.$route.query['transaction-type'] === 'training' && transactionId && transactionId.startsWith('multi_')) {
    //       // Update route with the new batch ID, preserving existing query parameters
    //       this.$router.replace({
    //         name: this.currentRouteName,
    //         query: {
    //           ...this.$route.query, // Preserve all existing query parameters
    //           'link-batch-id': this.selectedBatchId, // Update only the link-batch-id
    //         },
    //       })

    //       // Call API to fetch updated batch data after route change
    //       await this.$store.dispatch('batch/fetchBatch', transactionId)
    //     }
    //   },
    // },

    // React to changes in the view mode
    view(newVal, oldVal) {
    // Reset editable and selected nodes in the batch
      this.$store.dispatch('batch/setSelectedNodeId', null)
      this.$store.dispatch('batch/setEditableNode', null)

      // Automatically select the first mode unless in 'verification' route
      if (this.currentRouteName !== 'verification') {
        this.$store.dispatch('dataView/selectFirstMode')
      }

      // Adjust panel sizes for the new view
      this.setPanelSizes()

      // Clear lookup result data if leaving the 'explore-lookup' view
      if (oldVal === 'explore-lookup') {
        this.$store.dispatch('lookup/resetResultData')
      }
    },

    // Handle changes in data view mode
    dataViewMode(newVal, oldVal) {
      // Reset lookup data when transitioning away from 'key-lookup'
      if (oldVal === 'key-lookup' || oldVal === 'table-lookup') {
        this.$store.dispatch('lookup/resetResultData')
      }
    },

    // Monitor batch status for specific transitions (e.g., completion or failure)
    status: {
      async handler(newVal, oldVal) {
        if (['completed', 'failed'].includes(this.status)) {
          // Stop loading indicator and refresh batch data when status changes
          this.$store.commit('dataView/SET_LOADING', false)

          if (oldVal) {
            this.$store.dispatch('batch/refreshBatchData')
            // this.toExpandAll()
          }
        }
      },
      deep: true,
    },

    // Update page title whenever it changes
    pageTitle() {
      this.setPageTitle()
    },

    // Reset file counters when the selected document ID changes
    selectedDocumentId: {
      deep: true,
      handler() {
        this.loadedFiles = 0
        this.totalFiles = 0
      },
    },
  },

  // Lifecycle hook: Component creation
  created() {
    this.$store.commit('batch/SET_TRANSACTION_TYPE', this.$route.query['transaction-type'])
    this.$store.commit('batch/SET_TRAINING_LINK_BATCH_ID', this.$route.query['link-batch-id'])

    // Check for batch-id query parameter to select specific sub-batch
    const batchIdFromQuery = this.$route.query['batch-id']
    if (batchIdFromQuery) {
      this.$store.commit('batch/SET_SELECTED_BATCH_ID', batchIdFromQuery)
    }

    const routeId = this.$route.params.id

    this.$store.commit('dataView/SET_ROUTE_ID', routeId)
    // Initial setup based on the current route
    if (this.currentRouteName === 'automated-table-model') {
      this.$store.commit('batch/SET_VIEW', 'analyzer')
    }

    if (this.currentRouteName === 'verification') {
      this.initBatchForVerification()

      return
    }

    // General initialization for batch processing
    this.initBatch()

    // Set up event listeners
    bus.$on('wsData/batchStatus', this.onBatchStatus)
    bus.$on('lookup/displayAddRecordForm', this.displayAddRecordForm)
    bus.$on('toggle-navbar', this.gettogoleNavbar)

    // Initial view setup
    this.$store.dispatch('dataView/selectFirstMode')
    this.setPanelSizes()
    this.setPageTitle()
  },
  mounted() {
    this.blinkInterval = setInterval(() => {
      this.$store.state.batch.isAgentBlink = !this.$store.state.batch.isAgentBlink
    }, 600)
  },
  beforeDestroy() {
    // Clear blinking interval
    if (this.blinkInterval) {
      clearInterval(this.blinkInterval)
      this.$store.commit('batch/SET_AGENT_BLINK', false) // Recommended mutation approach
      // Updates the batch details in the store, including sub-path.
      this.$store.commit('batch/SET_BATCH_ID', null)
    }
  },
  // Lifecycle hook: Component destruction
  destroyed() {
    // Leave WebSocket room on destruction
    WS.leaveRoom(`batch_status_${this.id}`)

    // Remove event listeners
    bus.$off('wsData/batchStatus', this.onBatchStatus)
    bus.$off('lookup/displayAddRecordForm', this.displayAddRecordForm)
    bus.$off('toggle-navbar', this.gettogoleNavbar)

    // Reset store data on component destruction
    this.$store.dispatch('batch/reset')
    this.$store.dispatch('dataView/reset')
    this.$store.dispatch('lookup/reset')
  },
  methods: {
    // initialize Batch For Verification page
    async initBatchForVerification() {
      await this.$store.dispatch('dataView/setMainMode', 'verification')
      await this.$store.dispatch('batch/fetchVerificationDetails', this.id)

      this.setPanelSizes()
      this.setPageTitle()

      this.error = null
      this.loading = false
    },
    updatePanelSizes() {
      this.$nextTick(() => {
        const rightPane = this.$refs.rightTopPane?.$el.style.height

        if (rightPane) {
          this.$store.commit('batch/SET_TOP_PANESIZE', rightPane)
        }
      })
    },

    // Fetch specific batch ID from latest_batch_info
    async getBatchId() {
      if (this.$route.params.id) {
        return this.$route.params.id // Now it is transaction id
      }

      const previousBatchId = localStorage.getItem('previous_batch_id')

      if (previousBatchId) {
        const isBatchAvailable = await this.$store.dispatch('batch/checkBatchAvailability', previousBatchId)

        if (isBatchAvailable) {
          return previousBatchId
        }
      }
      const result = {}

      this.selectedProjectCountries.forEach(e => {
        const { countryCode, project } = e

        if (!result[countryCode]) {
          result[countryCode] = []
        }

        if (!result[countryCode].includes(project)) {
          result[countryCode].push(project)
        }
      })
      const res = await axios.post('/latest_batch_info/', {
        project_countries: result,
      })

      if (!res.data.batch_id) {
        return null
      }

      return res.data.batch_id
    },
    async initBatch() {
      this.loading = true

      try {
        // Set default value to these store
        this.$store.commit('dataView/SET_BATCHES_BY_DEFINITION_TYPE', [])
        this.$store.commit('dataView/SET_TYPES_BY_DEFINITION', [])

        // Fetch batchId
        const batchId = await this.getBatchId()

        // Checking batch availbility
        if (!batchId) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'No batch available',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          this.$router.push({ name: 'home' })

          return
        }

        // Fetch Batch by the batchId
        await this.$store.dispatch('batch/fetchBatch', {
          selectedTransaction: batchId,
          selectFirstDocument: true,
        }) // This is transaction batch

        // Fetch Application & Definition Settings
        await this.$store.dispatch('applicationSettings/fetchApplicationSettings')
        await this.$store.dispatch('definitionSettings/fetchDefinitionSettings')

        // Fetch Position Shift Data
        // await this.$store.dispatch('batch/fetchPositionShiftData')

        // Load Documents
        await this.$store.dispatch('batch/loadDocumentData')

        // Fetch Definition
        await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
        this.error = null
        this.loading = false

        // Joining a specific room on WebSocket
        WS.joinRoom(`batch_status_${this.batch.id}`)
      } catch (error) {
        this.error = error
        this.loading = false
      }
    },

    // Set batch status and others staff
    async onBatchStatus(data) {
      const batch = this.$store.getters['batch/batch']
      if (batch.id === data.batch_id) {
        this.$store.commit('batch/SET_STATUS', {
          status: data.status,
          remarks: data.remarks,
          event_time: data.event_time,
        })
      }
      if (['completed', 'failed'].includes(data.status)) {
        const transactionId = this.$route.params.id
        const currentExpandedNodes = [...this.$store.state.batch.expandedNodes]
        await this.$store.dispatch('batch/fetchBatch', {
          selectedTransaction: transactionId,
          selectFirstDocument: false,
        })
        await this.$store.dispatch('batch/fetchProfileKeys')
        currentExpandedNodes.forEach(nodeId => {
          this.$store.commit('batch/EXPAND_NODE', nodeId)
        })
        // Also expand any new nodes that should be expanded
        this.flatNodes.forEach(node => {
          if (node.expandable && !node.expanded && !node.id.includes('auto_extraction') && !node.id.includes('process_keys')) {
            this.$store.commit('batch/EXPAND_NODE', node.id)
          }
        })
      }
    },

    // set panel sizes on the UI template
    setPanelSizes() {
      this.panelSizes = {
        leftPaneSize: 1,
        rightTopPaneSize: 1,
      }
      this.$nextTick(() => {
        if (this.view === 'key' || this.view === 'explore-lookup') {
          this.panelSizes = {
            leftPaneSize: 30,
            rightTopPaneSize: this.currentRouteName === 'verification' ? 100 : 50,
          }
        } else {
          this.panelSizes = {
            leftPaneSize: 0,
            rightTopPaneSize: 50,
          }
        }

        this.$forceNextTick(() => {
          bus.$emit('fitToWidth')
        })
      })
    },

    // Display Add Record Form
    displayAddRecordForm(defaultData) {
      this.addRecordToDB = true
      this.addRecordData = defaultData
    },

    // Close Add Record Form
    closeAddRecordForm() {
      this.addRecordToDB = false
      this.addRecordData = null
    },

    // Set Pag eTitle
    setPageTitle() {
      this.$store.commit('app/SET_CURRENT_PAGE_TITLE', this.pageTitle)
    },

    // Calculate Loaded Files
    onCalculateLoadedFiles({ loadedFiles, totalFiles }) {
      this.loadedFiles = loadedFiles
      this.totalFiles = totalFiles
    },

    // Fetch toggle Navbar
    gettogoleNavbar() {
      this.togoleNavbar = !this.togoleNavbar
    },
    async downloadExtractionData() {
      try {
        const params = {
          batch_id: this.selectedBatchId,
          file_type: 'output_aidb_model',
        }

        // Add transaction_id if available
        if (this.$route.params.id) {
          params.selected_transaction_id = this.$route.params.id
        }

        this.$store.commit('dataView/SET_LOADING', true)

        const response = await axios.get('/retrive_json/', { params })

        // Create a blob and download the JSON file
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `extraction_data_${this.selectedBatchId}_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Success',
            text: 'Extraction data downloaded successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
      } catch (error) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error',
            text: error.response?.data?.detail || 'Failed to download extraction data',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      } finally {
        this.$store.commit('dataView/SET_LOADING', false)
      }
    },
    // On status update Expand all eligible nodes
    // toExpandAll() {
    //   const expandNodes = () => {
    //     let expanded = false // Track if new nodes are added

    //     this.flatNodes.forEach(node => {
    //       if (node.expandable && !node.expanded) {
    //         // Expand the node and commit to Vuex
    //         this.$store.commit('batch/EXPAND_NODE', node.id)
    //         // eslint-disable-next-line no-param-reassign
    //         node.expanded = true // Update the local state

    //         expanded = true // Mark that new nodes were expanded
    //       }
    //     })

    //     return expanded // Return whether new nodes were added
    //   }

    //   // Continuously expand nodes until no new nodes are added
    //   while (expandNodes()) {
    //     // Recheck for newly added nodes
    //   }
    // },
  },
}
</script>

<style scoped>
.box {
    height: calc(100vh - 155px);
}
.box-extend {
    height: calc(100vh - 86.5px);
}
.verification-box {
    height: calc(100vh - 10.85rem);
}
.node-tree-conent {
    height:100%;
    /* row-gap: 0.5rem; */
}
.image-viewer-conent {
    height:100%;
    row-gap: 0.5rem;
}
.section-content {
    position:absolute;
    top:0px;
    left:0px;
    width:calc(100% - 1rem);
    height:calc(100% - 1rem);
    overflow:auto;
    margin:0.5rem;
}
</style>
