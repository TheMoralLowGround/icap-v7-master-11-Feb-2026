<!--
 Organization: AIDocbuilder Inc.
 File: Imageviewer.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   The Imageviewer.vue component is responsible for displaying document pages
   within an interactive viewer. It manages page loading, error handling, and
   rendering of a child canvas view with additional features such as highlighting
   and chunk data visualization.

 Dependencies:
   - Vue: JavaScript framework for building UI.
   - BootstrapVue: Provides UI components like alerts and spinners.
   - Tiff.js: Library for rendering TIFF images.
   - ToastificationContent: Component for displaying toast notifications.
   - Vuex: For managing application state.
   - Helper functions: `getBatchMediaURL`, `parsePage` for batch and page parsing.

 Main Features:
   - Loads document pages dynamically, fetching images and associated data in batches.
   - Handles errors gracefully with user feedback via alert and toast notifications.
   - Utilizes Vuex getters to fetch application state for nodes, chunk data, and page lists.
   - Provides a spinner for loading indication and integrates a reusable `CanvasView`
     component for rendering pages.

 Core Components:
   - `<b-alert>`: Displays error messages when page loading fails.
   - `<b-spinner>`: Shows a loading spinner during data fetching.
   - `<canvas-view>`: Renders the actual pages with additional functionality
     (e.g., highlighting, chunk data).

 Notes:
   - Page loading is performed in batches to optimize performance and reduce memory usage.
   - This file is crucial for visualizing document pages and their metadata in the application.
-->

<template>
  <div
    ref="imageViewer"
    class="image-viewer"
  >
    <!-- Alert to display errors -->
    <b-alert
      variant="danger"
      :show="!loading && loadingError !== null ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <div
      v-if="loading"
      class="text-center"
    >
      <!-- Spinner displayed while loading -->
      <b-spinner
        variant="primary"
      />
    </div>
    <!-- Canvas view component to display pages -->
    <canvas-view
      v-if="!loading && !loadingError"
      class="canvas-view"
      :pages="pages"
      :highlighted-node="highlightedNode"
      :selectable-word-nodes="selectableWordNodes"
      :chunk-data="chunkData"
      :key-blocks="keyBlocks"
      :chunk-node-listening="chunkNodeListening"
      :atm-pattern-records="atmPatternRecords"
      :chunk-line-records="chunkLineRecords"
    />
  </div>
</template>

<script>
import Vue from 'vue'
import Tiff from 'tiff.js'
import { BSpinner, BAlert } from 'bootstrap-vue'
import ToastificationContent from '@/@core/components/toastification/ToastificationContent.vue'
import { getBatchMediaURL, parsePage } from '@/store/batch/helper'
import CanvasView from './CanvasView.vue'

export default {
  // Declaring components used in the template
  components: { BSpinner, BAlert, CanvasView },
  data() {
    return {
      loading: false, // Indicates if data is loading
      loadingError: null, // Stores error message during loading
      pages: [], // Holds page data to be displayed
      isDocidChanged: false, // Tracks if the document ID has changed
      cancelLoading: false, // Tracks if loading should be canceled
      tempPages: [], // Temporary storage for pages during loading
      abortController: null,
    }
  },
  computed: {
    // Retrieve selected node from the store
    node() {
      return this.$store.getters['batch/selectedNode']
    },
    // Retrieve selected page from the store
    page() {
      return this.$store.getters['batch/selectedPage']
    },
    // List of pages for the current document
    pageList() {
      return this.$store.getters['batch/documentData'].pages
    },
    // Highlights a specific node based on the current selection
    highlightedNode() {
      if (this.node && this.node.highlight) {
        return { pageId: this.node.pageId, pos: this.node?.pos }
      }
      return null
    },
    // Determines if chunk data view is active
    displayChunkData() {
      return this.$store.getters['batch/view'] === 'chunk-data'
    },
    // Determines if chunk node listening mode is active
    chunkNodeListening() {
      return this.$store.getters['dataView/mainMode'] === 'chunkData'
    },
    // Checks if selectable word nodes are enabled
    selectableWordNodes() {
      return this.$store.getters['batch/mode'] === 'edit' && !this.chunkNodeListening
    },
    // Retrieves chunk data if chunk data view is active
    chunkData() {
      return this.displayChunkData ? this.$store.getters['batch/chunkData'] : null
    },
    // Retrieves key blocks for the selected document
    keyBlocks() {
      return this.$store.getters['batch/selectedDocument']?.keyBlocks || []
    },
    // Retrieves chunk line records from the store
    chunkLineRecords() {
      return this.$store.getters['atm/chunkLineRecords']
    },
    // Retrieves ATM pattern records from the store
    atmPatternRecords() {
      return this.$store.getters['atm/atmPatternRecords']
    },
    // Retrieves selected document ID
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },
    batch() {
      return this.$store.getters['batch/batch']
    },
  },
  watch: {
    // Reload pages when the page list changes
    pageList: {
      deep: true,
      handler() {
        this.loadPages()
      },
    },
    // Mark document ID as changed when it updates
    selectedDocumentId: {
      deep: true,
      handler() {
        this.isDocidChanged = true
      },
    },
    // tempPages: {
    //   deep: true,
    //   handler(value) {
    //     for (let index = 0; index < value.length; index += 1) {
    //       const el = value[index]
    //       if (el === undefined || !el.image) {
    //         break
    //       }
    //       if (this.pages[index] === undefined) {
    //         this.pages.push(el)
    //       }
    //     }
    //   },
    // },
  },
  created() {
    this.loadPages() // Load pages when component is created
  },
  beforeRouteLeave(to, from, next) {
    this.cancelLoading = true // Cancel loading when leaving the route
    next()
  },
  methods: {
    // Loads pages and their associated data
    /* eslint-disable no-await-in-loop */
    async loadPages() {
      // Abort the previous session immediately
      if (this.abortController) {
        this.abortController.abort() // Cancel previous call
      }

      // Create a new AbortController for this session
      this.abortController = new AbortController()
      const { signal } = this.abortController

      this.loading = true
      const batch = this.$store.getters['batch/batch']
      const { subPath } = batch
      this.pages = []

      try {
        // Step 1: Load the initial document data (without full page parsing)
        const rawPages = this.pageList[0]?.pages || [] // Unparsed nodes

        // Initialize pages array with only the required properties
        const pages = rawPages?.map(page => ({
          id: page.id,
          width: 0,
          height: 0,
          imageUrl: getBatchMediaURL(batch.id, subPath, page.IMAGEFILE, batch.isDatasetBatch),
          image: null,
          wordNodes: [],
          styles: {},
        }))

        this.tempPages[pages.length - 1] = undefined
        this.isDocidChanged = false

        const BATCH_SIZE = 10 // Process 5 pages at a time
        const totalBatches = Math.ceil(pages.length / BATCH_SIZE)

        // Step 2: Sequentially process batches
        for (let batchIndex = 0; batchIndex < totalBatches; batchIndex += 1) {
          if (signal.aborted) {
            return
          }

          // Check if loading is canceled or doc ID is changed
          if (this.isDocidChanged || this.cancelLoading) {
            this.isDocidChanged = false
            this.loading = true
            this.$emit('calculate-loaded-files', 0)
            break
          }

          // Get current batch of page IDs
          const batchStart = batchIndex * BATCH_SIZE
          const batchEnd = Math.min(batchStart + BATCH_SIZE, pages.length)
          const currentBatch = pages?.slice(batchStart, batchEnd)
          const pageIds = currentBatch.map(page => page.id)
          const pageIdsString = pageIds.join(',')

          try {
            // Fetch child nodes for the batch
            const childNodesArray = await this.$store.dispatch('batch/loadNestedRaJson', pageIdsString)

            // Fetch images for the batch
            const images = await Promise.all(
              currentBatch.map(page => this.fetchImage(page.imageUrl)),
            )

            // Process each page in the batch
            for (let i = 0; i < currentBatch.length; i += 1) {
              const page = currentBatch[i]
              const childNodes = childNodesArray[i] // Use corresponding childNodes

              // Parse the page with child nodes
              const parsedPage = parsePage(childNodes)

              // Destructure positionInfo array [x, y, width, height]
              const [, , width = 0, height = 0] = parsedPage[page.id]?.pos
                ? parsedPage[page.id]?.pos.split(',').map(num => +num)
                : [0, 0, 0, 0]

              // Update the current page with the parsed content
              page.width = width
              page.height = height
              page.image = images[i]
              page.wordNodes = parsedPage[page.id]?.wordNodes
              page.styles = parsedPage[page.id]?.styles

              // Use `this.$set` to ensure reactivity
              this.$set(this.pages, batchStart + i, page)

              // Emit event for each loaded page
              const loadedFiles = pages.length > BATCH_SIZE ? batchStart + i + 1 : i + 1
              this.$emit('calculate-loaded-files', { loadedFiles, totalFiles: pages.length })
            }
          } catch (error) {
            if (signal.aborted) {
              this.loadingError = 'Fetch operation was aborted'
            } else {
              this.loadingError = error.message
            }
            break // Stop processing further pages if there is an error
          }
        }
      } catch (error) {
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: error?.response?.data?.detail || 'Error loading pages',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      } finally {
        if (!signal.aborted) {
          this.loading = false
        }
      }
    },

    // Fetches image data from a given URL
    async fetchImage(imageUrl) {
      try {
        const response = await fetch(imageUrl)
        const buffer = await response.arrayBuffer()
        const tiff = new Tiff({ buffer })
        return tiff.toCanvas()
      } catch (error) {
        throw new Error('Error loading image')
      }
    },
  },
}
</script>

<style scoped>
.image-viewer {
    height: 100%;
    position: relative;
}
.canvas-view {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
}
</style>
