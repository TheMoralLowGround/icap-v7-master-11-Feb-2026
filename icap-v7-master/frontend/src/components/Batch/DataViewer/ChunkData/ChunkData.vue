<!--
 Organization: AIDocbuilder Inc.
 File: Chunkdata.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation

 Last Updated By: Vinay
 Last Updated At: 2023-11-01

 Description:
   This component renders a table that displays chunked data dynamically based on the `chunkData` from Vuex.
   It includes functionality for highlighting and scrolling to specific cells.

 Main Features:
   - Dynamically generates table rows and columns based on chunked data.
   - Highlights selected cells temporarily when navigated programmatically.
   - Handles cell clicks, emitting events with position and page ID.
   - Listens to global events for navigation to specific table cells.

 Dependencies:
   - `@/bus` for event handling.
   - `bootstrap-vue` for table structure.
   - `lodash` for utility functions.

 Notes:
   - Scoped styles ensure a consistent table layout.
   - `highlightChunkData` is managed with a timeout to reset the state.
-->

<template>
  <div class="chunk-data-container">
    <b-alert
      variant="danger"
      :show="error !== null ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ error }} <!-- Displays the error message -->
        </p>
      </div>
    </b-alert>
    <!-- Conditionally render the table if chunkData exists -->
    <b-table-simple
      v-if="chunkData"
      class="custom-table chunks-table"
      hover
      striped
      bordered
    >
      <b-tbody>
        <!-- Loop through chunkLines and render each chunkLine as a table row -->
        <b-tr
          v-for="(chunkLine, chunkLineIndex) of chunkLines"
          :key="chunkLineIndex"
        >
          <!-- Loop through each column number and render each cell -->
          <b-td
            v-for="columnNumber in numberOfColumns"
            :key="columnNumber"
          >
            <!-- Check if the chunk exists in the current column and render its value and shape -->
            <div
              v-if="chunkLine.chunks[columnNumber - 1]"
              :ref="`${chunkLine.chunks[columnNumber - 1]['pageId']}+${chunkLine.chunks[columnNumber - 1]['pos']}`"
              :class="{
                'highlight-cell': highlightChunkData === `${chunkLine.chunks[columnNumber - 1]['pageId']}+${chunkLine.chunks[columnNumber - 1]['pos']}`
              }"
              @click="onCellClick(chunkLine.chunks[columnNumber - 1])"
            >
              <!-- Display the value of the chunk -->
              <div>{{ chunkLine.chunks[columnNumber - 1]['value'] }}</div>
              <!-- Display the shape of the chunk in a muted text style -->
              <div class="text-muted">
                {{ chunkLine.chunks[columnNumber - 1]['shape'] }}
              </div>
            </div>
          </b-td>
        </b-tr>
      </b-tbody>
    </b-table-simple>
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BTableSimple, BTbody,
  BTd, BTr, BAlert,
} from 'bootstrap-vue'
import { max } from 'lodash'

export default {
  components: {
    BTableSimple,
    BTbody,
    BTd,
    BTr,
    BAlert,
  },
  props: {
    error: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      // Stores the reference of the chunk data being highlighted
      highlightChunkData: null,
      // Timer to clear the highlight after a short duration
      highlightChunkDataTimer: null,
    }
  },
  computed: {
    // Fetches the chunkData from the store
    chunkData() {
      return this.$store.getters['batch/chunkData']
    },
    // Returns the chunkLines from chunkData or an empty array if chunkData doesn't exist
    chunkLines() {
      if (!this.chunkData) {
        return null
      }

      return this.chunkData.chunkLines || []
    },
    // Determines the maximum number of columns based on the length of chunks in each chunkLine
    numberOfColumns() {
      const chunkItemCounts = this.chunkLines.map(chunkLine => chunkLine.chunks.length)
      return max(chunkItemCounts) // Uses lodash's max function to get the maximum number of columns
    },
  },
  created() {
    // Registers an event listener for the 'scrollToChunkCell' event to scroll to a specific cell
    bus.$on('scrollToChunkCell', this.scrollToChunkCell)
  },
  destroyed() {
    // Removes the event listener when the component is destroyed to avoid memory leaks
    bus.$off('scrollToChunkCell', this.scrollToChunkCell)
  },
  methods: {
    // Event handler for clicking on a cell. Emits 'scrollToPos' event with position and pageId of the clicked cell
    onCellClick(cellData) {
      bus.$emit('scrollToPos', {
        pos: cellData.pos,
        pageId: cellData.pageId.toUpperCase(),
      })
    },
    // Scrolls to a specific chunk cell based on the provided pos and pageId
    scrollToChunkCell({ pos, pageId }) {
      // Finds the DOM element for the chunk cell using its ref
      const refElement = this.$refs[`${pageId}+${pos}`]
      if (!refElement) {
        return
      }

      // Clears any previously set timeout for removing the highlight
      clearTimeout(this.highlightChunkDataTimer)
      // Sets the current chunk cell as the highlighted one
      this.highlightChunkData = `${pageId}+${pos}`
      // Wait for the next DOM update before scrolling and removing the highlight after a delay
      this.$nextTick(() => {
        refElement[0].parentNode.scrollIntoView()
        this.highlightChunkDataTimer = setTimeout(() => {
          this.highlightChunkData = null
        }, 1500)
      })
    },
  },
}
</script>

<style scoped lang="scss">
.chunk-data-container {
  ::v-deep .chunks-table td {
    white-space: nowrap;  // Ensures the content inside table cells does not wrap
  }
}
.highlight-cell {
  border: 2px solid red;  // Highlights the selected cell with a red border
}
</style>
