<template>
  <div>
    <splitpanes class="default-theme">
      <pane
        size="25"
        max-size="25"
        class="pan-container"
      >
        <div class="h-100">
          <!-- <div class="node-tree-conent d-flex flex-column h-100"> -->
          <vue-perfect-scrollbar
            :settings="perfectScrollbarSettings"
            class="scroller-container scroll-area"
          >
            <div class="flex-grow-1">
              <LeftTree />
            </div>
          </vue-perfect-scrollbar>
          <!-- </div> -->
        </div>
      </pane>
      <pane
        size="75"
        class="pan-container"
      >
        <div
          class="h-100"
          @click="clearTreeDocSelection"
        >
          <DataViewer />
        </div>
      </pane>
    </splitpanes>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import VuePerfectScrollbar from 'vue-perfect-scrollbar'
import DataViewer from '@/components/Classification/DataViewer.vue'
import LeftTree from '@/components/Classification/LeftTree.vue'
// import {
//   BCard,
// } from 'bootstrap-vue'
import 'splitpanes/dist/splitpanes.css'
import bus from '@/bus'

export default {
  components: {
    Splitpanes,
    Pane,
    // BCard,
    DataViewer,
    LeftTree,
    VuePerfectScrollbar,
  },
  data() {
    return {
      perfectScrollbarSettings: {
        maxScrollbarLength: 80,
        wheelPropagation: false,
      },
    }
  },
  created() {
    this.$forceNextTick(() => {
      bus.$emit('fitToWidthClassification')
    })
  },
  methods: {
    clearTreeDocSelection() {
      bus.$emit('classification/clearTreeDocSelection')
    },
  },
}
</script>

<style scoped lang="scss">
.card-body {
  padding: .5rem;
}
.pan-container {
  height: calc(100vh - 129px);
}
.node-tree-conent {
  overflow-y: auto;
}
.scroller-container {
    height:100%;
    position:relative;
}
</style>
