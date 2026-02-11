<template>
  <div>
    <!-- Feather icon with tooltip to trigger the copy definition data modal -->
    <feather-icon
      v-b-tooltip.hover
      icon="CopyIcon"
      size="20"
      class="cursor-pointer"
      title="Copy Definition Data"
      @click="copyData"
    />
    <!-- Modal for copying definition data, shown only when `showModal` is true -->
    <copy-data-modal
      v-if="showModal"
      @modal-closed="showModal = false"
    />
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import CopyDataModal from './CopyDataModal.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip, // Registering the Bootstrap tooltip directive
  },
  components: {
    CopyDataModal, // Registering the CopyDataModal component
  },
  data() {
    return {
      showModal: false, // Boolean to control the visibility of the modal
    }
  },
  methods: {
    // Method to show the modal
    copyData() {
      this.showModal = true // Sets showModal to true, making the modal visible
    },
  },
}
</script>
