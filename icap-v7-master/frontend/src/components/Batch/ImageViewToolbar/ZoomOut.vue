<template>
  <feather-icon
    v-b-tooltip.hover
    icon="ZoomOutIcon"
    size="20"
    class="cursor-pointer"
    title="Zoom Out"
    @click="zoomOut"
  />
</template>

<script>
import bus from '@/bus'
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  computed: {
    // Checks if the current batch is an Excel batch
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
  },
  methods: {
    // called zoomOut from store
    zoomOut() {
      if (!this.isExcelBatch) {
        this.$store.dispatch('batch/zoomOut')
      } else {
        bus.$emit('excelZoomOut')
      }
    },
  },
}
</script>
