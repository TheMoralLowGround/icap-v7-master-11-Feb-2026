<template>
  <feather-icon
    v-b-tooltip.hover
    icon="ZoomInIcon"
    size="20"
    class="cursor-pointer"
    title="Zoom In"
    @click="zoomIn"
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
    // called zoomIn from store
    zoomIn() {
      if (!this.isExcelBatch) {
        this.$store.dispatch('batch/zoomIn')
      } else {
        bus.$emit('excelZoomIn')
      }
    },
  },
}
</script>
