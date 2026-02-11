<template>
  <div>
    <feather-icon
      v-b-tooltip.hover
      icon="UploadIcon"
      size="20"
      class="cursor-pointer"
      title="Import Data"
      @click="importData"
    />
    <import-data
      v-if="showModal"
      @modal-closed="showModal = false"
    />
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import ImportData from '@/components/Lookup/ImportData/ImportData.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    ImportData,
  },
  data() {
    return {
      showModal: false,
    }
  },
  methods: {
    importData() {
      this.showModal = true
    },
  },
}
</script>
