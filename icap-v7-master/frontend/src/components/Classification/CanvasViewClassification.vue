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
        class="h-100"
        :style="{
          transform: `translate(${scrollX}px, ${scrollY}px)`
        }"
      >
        <v-stage
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
              :key="imageConfig.id"
              :config="imageConfig"
            />

            <template>
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

            <v-transformer
              ref="transformer"
              :config="transformerConfig"
            />
          </v-layer>
        </v-stage>
      </div>
    </div>
    <ConfirmEnableTrigger
      v-if="isEnableTrigger && isNameMatchingClassifed[selectedPage]"
      @modal-closed="setTriggerEnablement(selectedPage, true)"
      @confirmed="setTriggerEnablement(selectedPage, false)"
    />
  </div>

</template>

<script>
import { min, max } from 'lodash'
import bus from '@/bus'
import Vue from 'vue'
import ConfirmEnableTrigger from '@/components/Classification/ConfirmEnableTrigger.vue'

// padding will increase the size of stage
// so scrolling will look smoother
const PADDING = 500
const localBus = new Vue()
const resizeOb = new ResizeObserver(() => {
  localBus.$emit('containerSizeChanged')
})

export default {
  components: {
    ConfirmEnableTrigger,
  },
  props: {
    pages: {
      type: Array,
      required: true,
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
      isEnableTrigger: false,
      isNameMatchingClassifed: [],
      selectedPage: -1,
      setisNameMatchingClassifed: false,
    }
  },
  computed: {
    batchId() {
      // return '20240220.100028'
      return this.$store.getters['batch/batch'].id
    },
    zoom() {
      return this.$store.getters['batch/zoom']
    },
    canvasWidth() {
      const maxWidth = max(this.pages.map(page => page.width))
      return maxWidth * this.zoom
    },
    canvasHeight() {
      const totalHeight = this.pages.map(page => page.height).reduce((a, b) => a + b, 0)
      return totalHeight * this.zoom
    },
    classificationData() {
      const data = this.$store.getters['classifications/getClassificationData']
      if (!this.setisNameMatchingClassifed) {
        data.data.forEach((item, index) => {
          this.isNameMatchingClassifed[index] = !!item.name_matching_doc_type
          this.setisNameMatchingClassifed = true
        })
      }
      return data
    },
    stageConfig() {
      return {
        width: window.innerWidth + PADDING * 2,
        height: window.innerHeight + PADDING * 2,
        x: -this.scrollX,
        y: -this.scrollY,
      }
    },
    leftMargin() {
      let margin = 0
      if (this.canvasWidth < this.containerSize?.width) {
        margin = (this.containerSize.width - this.canvasWidth) / 2
      }
      return margin
    },
    imageLayerConfig() {
      return {
        scaleX: this.zoom,
        scaleY: this.zoom,
      }
    },
    pageImages() {
      let pageY = 0
      return this.pages.map(page => {
        const pageConfig = {
          x: 0,
          y: pageY,
          image: page.image,
          pos: page.pos,
          width: page.width,
          height: page.height,
          id: page.id,
        }
        pageY += page.height
        return pageConfig
      })
    },
    pageYOffsets() {
      const offsets = {}
      this.pageImages.forEach(pageImge => {
        offsets[pageImge.id] = pageImge.y
      })
      return offsets
    },
    wordNodesConfig() {
      const triggers = []
      let pageY = 0

      const triggerPushing = (wordNode, index) => {
        if (wordNode.pos) {
          const positionInfo = wordNode.pos.split(',').map(num => +num)
          const x = positionInfo[0]
          const y = positionInfo[1] + pageY
          const width = positionInfo[2] - positionInfo[0]
          const height = positionInfo[3] - positionInfo[1]

          let fill = 'transparent'
          let opacity = 0.5
          if (this.selectedNodeIds.includes(wordNode.id) && this.classificationData.data[index].trigger.length === 0) {
            fill = 'yellow'
            opacity = 0.5
          }
          this.classificationData.data.forEach(item => {
            item.trigger.forEach(triggerItem => {
              if (triggerItem.ids.includes(wordNode.id)) {
                fill = 'yellow'
                opacity = 0.5
              }
            })
          })
          triggers.push({
            id: wordNode.id,
            x,
            y,
            width,
            height,
            fill,
            wordText: wordNode.v,
            opacity,
          })
        }
      }

      this.pages.forEach((page, index) => {
        const processNode = node => {
          if (node.type !== 'word' && node.children) {
            node.children.forEach(processNode)
          } else {
            triggerPushing(node, index)
          }
        }

        page.wordNodes.forEach(wordNodes => {
          wordNodes.children.forEach(processNode)
        })

        pageY += page.height
      })
      return triggers
    },
    extendedUserSelectedPatterns() {
      return this.$store.getters['atm/extendedUserSelectedPatterns']
    },
    multipleLineRecord() {
      return this.$store.getters['dataView/modelMultipleLineRecord']
    },
    multiLineRecordsConfig() {
      const multiLineRecords = []

      if (!this.extendedUserSelectedPatterns) {
        return multiLineRecords
      }

      this.extendedUserSelectedPatterns.forEach(item => {
        let pageY = null
        let pageId = null
        let batchId = null
        let left
        let top
        let right
        let bottom

        item.forEach(e => {
          // eslint-disable-next-line no-unused-vars
          const [itemLeft, itemTop, itemRight, itemBottom, itemPageId, _, itemBatchId] = e.pos.split(',')

          if (pageY == null || pageId == null || batchId == null) {
            pageY = this.pageYOffsets[itemPageId]
            pageId = itemPageId
            batchId = itemBatchId
          }

          if (!left || left > parseInt(itemLeft, 10)) {
            left = parseInt(itemLeft, 10)
          }

          if (!top || top > parseInt(itemTop, 10)) {
            top = parseInt(itemTop, 10)
          }

          if (!right || right < parseInt(itemRight, 10)) {
            right = parseInt(itemRight, 10)
          }

          if (!bottom || bottom < parseInt(itemBottom, 10)) {
            bottom = parseInt(itemBottom, 10)
          }
        })

        if (pageY != null && batchId === this.batchId) {
          const x = parseInt(left, 10)
          const y = parseInt(top, 10) + pageY
          const width = parseInt(right, 10) - parseInt(left, 10)
          const height = parseInt(bottom, 10) - parseInt(top, 10)

          multiLineRecords.push({
            x,
            y,
            width,
            height,
            fill: 'transparent',
            opacity: 0.6,
            pos: [left, top, right, bottom].join(','),
            pageId,
            // posRef: e.pos,
            // pattern,
            stroke: 'red',
            strokeWidth: 4,
          })
        }
      })

      return multiLineRecords
    },
    enableSelector() {
      return this.$store.getters['batch/enableSelector']
    },
    enableMeasure() {
      return this.$store.getters['batch/enableMeasure']
    },
    selectorPosition() {
      if (!this.selectorRectConfig.visible) {
        return null
      }

      let topPos = this.selectorRectConfig.y
      let pageId = ''
      let selectedPageIndex = -1

      // Calulate height respective to the page
      for (let pageIndex = 0; pageIndex < this.pages.length; pageIndex += 1) {
        const page = this.pages[pageIndex]
        if (topPos > page.height) {
          topPos -= page.height
        } else {
          pageId = page.id
          selectedPageIndex = pageIndex
          break
        }
      }

      return {
        startPos: this.selectorRectConfig.x.toString(),
        endPos: (this.selectorRectConfig.x + (this.selectorRectConfig.width * this.selectorRectConfig.scaleX)).toString(),
        topPos: topPos.toString(),
        bottomPos: (topPos + (this.selectorRectConfig.height * this.selectorRectConfig.scaleY)).toString(),
        pageId,
        pageIndex: selectedPageIndex,
      }
    },
    displayKeyAnchors() {
      return this.$store.getters['batch/displayKeyAnchors']
    },
    keyAnchorsData() {
      return this.$store.getters['batch/keyAnchorsData']
    },
  },
  watch: {
    selectorPosition: {
      handler() {
        this.$store.commit('batch/SET_SELECTOR_POSITION', this.selectorPosition)
      },
      deep: true,
    },
    measuredDistance: {
      handler() {
        this.$store.commit('batch/SET_MEASURED_DISTANCE', this.measuredDistance)
      },
      deep: true,
    },
    enableSelector() {
      if (this.enableSelector === false) {
        this.deleteSelector()
      }
    },
    enableMeasure() {
      if (this.enableMeasure === false) {
        this.deleteMeasure()
      }
    },
    pages() {
      this.pageY()
    },
  },
  created() {
    bus.$on('fitToWidthClassification', this.fitToWidth)
    bus.$on('scrollToHighlightedNode', this.scrollToHighlightedNode)
    bus.$on('scrollToPage', this.scrollToPage)
    localBus.$on('containerSizeChanged', this.onContainerSizeChange)
  },
  mounted() {
    this.setContainerSize()
    this.fitToWidth()
    resizeOb.observe(this.$refs.scrollContainer)
    this.scrollToHighlightedNode()
  },
  beforeDestroy() {
    resizeOb.unobserve(this.$refs.scrollContainer)
  },
  destroyed() {
    bus.$off('fitToWidthClassification', this.fitToWidth)
    bus.$off('scrollToHighlightedNode', this.scrollToHighlightedNode)
    bus.$off('scrollToPage', this.scrollToPage)
    localBus.$off('containerSizeChanged', this.onContainerSizeChange)
  },
  methods: {
    pageY() {
      const pageYList = []
      pageYList[0] = 0
      let pageY = 0
      this.pages.forEach((page, index) => {
        pageY += page.height
        pageYList[index + 1] = pageY
      })
      return pageYList
    },
    handleTransformEnd(e) {
      this.selectorRectConfig.x = e.target.x()
      this.selectorRectConfig.y = e.target.y()
      this.selectorRectConfig.rotation = e.target.rotation()
      this.selectorRectConfig.scaleX = e.target.scaleX()
      this.selectorRectConfig.scaleY = e.target.scaleY()
    },
    handleDragEnd(e) {
      this.selectorRectConfig.x = e.target.x()
      this.selectorRectConfig.y = e.target.y()
    },
    handleMouseEnter(e) {
      const container = e.target.getStage().container()
      container.style.cursor = 'pointer'
    },
    handleMouseLeave(e) {
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

        // Update line points
        const layer = this.$refs.layer.getNode()
        const pointerPosition = layer.getRelativePointerPosition()

        this.dragEndX = pointerPosition.x
        this.dragEndY = pointerPosition.y
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
      }
    },
    onScroll() {
      this.scrollX = this.$refs.scrollContainer.scrollLeft - PADDING
      this.scrollY = this.$refs.scrollContainer.scrollTop - PADDING
    },
    onContainerSizeChange() {
      this.setContainerSize()
    },
    setContainerSize() {
      this.containerSize = {
        width: this.$refs.scrollContainer.clientWidth,
        height: this.$refs.scrollContainer.clientHeight,
      }
    },
    fitToWidth() {
      if (!this.containerSize || this.pages.length === 0) {
        return
      }

      const pageWidth = max(this.pages.map(page => page.width))

      const widthZoom = this.containerSize.width / pageWidth
      this.$store.commit('batch/SET_ZOOM', widthZoom - 0.1)
    },
    scrollToHighlightedNode() {
      if (!this.$refs.highlightedNode) {
        return
      }
      this.$refs.scrollContainer.scrollTop = this.$refs.highlightedNode.offsetTop - 20
      this.$refs.scrollContainer.scrollLeft = this.$refs.highlightedNode.offsetLeft - 20
    },
    scrollToPage(pageId) {
      const pageConfig = this.pageImages.find(pageImage => pageImage.id === pageId)
      const { pos } = pageConfig
      if (!pageConfig) {
        return
      }
      const positionInfo = pos.split(',').map(num => +num)
      const x = positionInfo[0]
      const y = positionInfo[1] + pageConfig.y
      const width = positionInfo[2] - positionInfo[0]
      const height = positionInfo[3] - positionInfo[1]

      clearTimeout(this.scrollToPosTimer)

      this.scrollNodeConfig.x = x
      this.scrollNodeConfig.y = y
      this.scrollNodeConfig.width = width
      this.scrollNodeConfig.height = height
      this.scrollNodeConfig.visible = true

      this.$nextTick(() => {
        const { scrollContainer, scrollNode } = this.$refs

        scrollContainer.scrollTo({
          top: scrollNode.offsetTop - 20,
          left: scrollNode.offsetLeft - 20,
          behavior: 'smooth',
        })

        this.scrollToPosTimer = setTimeout(() => {
          this.scrollNodeConfig.visible = false
        }, 1500)
      })
    },
    nodeMouseEnterHandler(event) {
      if (this.classificationData.manual_classification_status !== 'ready') {
        return
      }
      const nodeId = event.target.attrs.id
      if (event.evt.shiftKey) {
        if (!this.selectedNodeIds.includes(nodeId)) {
          this.selectedNodeIds.push(nodeId)
        }
      } else {
        this.selectedNodeIds = [nodeId]
      }
    },
    nodeMouseLeaveHandler(event) {
      if (this.classificationData.manual_classification_status !== 'ready') {
        return
      }
      if (!event.evt.shiftKey) {
        this.selectedNodeIds = []
      }
    },
    nodeMouseDownHandler(event) {
      if (this.classificationData.manual_classification_status !== 'ready') {
        return
      }
      event.evt.preventDefault()

      if (this.selectedNodeIds.length === 0) {
        return
      }

      const triggers = []
      const triggerPushing = (wordNode, pageId) => {
        triggers.push({
          pageId,
          ...wordNode,
        })
      }
      this.pages.forEach(page => {
        const processNode = node => {
          if (node.type !== 'word' && node.children) {
            node.children.forEach(processNode)
          } else {
            triggerPushing(node, page.id)
          }
        }
        page.wordNodes.forEach(wordNodes => {
          wordNodes.children.forEach(processNode)
        })
      })
      const selectedNodes = triggers.filter(node => this.selectedNodeIds.includes(node.id))
      const { pageId, s } = selectedNodes[0]
      const pageIndex = this.pages.findIndex(page => page.id === pageId)

      const classificationData = { ...this.classificationData }
      if (classificationData.data[pageIndex].name_matching_doc_type && this.isNameMatchingClassifed[pageIndex]) {
        this.isEnableTrigger = true
        this.selectedPage = pageIndex
        return
      }

      if (pageId === selectedNodes[0].pageId && classificationData.data[pageIndex].trigger.length) {
        if (classificationData.data[pageIndex].trigger[0].ids.some(element => this.selectedNodeIds.includes(element))) {
          classificationData.data[pageIndex].trigger = []
          this.$store.commit('classifications/SET_VERIFIED', false)
          this.$store.commit('classifications/SET_CLASSIFICATION_DATA', classificationData)
        }
        return
      }

      const text = selectedNodes.map(node => node.v).join(' ')
      const startPos = min(selectedNodes.map(node => +node.pos.split(',')[0])).toString()
      const topPos = min(selectedNodes.map(node => +node.pos.split(',')[1])).toString()
      const endPos = max(selectedNodes.map(node => +node.pos.split(',')[2])).toString()
      const bottomPos = max(selectedNodes.map(node => +node.pos.split(',')[3])).toString()

      const positonInfo = `${startPos},${topPos},${endPos},${bottomPos}`

      const value = {
        pattern: text,
        pos: positonInfo,
        style_id: s,
        ids: this.selectedNodeIds,
      }

      classificationData.data[pageIndex].trigger[0] = value
      this.$store.commit('classifications/SET_VERIFIED', false)
      this.$store.commit('classifications/SET_CLASSIFICATION_DATA', classificationData)
    },
    createSelector(x, y, width, height) {
      this.selectorRectConfig.x = x
      this.selectorRectConfig.y = y
      this.selectorRectConfig.width = width
      this.selectorRectConfig.height = height
      this.selectorRectConfig.scaleX = 1
      this.selectorRectConfig.scaleY = 1
      this.selectorRectConfig.visible = true
      // Attach transformer
      const transformerNode = this.$refs.transformer.getNode()
      transformerNode.nodes([this.$refs.selectorRect.getNode()])
    },
    deleteSelector() {
      this.selectorRectConfig.visible = false
      // Detach transformer
      const transformerNode = this.$refs.transformer.getNode()
      transformerNode.nodes([])
    },
    setTriggerEnablement(index, value) {
      this.isEnableTrigger = false
      this.selectedPage = -1
      this.isNameMatchingClassifed[index] = value
    },
  },
}
</script>

<style scoped>
.scroll-container {
    overflow: auto;
    height: 100%;
}
.large-container {
    overflow: hidden;
    position: relative;
}
.highlighted-node, .scroll-node {
    position: absolute;
}
</style>
