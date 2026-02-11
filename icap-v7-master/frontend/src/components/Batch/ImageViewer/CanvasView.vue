<!--
Organization: AIDocbuilder Inc.
File: CanvasView.vue
Version: 6.0

Authors:
    - Vinay - Initial implementation
    - Ali - Code optimization

Last Updated By: Ali
Last Updated At: 2024-11-20

Description:
    This is a vue component for show the images with canvas libs. This is one of our core component in this project. It shows the images with the details
    and it has lots of actions/functionalities like zooming, highlighting, selectors, anchoring etc.

Dependencies:
    - perant component

Main Features:
    - Show images.
    - Interect with those images.
    - Word by words highlights.
    - Zoom-In and Zoom-out images.
    - Ranges Selectors.
    - Capture by Anchor shape.
    - Fit to width.
 -->
<template>
  <div
    ref="scrollContainer"
    class="scroll-container"
    @scroll="onScroll"
  >
    <div
      class="large-container"
      :style="{
        width: canvasWidth + 'px',
        height: canvasHeight + 'px',
        'margin-left': leftMargin + 'px'
      }"
    >
      <div
        v-if="highlightedNodeConfig"
        ref="highlightedNode"
        class="highlighted-node"
        :style="{
          top: highlightedNodeConfig.y * zoom + 'px',
          left: highlightedNodeConfig.x * zoom + 'px',
          width: highlightedNodeConfig.width * zoom + 'px',
          height: highlightedNodeConfig.height * zoom + 'px',
        }"
      />

      <div
        v-if="scrollNodeConfig.visible"
        ref="scrollNode"
        class="scroll-node"
        :style="{
          top: scrollNodeConfig.y * zoom + 'px',
          left: scrollNodeConfig.x * zoom + 'px',
          width: scrollNodeConfig.width * zoom + 'px',
          height: scrollNodeConfig.height * zoom + 'px',
        }"
      />

      <div
        :style="{
          transform: `translate(${scrollX}px, ${scrollY}px)`
        }"
      >
        <v-stage
          ref="stage"
          :config="stageConfig"
          @mousedown="handleStageMouseDown"
          @touchstart="handleStageMouseDown"
          @mousemove="handleStageMouseMove"
          @touchmove="handleStageMouseMove"
          @mouseup="handleStageMouseUp"
          @touchend="handleStageMouseUp"
        >
          <v-layer
            ref="layer"
            :config="imageLayerConfig"
          >
            <v-image
              v-for="imageConfig of pageImages"
              ref="image"
              :key="imageConfig.id"
              :config="imageConfig"
            />
            <v-rect
              v-if="highlightedNodeConfig"
              ref="rect"
              :config="highlightedNodeConfig"
            />

            <template v-if="selectableWordNodes">
              <v-rect
                v-for="wordNodeConfig of wordNodesConfig"
                :key="wordNodeConfig.id"
                :config="wordNodeConfig"
                @mouseenter="nodeMouseEnterHandler"
                @mouseleave="nodeMouseLeaveHandler"
                @mousedown="nodeMouseDownHandler"
              />
            </template>

            <v-rect
              v-for="(chunkNodeConfig, index) of chunkNodesConfig"
              :key="index"
              :config="chunkNodeConfig"
              @mousedown="chunkNodeMouseDownHandler"
            />

            <v-rect
              v-for="(keyBlockConfig, index) of keyBlocksConfig"
              :key="`keyBlock${index}`"
              :config="keyBlockConfig"
            />

            <template v-if="mode === 'automated-table-model'">
              <template v-if="atmWizardTabs.results.active">
                <v-rect
                  v-for="(atmPatternRecordConfig, index) of atmPatternRecordsConfig"
                  :key="atmPatternRecordConfig.pos + index"
                  :config="atmPatternRecordConfig"
                  @mouseenter="handleMouseEnter"
                  @mouseleave="handleMouseLeave"
                  @mousedown="atmPatternMouseDownHandler"
                />
              </template>

              <template v-if="atmWizardTabs.tableRowSelection.active">
                <template
                  v-if="multipleLineRecord"
                >
                  <v-rect
                    v-for="(multiLineRecord, index) of multiLineRecordsConfig"
                    :key="multiLineRecord.pos + multiLineRecord.pageId + index"
                    :config="multiLineRecord"
                    @mouseenter="handleMouseEnter"
                    @mouseleave="handleMouseLeave"
                  />
                </template>
                <v-rect
                  v-for="(chunkLineRecordConfig, index) of chunkLineRecordsConfig"
                  :key="chunkLineRecordConfig.posRef + index"
                  :config="chunkLineRecordConfig"
                  @mouseenter="handleMouseEnter"
                  @mouseleave="handleMouseLeave"
                  @mousedown="atmPatternMouseDownHandler"
                />
              </template>
            </template>

            <v-rect
              :config="selectionRectConfig"
            />

            <v-rect
              :config="scrollNodeConfig"
            />

            <v-rect
              ref="selectorRect"
              :config="selectorRectConfig"
              @transformend="handleTransformEnd"
              @dragend="handleDragEnd"
            />

            <v-line
              :config="measureLineConfig"
            />

            <v-transformer
              ref="transformer"
              :config="transformerConfig"
            />

            <v-line
              v-for="(keyAnchorLineConfig, index) of keyAnchorLineConfigs"
              :key="`anchor-line-${index}`"
              :config="keyAnchorLineConfig"
            />
          </v-layer>
        </v-stage>
      </div>
    </div>
  </div>

</template>

<script>
import { min, max } from 'lodash'
import bus from '@/bus'
import Vue from 'vue'

// padding will increase the size of stage
// so scrolling will look smoother
const PADDING = 500
const localBus = new Vue()
const resizeOb = new ResizeObserver(() => {
  localBus.$emit('containerSizeChanged')
})

export default {
  props: {
    pages: {
      type: Array,
      required: true,
    },
    highlightedNode: {
      type: Object,
      required: false,
      default: null,
    },
    selectableWordNodes: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    chunkData: {
      type: Object,
      required: false,
      default() {
        return null
      },
    },
    keyBlocks: {
      type: Array,
      required: false,
      default() {
        return []
      },
    },
    chunkNodeListening: {
      type: Boolean,
      required: true,
    },
    atmPatternRecords: {
      type: Array,
      required: false,
      default() {
        return null
      },
    },
    chunkLineRecords: {
      type: Array,
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      selectionRectConfig: {
        rotation: 0,
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        scaleX: 1,
        scaleY: 1,
        fill: 'transparent',
        stroke: '#7367f0',
        strokeWidth: 2,
        visible: false,
        strokeScaleEnabled: false,
      },
      measureLineConfig: {
        points: [0, 0, 0, 0],
        stroke: '#7367f0',
        strokeWidth: 3,
        visible: false,
        drawing: false,
      },
      selectorRectConfig: {
        rotation: 0,
        x: 10,
        y: 10,
        width: 100,
        height: 100,
        scaleX: 1,
        scaleY: 1,
        fill: 'transparent',
        stroke: '#7367f0',
        strokeWidth: 2,
        draggable: true,
        visible: false,
        strokeScaleEnabled: false,
        name: 'selectorRect',
        selectedText: '', // Store the selected text
        selectedWords: [], // Store the selected words array
        wordCount: 0, // Store the word count
      },
      transformerConfig: {
        rotateEnabled: false,
        borderEnabled: false,
        ignoreStroke: true,
        flipEnabled: false,
        anchorStroke: '#7367f0',
        name: 'transformer',
      },
      scrollX: 0,
      scrollY: 0,
      containerSize: null,
      selectedNodeIds: [],
      dragStartX: 0,
      dragStartY: 0,
      dragEndX: 0,
      dragEndY: 0,
      scrollNodeConfig: {
        rotation: 0,
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        scaleX: 1,
        scaleY: 1,
        fill: 'transparent',
        stroke: 'red',
        strokeWidth: 2,
        visible: false,
        strokeScaleEnabled: false,
        listening: false,
      },
      scrollToPosTimer: null,
      previousViewMode: null,
    }
  },
  computed: {
    mode() {
      // Retrieves the current data view mode from the Vuex store.
      return this.$store.getters['dataView/mode']
    },
    vMode() {
      // Retrieves the current batch view mode from the Vuex store.
      return this.$store.getters['batch/view']
    },
    batchId() {
      // Gets the current batch's ID from the Vuex store.
      return this.$store.getters['batch/batch'].id
    },
    zoom() {
      // Retrieves the zoom level for the batch from the Vuex store.
      return this.$store.getters['batch/zoom']
    },
    canvasWidth() {
      // Calculates the canvas width by finding the widest page and applying the zoom factor.
      const maxWidth = max(this.pages.map(page => page.width))
      return maxWidth * this.zoom
    },
    canvasHeight() {
      // Calculates the canvas height by summing up the heights of all pages and applying the zoom factor.
      const totalHeight = this.pages.map(page => page.height).reduce((a, b) => a + b, 0)
      return totalHeight * this.zoom
    },
    stageConfig() {
      // Configures the stage dimensions and position based on the window size and scroll offsets.
      return {
        width: window.innerWidth + PADDING * 2, // Adding padding for better layout handling.
        height: window.innerHeight + PADDING * 2,
        x: -this.scrollX, // Adjusting for horizontal scrolling.
        y: -this.scrollY, // Adjusting for vertical scrolling.
      }
    },
    leftMargin() {
      // Calculates the left margin to center the canvas if it's smaller than the container width.
      let margin = 0
      if (this.canvasWidth < this.containerSize?.width) {
        margin = (this.containerSize.width - this.canvasWidth) / 2
      }
      return margin
    },
    imageLayerConfig() {
      // Configures the image layer scaling based on the current zoom level.
      return {
        scaleX: this.zoom,
        scaleY: this.zoom,
      }
    },
    pageImages() {
      // Maps each page to its display configuration, including position and dimensions.
      let pageY = 0 // Tracks cumulative vertical offset for each page.
      return this.pages.map(page => {
        const pageConfig = {
          x: 0, // Pages are aligned at the left edge.
          y: pageY, // Sets the Y-offset for the current page.
          image: page.image, // The source of the page's image.
          width: page.width, // The original width of the page.
          height: page.height, // The original height of the page.
          id: page.id, // Unique identifier for the page.
        }
        pageY += page.height // Updates the Y-offset for the next page.
        return pageConfig
      })
    },
    pageYOffsets() {
      // Creates a mapping of page IDs to their Y-offsets for quick access.
      const offsets = {}
      this.pageImages.forEach(pageImage => {
        offsets[pageImage.id] = pageImage.y
      })
      return offsets
    },
    wordNodesConfig() {
      // Constructs configuration for word nodes (e.g., text boxes) displayed on the canvas.
      const wordNodes = []
      let pageY = 0 // Tracks cumulative vertical offset for each page.
      this.pages.forEach(page => {
        page.wordNodes.forEach(wordNode => {
          const positionInfo = wordNode.pos.split(',').map(num => +num)

          const x = positionInfo[0] // X-coordinate of the word node.
          const y = positionInfo[1] + pageY // Adjusted Y-coordinate with cumulative offset.
          const width = positionInfo[2] - positionInfo[0] // Width of the word node.
          const height = positionInfo[3] - positionInfo[1] // Height of the word node.

          let fill = 'transparent' // Default fill color.
          let opacity = 1 // Default opacity.
          if (this.selectedNodeIds.includes(wordNode.id)) {
            fill = 'yellow' // Highlight color for selected nodes.
            opacity = 0.5 // Reduced opacity for highlighting.
          }

          wordNodes.push({
            id: wordNode.id, // Unique identifier for the word node.
            x,
            y,
            width,
            height,
            fill,
            wordText: wordNode.v, // Text content of the word node.
            opacity,
            text: wordNode.v,
          })
        })
        pageY += page.height // Updates the Y-offset for the next page.
      })
      return wordNodes
    },
    chunkNodesConfig() {
      const chunkNodes = []

      if (!this.chunkData) {
        // Return an empty array if chunk data is not available.
        return chunkNodes
      }

      // Iterate through each chunk line and its associated chunks.
      this.chunkData.chunkLines.forEach(chunkLine => {
        chunkLine.chunks.forEach(chunkItem => {
          const pageY = this.pageYOffsets[chunkItem.pageId.toUpperCase()] // Get the Y-offset for the page containing the chunk.
          if (pageY != null) {
            const text = chunkItem.value // Extract the text value of the chunk.
            const positionInfo = chunkItem.pos.split(',').map(num => +num) // Parse position info (x1, y1, x2, y2).
            const x = positionInfo[0]
            const y = positionInfo[1] + pageY // Adjust Y-coordinate with page offset.
            const width = positionInfo[2] - positionInfo[0] // Calculate width.
            const height = positionInfo[3] - positionInfo[1] // Calculate height.

            chunkNodes.push({
              text, // Text content of the chunk.
              x,
              y,
              width,
              height,
              fill: 'yellow', // Highlight color for chunks.
              opacity: 0.4, // Set semi-transparency for visibility.
              listening: this.chunkNodeListening, // Whether the node responds to events.
              pos: chunkItem.pos, // Original position string.
              pageId: chunkItem.pageId, // ID of the page containing the chunk.
            })
          }
        })
      })

      return chunkNodes // Return the list of chunk node configurations.
    },

    keyBlocksConfig() {
      const keyBlockNodes = []

      if (!this.highlightKeyBlocks) {
        // Return an empty array if key block highlighting is disabled.
        return keyBlockNodes
      }

      // Iterate through each key block.
      this.keyBlocks.forEach(keyBlock => {
        const pageY = this.pageYOffsets[keyBlock.pageId] // Get the Y-offset for the page containing the key block.
        if (pageY != null) {
          const positionInfo = keyBlock.pos.split(',').map(num => +num) // Parse position info (x1, y1, x2, y2).
          const x = positionInfo[0]
          const y = positionInfo[1] + pageY // Adjust Y-coordinate with page offset.
          const width = positionInfo[2] - positionInfo[0] // Calculate width.
          const height = positionInfo[3] - positionInfo[1] // Calculate height.

          keyBlockNodes.push({
            x,
            y,
            width,
            height,
            fill: 'transparent', // Transparent fill to avoid obscuring content.
            stroke: 'red', // Red border to highlight the key block.
            strokeWidth: 2, // Thickness of the border.
            listening: false, // Prevent interaction with the key block nodes.
          })
        }
      })

      return keyBlockNodes // Return the list of key block node configurations.
    },

    atmWizardTabs() {
      // Retrieve ATM wizard tabs from the Vuex store.
      return this.$store.getters['atm/atmWizardTabs']
    },

    extendedUserSelectedPatterns() {
      // Retrieve extended user-selected patterns from the Vuex store.
      return this.$store.getters['atm/extendedUserSelectedPatterns']
    },

    multipleLineRecord() {
      // Retrieve the multiple-line record data from the Vuex store.
      return this.$store.getters['dataView/modelMultipleLineRecord']
    },

    chunkLineRecordsConfig() {
      const chunkLineRecords = []

      if (!this.chunkLineRecords) {
        // Return an empty array if no chunk line records are available.
        return chunkLineRecords
      }

      // Iterate through each chunk line record.
      this.chunkLineRecords.forEach(pos => {
        // Split position string into components.
        // eslint-disable-next-line no-unused-vars
        const [left, top, right, bottom, pageId, _, __, ___, status, pattern] = pos.split(',')
        const pageY = this.pageYOffsets[pageId] // Get the Y-offset for the page.

        if (pageY != null) {
          const x = parseInt(left, 10) // Convert left coordinate to integer.
          const y = parseInt(top, 10) + pageY // Adjust Y-coordinate with page offset.
          const width = parseInt(right, 10) - parseInt(left, 10) // Calculate width.
          const height = parseInt(bottom, 10) - parseInt(top, 10) // Calculate height.

          chunkLineRecords.push({
            x,
            y,
            width,
            height,
            fill: status === 'blank' ? 'transparent' : status, // Use transparent fill if status is 'blank'.
            opacity: 0.4, // Set semi-transparency for visibility.
            pos: [left, top, right, bottom].join(','), // Reconstruct position string.
            pageId, // ID of the page containing the record.
            posRef: pos, // Original position reference.
            pattern, // Associated pattern.
          })
        }
      })

      return chunkLineRecords // Return the list of chunk line record configurations.
    },
    atmPatternRecordsConfig() {
      const atmPatternRecords = []

      // If no ATM pattern records are available, return an empty array.
      if (!this.atmPatternRecords) {
        return atmPatternRecords
      }

      // Loop through each position in ATM pattern records.
      this.atmPatternRecords.forEach(pos => {
        // Parse position details from the `pos` string.
        // eslint-disable-next-line no-unused-vars
        const [left, top, right, bottom, pageId, _, batchId, posRef, status, refStatus] = pos.split(',')
        const pageY = this.pageYOffsets[pageId] // Get the page's vertical offset.

        // Proceed only if pageY is valid and the batch ID matches the current batch.
        if (pageY != null && this.batchId === batchId) {
          const x = parseInt(left, 10) // X-coordinate of the rectangle.
          const y = parseInt(top, 10) + pageY // Y-coordinate, adjusted for the page offset.
          const width = parseInt(right, 10) - parseInt(left, 10) // Calculate width.
          const height = parseInt(bottom, 10) - parseInt(top, 10) // Calculate height.

          // Push the rectangle configuration into the `atmPatternRecords` array.
          atmPatternRecords.push({
            x,
            y,
            width,
            height,
            fill: status === 'blank' ? 'transparent' : status, // Determine fill color based on status.
            refStatus, // Reference status of the pattern.
            opacity: 0.4, // Set transparency.
            pos: [left, top, right, bottom].join(','), // Position string.
            pageId,
            posRef, // Position reference.
          })
        }
      })

      return atmPatternRecords // Return the generated configuration.
    },

    multiLineRecordsConfig() {
      const multiLineRecords = []

      // If no user-selected patterns are available, return an empty array.
      if (!this.extendedUserSelectedPatterns) {
        return multiLineRecords
      }

      // Loop through each item in the user-selected patterns.
      this.extendedUserSelectedPatterns.forEach(item => {
        let pageY = null
        let pageId = null
        let batchId = null
        let left
        let top
        let right
        let bottom

        // Process each element within the pattern group.
        item.forEach(e => {
          // eslint-disable-next-line no-unused-vars
          const [itemLeft, itemTop, itemRight, itemBottom, itemPageId, _, itemBatchId] = e.pos.split(',')

          // Set initial values for pageY, pageId, and batchId if not already set.
          if (pageY == null || pageId == null || batchId == null) {
            pageY = this.pageYOffsets[itemPageId]
            pageId = itemPageId
            batchId = itemBatchId
          }

          // Calculate the minimum bounding rectangle for the group.
          if (!left || left > parseInt(itemLeft, 10)) left = parseInt(itemLeft, 10)
          if (!top || top > parseInt(itemTop, 10)) top = parseInt(itemTop, 10)
          if (!right || right < parseInt(itemRight, 10)) right = parseInt(itemRight, 10)
          if (!bottom || bottom < parseInt(itemBottom, 10)) bottom = parseInt(itemBottom, 10)
        })

        // Create a configuration only if the page offset is valid and batch IDs match.
        if (pageY != null && batchId === this.batchId) {
          const x = parseInt(left, 10)
          const y = parseInt(top, 10) + pageY
          const width = parseInt(right, 10) - parseInt(left, 10)
          const height = parseInt(bottom, 10) - parseInt(top, 10)

          // Push the multi-line record configuration.
          multiLineRecords.push({
            x,
            y,
            width,
            height,
            fill: 'transparent', // Transparent fill.
            opacity: 0.6, // Set transparency.
            pos: [left, top, right, bottom].join(','), // Position string.
            pageId,
            stroke: 'red', // Set border color.
            strokeWidth: 4, // Border width.
          })
        }
      })

      return multiLineRecords // Return the generated configuration.
    },

    highlightedNodeConfig() {
      // Return null if no node is highlighted.
      if (!this.highlightedNode) {
        return null
      }

      // Find the configuration for the page of the highlighted node.
      const pageConfig = this.pageImages.find(pageImage => pageImage.id === this.highlightedNode.pageId)
      if (!pageConfig) {
        return null // Return null if no page configuration is found.
      }

      // Parse position details from the highlighted node's position string.
      const positionInfo = this.highlightedNode.pos.split(',').map(num => +num)

      const x = positionInfo[0]
      const y = positionInfo[1] + pageConfig.y // Adjust for page offset.
      const width = positionInfo[2] - positionInfo[0] // Calculate width.
      const height = positionInfo[3] - positionInfo[1] // Calculate height.

      // Return the highlighted node configuration.
      return {
        x,
        y,
        width,
        height,
        fill: 'transparent', // Transparent fill.
        stroke: 'red', // Border color.
        strokeWidth: 2, // Border width.
        listening: false, // Disable interaction.
      }
    },

    // Vuex getters for enabling selectors.
    enableSelector() {
      return this.$store.getters['batch/enableSelector']
    },

    // Vuex getters for measuring tools.
    enableMeasure() {
      return this.$store.getters['batch/enableMeasure']
    },

    // Vuex getters for highlighting key blocks.
    highlightKeyBlocks() {
      return this.$store.getters['batch/highlightKeyBlocks']
    },

    // Calulate selector respective to the page
    selectorPosition() {
      // Check if the selector rectangle is visible. If not, return null.
      if (!this.selectorRectConfig.visible) {
        return null
      }

      // Initialize variables to calculate the position and corresponding page.
      let topPos = this.selectorRectConfig.y // The y-coordinate of the selector relative to the document.
      let pageId = '' // ID of the page where the selector resides.
      let selectedPageIndex = -1 // Index of the page where the selector is located.
      // Calculate the position relative to the pages by iterating through them.
      for (let pageIndex = 0; pageIndex < this.pages.length; pageIndex += 1) {
        // Get the current page.
        const page = this.pages[pageIndex]
        if (topPos > page.height) {
          // If the current top position exceeds the page's height, move to the next page.
          topPos -= page.height
        } else {
          // Found the page containing the selector. Store its ID and index.
          pageId = page.id
          selectedPageIndex = pageIndex
          break
        }
      }

      // Calculate selector bounds (accounting for scaling)
      const selectorBounds = {
        left: this.selectorRectConfig.x,
        top: this.selectorRectConfig.y,
        right: this.selectorRectConfig.x + (this.selectorRectConfig.width * this.selectorRectConfig.scaleX),
        bottom: this.selectorRectConfig.y + (this.selectorRectConfig.height * this.selectorRectConfig.scaleY),
      }

      // Get selected text from word nodes
      const selectedText = this.getSelectedText(selectorBounds)

      // Return the computed selector's position and associated page information with selected text.
      return {
        startPos: this.selectorRectConfig.x.toString(), // x-coordinate of the left side of the selector.
        endPos: (this.selectorRectConfig.x + (this.selectorRectConfig.width * this.selectorRectConfig.scaleX)).toString(), // x-coordinate of the right side of the selector.
        topPos: topPos.toString(), // y-coordinate of the top of the selector.
        bottomPos: (topPos + (this.selectorRectConfig.height * this.selectorRectConfig.scaleY)).toString(), // y-coordinate of the bottom of the selector.
        pageId, // ID of the page containing the selector.
        pageIndex: selectedPageIndex, // Index of the page containing the selector.
        selectedText: selectedText.text, // The selected text content
        // selectedWords: selectedText.words, // Array of selected word objects with position info
        wordCount: selectedText.words.length, // Number of words selected
      }
    },
    measuredDistance() {
      // Check if the measure line is visible and not currently being drawn. If not, return null.
      if (!this.measureLineConfig.visible || this.measureLineConfig.drawing) {
        return null
      }

      // Calculate the horizontal and vertical distances between the start and end points of the measure line.
      const xDistance = Math.abs(this.measureLineConfig.points[2] - this.measureLineConfig.points[0]).toFixed(2) // Horizontal distance.
      const yDistance = Math.abs(this.measureLineConfig.points[3] - this.measureLineConfig.points[1]).toFixed(2) // Vertical distance.

      // Return the computed distances as an object.
      return { xDistance, yDistance }
    },

    // Get the state of whether key anchors should be displayed from the Vuex store.
    displayKeyAnchors() {
      return this.$store.getters['batch/displayKeyAnchors']
    },

    // Retrieve the key anchors' data from the Vuex store.
    keyAnchorsData() {
      return this.$store.getters['batch/keyAnchorsData']
    },
    keyAnchorLineConfigs() {
      const lines = []

      // Check if key anchors should be displayed
      if (!this.displayKeyAnchors) {
        return lines // Return an empty array if not visible
      }

      // Retrieve the key anchor data for each side (top, bottom, left, right)
      const topData = this.keyAnchorsData.top || {}
      const bottomData = this.keyAnchorsData.bottom || {}
      const leftData = this.keyAnchorsData.left || {}
      const rightData = this.keyAnchorsData.right || {}
      const { selectedAnchor } = this.keyAnchorsData // Retrieve the currently selected anchor

      // Convert thresholds to floats or default to 0 if not available
      const topThreshold = topData.threshold ? parseFloat(topData.threshold) : 0
      const bottomThreshold = bottomData.threshold ? parseFloat(bottomData.threshold) : 0
      const leftThreshold = leftData.threshold ? parseFloat(leftData.threshold) : 0
      const rightThreshold = rightData.threshold ? parseFloat(rightData.threshold) : 0

      let page
      let pageYOffset
      let x1
      let y1
      let x2
      let y2

      // Process top anchor if available
      if (topData.pos) {
        page = this.pages[topData.pageIndex] // Get the page for the top anchor
        if (page) {
          pageYOffset = this.pageYOffsets[page.id] // Get the page Y offset
          x1 = leftData.pos ? +leftData.pos.split(',')[2] : 0
          y1 = +topData.pos.split(',')[3] + pageYOffset
          x2 = rightData.pos ? +rightData.pos.split(',')[0] : page.width
          y2 = +topData.pos.split(',')[3] + pageYOffset

          // If the top anchor is selected, add a special dashed line
          if (selectedAnchor === 'top') {
            lines.push({
              points: [x1 + leftThreshold, y1, x2 + rightThreshold, y2],
              stroke: '#7367f0',
              strokeWidth: 2,
              strokeScaleEnabled: false,
              dash: [10, 10], // Dashed line style
            })
          }

          // Add a red line for the top anchor
          lines.push({
            points: [x1 + leftThreshold, y1 + topThreshold, x2 + rightThreshold, y2 + topThreshold],
            stroke: 'red',
            strokeWidth: 2,
            strokeScaleEnabled: false,
            dash: selectedAnchor === 'top' ? [10, 10] : [],
          })
        }
      }

      // Process bottom anchor if available
      if (bottomData.pos) {
        page = this.pages[bottomData.pageIndex] // Get the page for the bottom anchor
        if (page) {
          pageYOffset = this.pageYOffsets[page.id] // Get the page Y offset
          x1 = leftData.pos ? +leftData.pos.split(',')[2] : 0
          y1 = +bottomData.pos.split(',')[1] + pageYOffset
          x2 = rightData.pos ? +rightData.pos.split(',')[0] : page.width
          y2 = +bottomData.pos.split(',')[1] + pageYOffset

          // If the bottom anchor is selected, add a special dashed line
          if (selectedAnchor === 'bottom') {
            lines.push({
              points: [x1 + leftThreshold, y1, x2 + rightThreshold, y2],
              stroke: '#7367f0',
              strokeWidth: 2,
              strokeScaleEnabled: false,
              dash: [10, 10], // Dashed line style
            })
          }

          // Add a red line for the bottom anchor
          lines.push({
            points: [x1 + leftThreshold, y1 + bottomThreshold, x2 + rightThreshold, y2 + bottomThreshold],
            stroke: 'red',
            strokeWidth: 2,
            strokeScaleEnabled: false,
            dash: selectedAnchor === 'bottom' ? [10, 10] : [],
          })
        }
      }

      // Process left anchor if available
      if (leftData.pos) {
        page = this.pages[leftData.pageIndex] // Get the page for the left anchor
        if (page) {
          pageYOffset = this.pageYOffsets[page.id] // Get the page Y offset
          x1 = +leftData.pos.split(',')[2]
          y1 = (topData.pos ? +topData.pos.split(',')[3] : 0) + pageYOffset
          x2 = +leftData.pos.split(',')[2]
          y2 = (bottomData.pos ? +bottomData.pos.split(',')[1] : page.height) + pageYOffset

          // If the left anchor is selected, add a special dashed line
          if (selectedAnchor === 'left') {
            lines.push({
              points: [x1, y1 + topThreshold, x2, y2 + bottomThreshold],
              stroke: '#7367f0',
              strokeWidth: 2,
              strokeScaleEnabled: false,
              dash: [10, 10], // Dashed line style
            })
          }

          // Add a red line for the left anchor
          lines.push({
            points: [x1 + leftThreshold, y1 + topThreshold, x2 + leftThreshold, y2 + bottomThreshold],
            stroke: 'red',
            strokeWidth: 2,
            strokeScaleEnabled: false,
            dash: selectedAnchor === 'left' ? [10, 10] : [],
          })
        }
      }

      // Process right anchor if available
      if (rightData.pos) {
        page = this.pages[rightData.pageIndex] // Get the page for the right anchor
        if (page) {
          pageYOffset = this.pageYOffsets[page.id] // Get the page Y offset
          x1 = +rightData.pos.split(',')[0]
          y1 = (topData.pos ? +topData.pos.split(',')[3] : 0) + pageYOffset
          x2 = +rightData.pos.split(',')[0]
          y2 = (bottomData.pos ? +bottomData.pos.split(',')[1] : page.height) + pageYOffset

          // If the right anchor is selected, add a special dashed line
          if (selectedAnchor === 'right') {
            lines.push({
              points: [x1, y1 + topThreshold, x2, y2 + bottomThreshold],
              stroke: '#7367f0',
              strokeWidth: 2,
              strokeScaleEnabled: false,
              dash: [10, 10], // Dashed line style
            })
          }

          // Add a red line for the right anchor
          lines.push({
            points: [x1 + rightThreshold, y1 + topThreshold, x2 + rightThreshold, y2 + bottomThreshold],
            stroke: 'red',
            strokeWidth: 2,
            strokeScaleEnabled: false,
            dash: selectedAnchor === 'right' ? [10, 10] : [],
          })
        }
      }

      // Return the array of lines for key anchors
      return lines
    },
  },
  watch: {
    // Watcher for `selectorPosition`: Reacts to changes in the `selectorPosition` property
    // and commits the updated value to the Vuex store using the 'batch/SET_SELECTOR_POSITION' mutation.
    selectorPosition: {
      handler() {
        this.$store.commit('batch/SET_SELECTOR_POSITION', this.selectorPosition)
      },
      deep: true, // Ensures the watcher reacts to changes in nested properties of `selectorPosition`.
    },

    // Watcher for `measuredDistance`: Reacts to changes in the `measuredDistance` property
    // and commits the updated value to the Vuex store using the 'batch/SET_MEASURED_DISTANCE' mutation.
    measuredDistance: {
      handler() {
        this.$store.commit('batch/SET_MEASURED_DISTANCE', this.measuredDistance)
      },
      deep: true, // Ensures the watcher reacts to changes in nested properties of `measuredDistance`.
    },

    // Watcher for `enableSelector`: Invokes `deleteSelector` if `enableSelector` is set to `false`.
    enableSelector() {
      if (this.enableSelector === false) {
        this.deleteSelector()
      }
    },

    // Watcher for `enableMeasure`: Invokes `deleteMeasure` if `enableMeasure` is set to `false`.
    enableMeasure() {
      if (this.enableMeasure === false) {
        this.deleteMeasure()
      }
    },
    vMode(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.previousViewMode = oldVal
      }
    },
  },

  // Lifecycle hook: Called when the component is created.
  created() {
    // Listens for custom events on the global event bus and local event bus.
    bus.$on('fitToWidth', this.fitToWidth) // Executes `fitToWidth` when 'fitToWidth' event is triggered.
    bus.$on('scrollToHighlightedNode', this.scrollToHighlightedNode) // Executes `scrollToHighlightedNode` when the event is triggered.
    bus.$on('scrollToPos', this.scrollToPos) // Executes `scrollToPos` when the event is triggered.
    localBus.$on('containerSizeChanged', this.onContainerSizeChange) // Executes `onContainerSizeChange` when 'containerSizeChanged' is triggered.
  },

  // The `mounted` hook is called after the component is mounted to the DOM.
  // At this stage, you can safely access the component's DOM elements.
  mounted() {
    this.setContainerSize()
    this.fitToWidth()
    resizeOb.observe(this.$refs.scrollContainer)
    this.scrollToHighlightedNode()
  },

  // The `beforeDestroy` (or `beforeUnmount` in Vue 3) hook is called right before
  // a component is destroyed and its event listeners and child components are removed.
  beforeDestroy() {
    resizeOb.unobserve(this.$refs.scrollContainer)
  },

  // Lifecycle hook: Component destruction
  destroyed() {
    bus.$off('fitToWidth', this.fitToWidth)
    bus.$off('scrollToHighlightedNode', this.scrollToHighlightedNode)
    bus.$off('scrollToPos', this.scrollToPos)
    localBus.$off('containerSizeChanged', this.onContainerSizeChange)
  },
  methods: {
    updateSelectorTextData() {
      if (!this.selectorRectConfig.visible) {
      // Clear text data if selector is not visible
        this.selectorRectConfig.selectedText = ''
        this.selectorRectConfig.selectedWords = []
        this.selectorRectConfig.wordCount = 0
        return
      }

      // Calculate selector bounds
      const selectorBounds = {
        left: this.selectorRectConfig.x,
        top: this.selectorRectConfig.y,
        right: this.selectorRectConfig.x + (this.selectorRectConfig.width * this.selectorRectConfig.scaleX),
        bottom: this.selectorRectConfig.y + (this.selectorRectConfig.height * this.selectorRectConfig.scaleY),
      }

      // Get selected text
      const selectedText = this.getSelectedText(selectorBounds)

      // Update the selector config with text data
      this.selectorRectConfig.selectedText = selectedText.text
      this.selectorRectConfig.selectedWords = selectedText.words
      this.selectorRectConfig.wordCount = selectedText.words.length
    },
    getSelectedText(selectorBounds) {
      const selectedWords = []

      // Check if word nodes are available
      if (!this.selectableWordNodes) {
        return { text: '', words: [], count: 0 }
      }

      // Iterate through all word node configurations to find intersecting ones
      this.wordNodesConfig.forEach(wordNode => {
      // Check if word node intersects with selector bounds
        if (this.isWordNodeInSelector(wordNode, selectorBounds)) {
          selectedWords.push({
            id: wordNode.id,
            text: wordNode.wordText || wordNode.text, // Use either property that exists
            x: wordNode.x,
            y: wordNode.y,
            width: wordNode.width,
            height: wordNode.height,
          })
        }
      })

      // Sort words by position (top to bottom, then left to right)
      selectedWords.sort((a, b) => {
      // First sort by y-position (top to bottom)
        if (Math.abs(a.y - b.y) > 5) { // 5px tolerance for same line
          return a.y - b.y
        }
        // Then sort by x-position (left to right) for words on the same line
        return a.x - b.x
      })

      // Combine text from selected words
      const combinedText = selectedWords.map(word => word.text).join(' ')

      return {
        text: combinedText.trim(),
        words: selectedWords,
        count: selectedWords.length,
      }
    },

    // Helper method to check if a word node intersects with the selector
    isWordNodeInSelector(wordNode, selectorBounds) {
      const wordBounds = {
        left: wordNode.x,
        top: wordNode.y,
        right: wordNode.x + wordNode.width,
        bottom: wordNode.y + wordNode.height,
      }

      // Check for intersection (overlap)
      return !(
        wordBounds.right < selectorBounds.left
      || wordBounds.left > selectorBounds.right
      || wordBounds.bottom < selectorBounds.top
      || wordBounds.top > selectorBounds.bottom
      )
    },
    handleTransformEnd(e) {
      this.selectorRectConfig.x = e.target.x()
      this.selectorRectConfig.y = e.target.y()
      this.selectorRectConfig.rotation = e.target.rotation()
      this.selectorRectConfig.scaleX = e.target.scaleX()
      this.selectorRectConfig.scaleY = e.target.scaleY()

      this.updateSelectorTextData() // Update text data after transform
    },

    // MODIFY your existing handleDragEnd method to include text logging:
    handleDragEnd(e) {
    // Your existing code
      this.selectorRectConfig.x = e.target.x()
      this.selectorRectConfig.y = e.target.y()
      this.updateSelectorTextData()
    },

    handleMouseEnter(e) {
      // Change the cursor to a pointer when the mouse enters the target element.
      const container = e.target.getStage().container()
      container.style.cursor = 'pointer'
    },

    handleMouseLeave(e) {
      // Reset the cursor to default when the mouse leaves the target element.
      const container = e.target.getStage().container()
      container.style.cursor = 'default'
    },
    handleStageMouseDown(e) {
      e.evt.preventDefault()

      // Do nothing if clicked on selector rectangle
      const clickedOnSelectorRect = e.target.hasName('selectorRect')
      const clickedOnTransformer = e.target.getParent().className === 'Transformer'
      if (clickedOnSelectorRect || clickedOnTransformer) {
        return
      }

      if (this.enableSelector) {
        // Start selection otherwise
        const layer = this.$refs.layer.getNode()
        const pointerPosition = layer.getRelativePointerPosition()
        this.dragStartX = pointerPosition.x
        this.dragStartY = pointerPosition.y
        this.dragEndX = pointerPosition.x
        this.dragEndY = pointerPosition.y

        this.selectionRectConfig.width = 0
        this.selectionRectConfig.height = 0
        this.selectionRectConfig.visible = true
      }

      if (this.enableMeasure) {
        // Start measure otherwise
        const layer = this.$refs.layer.getNode()
        const pointerPosition = layer.getRelativePointerPosition()
        this.dragStartX = pointerPosition.x
        this.dragStartY = pointerPosition.y
        this.dragEndX = pointerPosition.x
        this.dragEndY = pointerPosition.y

        this.measureLineConfig.points = [0, 0, 0, 0]
        this.measureLineConfig.visible = true
        this.measureLineConfig.drawing = true
      }
    },
    handleStageMouseMove(e) {
      e.evt.preventDefault()
      if (this.enableSelector) {
        if (!this.selectionRectConfig.visible) {
          return
        }

        // Update dimenitions of selection rectangle
        const layer = this.$refs.layer.getNode()
        const pointerPosition = layer.getRelativePointerPosition()

        this.dragEndX = pointerPosition.x
        this.dragEndY = pointerPosition.y

        this.selectionRectConfig.x = Math.min(this.dragStartX, this.dragEndX)
        this.selectionRectConfig.y = Math.min(this.dragStartY, this.dragEndY)
        this.selectionRectConfig.width = Math.abs(this.dragEndX - this.dragStartX)
        this.selectionRectConfig.height = Math.abs(this.dragEndY - this.dragStartY)
      }

      if (this.enableMeasure) {
        // if user is not drawing line, do nothing
        if (!this.measureLineConfig.drawing) {
          return
        }

        // Update line points
        const layer = this.$refs.layer.getNode()
        const pointerPosition = layer.getRelativePointerPosition()

        this.dragEndX = pointerPosition.x
        this.dragEndY = pointerPosition.y

        const points = [
          this.dragStartX,
          this.dragStartY,
          this.dragEndX,
          this.dragEndY,
        ]
        this.measureLineConfig.points = points
      }
    },
    handleStageMouseUp(e) {
      e.evt.preventDefault()
      if (this.enableSelector) {
        if (!this.selectionRectConfig.visible) {
          return
        }

        if (this.selectionRectConfig.width > 0) {
          this.createSelector(this.selectionRectConfig.x, this.selectionRectConfig.y, this.selectionRectConfig.width, this.selectionRectConfig.height)
        }

        // Hide selection rectangle
        this.selectionRectConfig.visible = false
      }
      if (this.enableMeasure) {
        // if user is drawing a line, complete the line.
        if (this.measureLineConfig.drawing) {
          this.measureLineConfig.drawing = false
        }
      }
    },
    // Handles scroll events to update the current scroll position
    onScroll() {
      // Adjust the scroll positions by subtracting a padding value
      this.scrollX = this.$refs.scrollContainer.scrollLeft - PADDING
      this.scrollY = this.$refs.scrollContainer.scrollTop - PADDING
    },

    // Triggered when the container's size changes
    onContainerSizeChange() {
      this.setContainerSize() // Update the container size
    },

    // Sets the container size (width and height) based on the DOM element
    setContainerSize() {
      this.containerSize = {
        width: this.$refs.scrollContainer.clientWidth,
        height: this.$refs.scrollContainer.clientHeight,
      }
    },

    // Adjusts the zoom level to fit the container width
    fitToWidth(customZoomLevel = false) {
      if (!this.containerSize || this.pages.length === 0) {
        return // Exit if no container size or pages are defined
      }

      // Find the maximum width among all pages
      const pageWidth = max(this.pages.map(page => page.width))

      // Calculate a zoom level based on container width and page width
      const widthZoom = this.containerSize.width / pageWidth < 0.23 ? 0.23 : this.containerSize.width / pageWidth
      if (this.previousViewMode === null) {
        this.previousViewMode = this.vMode
      }

      // Handle custom zoom or specific modes
      if (customZoomLevel || this.vMode !== this.previousViewMode) {
        this.$store.commit('batch/SET_ZOOM', widthZoom - 0.1)
        return
      }

      // Apply zoom level based on conditions
      if (this.zoom === 1 || this.zoom <= (widthZoom - 0.1)) {
        this.$store.commit('batch/SET_ZOOM', widthZoom - 0.1)
      }
    },

    // Scrolls the view to a highlighted node
    scrollToHighlightedNode() {
      if (!this.$refs.highlightedNode) {
        return // Exit if no highlighted node exists
      }

      // Adjust the scroll to center the highlighted node with some padding
      this.$refs.scrollContainer.scrollTop = this.$refs.highlightedNode.offsetTop - 20
      this.$refs.scrollContainer.scrollLeft = this.$refs.highlightedNode.offsetLeft - 20
    },

    // Scrolls the view to a specific position within a page
    scrollToPos(data) {
      const { pos, pageId } = data

      // Find the configuration for the specified page
      const pageConfig = this.pageImages.find(pageImage => pageImage.id === pageId)
      if (!pageConfig) {
        return // Exit if the page is not found
      }

      // Parse position data
      const positionInfo = pos.split(',').map(num => +num)
      const x = positionInfo[0]
      const y = positionInfo[1] + pageConfig.y
      const width = positionInfo[2] - positionInfo[0]
      const height = positionInfo[3] - positionInfo[1]

      clearTimeout(this.scrollToPosTimer) // Clear any existing timers

      this.scrollNodeConfig.x = x
      this.scrollNodeConfig.y = y
      this.scrollNodeConfig.width = width
      this.scrollNodeConfig.height = height
      this.scrollNodeConfig.visible = true

      this.$nextTick(() => {
        // Scroll to the updated position
        this.$refs.scrollContainer.scrollTop = this.$refs.scrollNode.offsetTop - 20
        this.$refs.scrollContainer.scrollLeft = this.$refs.scrollNode.offsetLeft - 20

        // Hide the scroll node after 1.5 seconds
        this.scrollToPosTimer = setTimeout(() => {
          this.scrollNodeConfig.visible = false
        }, 10000)
      })
    },

    // Handles mouse enter events on nodes
    nodeMouseEnterHandler(event) {
      const nodeId = event.target.attrs.id

      // Add the node to selected nodes if Shift is pressed
      if (event.evt.shiftKey) {
        if (!this.selectedNodeIds.includes(nodeId)) {
          this.selectedNodeIds.push(nodeId)
        }
      } else {
        this.selectedNodeIds = [nodeId] // Select only the current node
      }
    },

    // Handles mouse leave events on nodes
    nodeMouseLeaveHandler(event) {
      if (!event.evt.shiftKey) {
        this.selectedNodeIds = [] // Clear selection if Shift is not pressed
      }
    },

    // Handles mouse down events on nodes
    nodeMouseDownHandler(event) {
      event.evt.preventDefault()

      if (this.selectedNodeIds.length === 0) {
        return // Exit if no nodes are selected
      }

      const wordNodes = []

      // Aggregate all word nodes from pages
      this.pages.forEach(page => {
        page.wordNodes.forEach(wordNode => {
          wordNodes.push({
            pageId: page.id,
            ...wordNode,
          })
        })
      })

      // Filter nodes based on selected IDs
      const selectedNodes = wordNodes.filter(node => this.selectedNodeIds.includes(node.id))

      // Extract position and style information
      const text = selectedNodes.map(node => node.v).join(' ')
      const startPos = min(selectedNodes.map(node => +node.pos.split(',')[0])).toString()
      const topPos = min(selectedNodes.map(node => +node.pos.split(',')[1])).toString()
      const endPos = max(selectedNodes.map(node => +node.pos.split(',')[2])).toString()
      const bottomPos = min(selectedNodes.map(node => +node.pos.split(',')[3])).toString()

      const { pageId, styleId } = selectedNodes[0]
      const pageIndex = this.pages.findIndex(page => page.id === pageId)
      const page = this.pages[pageIndex]
      const style = styleId && page.styles[styleId] ? page.styles[styleId] : null

      // Emit the selected node information
      const value = {
        text,
        startPos,
        topPos,
        endPos,
        bottomPos,
        pageIndex,
        pageId,
        style,
        pageHeight: page.height,
        pageWidth: page.width,
      }
      bus.$emit('imageViewerValueSelected', value)
    },

    // Creates a selection rectangle
    createSelector(x, y, width, height) {
      this.selectorRectConfig.x = x
      this.selectorRectConfig.y = y
      this.selectorRectConfig.width = width
      this.selectorRectConfig.height = height
      this.selectorRectConfig.scaleX = 1
      this.selectorRectConfig.scaleY = 1
      this.selectorRectConfig.visible = true

      this.updateSelectorTextData() // Update text data when selector is created

      // Attach transformer
      const transformerNode = this.$refs.transformer.getNode()
      transformerNode.nodes([this.$refs.selectorRect.getNode()])
    },

    // Deletes the selection rectangle
    deleteSelector() {
      this.selectorRectConfig.visible = false

      // Detach the transformer
      const transformerNode = this.$refs.transformer.getNode()
      transformerNode.nodes([])
      this.updateSelectorTextData() // Clear text data when selector is deleted
    },

    // Resets the measurement line configuration
    deleteMeasure() {
      this.measureLineConfig.points = [0, 0, 0, 0]
      this.measureLineConfig.visible = false
      this.measureLineConfig.drawing = false
    },

    // Handles mouse down events on chunk nodes
    chunkNodeMouseDownHandler(event) {
      const { text, pos, pageId } = event.target.attrs

      // Emit a specific event if in chunk-data mode
      if (this.mode === 'chunk-data') {
        bus.$emit('scrollToChunkCell', { pos, pageId })
      }

      const startPos = pos.split(',')[0]
      const topPos = pos.split(',')[1]
      const endPos = pos.split(',')[2]
      const bottomPos = pos.split(',')[3]

      const pageIndex = this.pages.findIndex(page => page.id === pageId.toUpperCase())
      const page = this.pages[pageIndex]

      // Emit the chunk node information
      const value = {
        text,
        startPos,
        topPos,
        endPos,
        bottomPos,
        pageIndex,
        style: null,
        pageHeight: page.height,
        pageWidth: page.width,
      }
      bus.$emit('imageViewerValueSelected', value)
    },

    // Handles mouse down events on ATM patterns
    atmPatternMouseDownHandler(event) {
      const { posRef, refStatus } = event.target.attrs

      if (this.atmWizardTabs.tableRowSelection.active) {
        // Emit event for table row selection
        bus.$emit('atm/selectTableRow', posRef)
        return
      }

      // Handle Shift key behavior
      if (event.evt.shiftKey) {
        bus.$emit('atm/onShiftClick', posRef)
      }

      // Emit event to scroll to ATM pattern record
      bus.$emit('atm/scrollToAtmPatternRecord', { posRef, refStatus })
    },
  },
}
</script>

<style scoped>
.scroll-container {
    overflow: auto;
}
.large-container {
    overflow: hidden;
    position: relative;
}
.highlighted-node, .scroll-node {
    position: absolute;
    transition: stroke-color 1s ease;
}
</style>
