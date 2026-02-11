<template>
  <!-- Feather icon with tooltip to reset Fit to Width -->
  <feather-icon
    v-b-tooltip.hover
    icon="MinimizeIcon"
    size="20"
    class="cursor-pointer"
    title="Fit to Width"
    @click="fitToWidth"
  />
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import bus from '@/bus'

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
    // Reset Fit to Width
    fitToWidth() {
      if (!this.isExcelBatch) {
        bus.$emit('fitToWidth', true)
      } else {
        bus.$emit('excelFitToWidth')
      }
    },
  },
}
</script>
