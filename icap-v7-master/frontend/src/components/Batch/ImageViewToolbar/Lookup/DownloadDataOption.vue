<template>
  <div>
    <feather-icon
      v-b-tooltip.hover
      icon="DownloadIcon"
      size="20"
      class="cursor-pointer"
      title="Download Data"
      @click="downloadData"
    />
    <download-data
      v-if="showModal"
      @modal-closed="showModal = false"
    />
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import DownloadData from '@/components/Lookup/DownloadData/DownloadData.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    DownloadData,
  },
  data() {
    return {
      showModal: false,
    }
  },
  methods: {
    downloadData() {
      this.showModal = true
    },
  },
}
</script>
