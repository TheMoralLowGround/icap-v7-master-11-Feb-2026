<template>
  <div>
    <b-button
      id="open-popover-test-options"
      size="sm"
      :variant="isPopoverOpen ? 'primary' : 'outline-primary'"
      @click="togglePopover"
    >
      Test
    </b-button>
    <b-popover
      target="open-popover-test-options"
      placement="bottom"
      boundary="scrollParent"
      custom-class="less-padding-popover low-z-index-popover"
      triggers="manual"
      :show="isPopoverOpen"
      @show="isPopoverOpen = true"
      @hide="isPopoverOpen = false"
    >
      <div>
        <TestOptions
          test-batch-title="Set"
          test-transaction-title="Batch"
          test-document-title="Document"
          custom-variant-class="btn-xs"
        />
      </div>
    </b-popover>
  </div>
</template>

<script>
import { BPopover, BButton } from 'bootstrap-vue'
import TestOptions from '../DataViewToolbar/TestOptions.vue'

export default {
  components: {
    BPopover,
    BButton,
    TestOptions,
  },
  data() {
    return {
      isPopoverOpen: false,
    }
  },
  mounted() {
    document.addEventListener('click', this.handleOutsideClick)
  },
  beforeDestroy() {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  methods: {
    togglePopover() {
      this.isPopoverOpen = !this.isPopoverOpen
    },
    handleOutsideClick(event) {
      if (!this.isPopoverOpen) return

      // Get the button and popover elements
      const button = document.getElementById('open-popover-test-options')
      const popover = document.querySelector('.popover')

      // Check if click was outside both button and popover
      const clickedOutsideButton = button && !button.contains(event.target)
      const clickedOutsidePopover = popover && !popover.contains(event.target)

      if (clickedOutsideButton && clickedOutsidePopover) {
        this.isPopoverOpen = false
      }
    },
  },
}
</script>

<style scoped>
.btn-sm {
    padding: 0.486rem 0.75rem;
    border-radius: 0.358rem;
}

.low-z-index-popover {
  z-index: 50 !important;
}
</style>

<style>
.less-padding-popover .popover-body {
  padding: 0.65rem !important;
}
</style>
