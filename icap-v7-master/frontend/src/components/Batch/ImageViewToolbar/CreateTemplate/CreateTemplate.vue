<template>
  <div>
    <!-- Feather icon with tooltip to trigger the Create template data modal -->
    <feather-icon
      v-b-tooltip.hover
      icon="ClipboardIcon"
      size="20"
      class="cursor-pointer"
      title="Create template"
      @click="copyData"
    />

    <!-- Modal for Create template data, shown only when `showModal` is true -->
    <create-template-modal
      v-if="showModal"
      @modal-closed="showModal = false"
    />
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import CreateTemplateModal from './CreateTemplateModal.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    CreateTemplateModal,
  },
  data() {
    return {
      showModal: false, // Boolean to control the visibility of the modal
    }
  },
  methods: {
    // Method to show the modal
    copyData() {
      this.showModal = true
    },
  },
}
</script>
