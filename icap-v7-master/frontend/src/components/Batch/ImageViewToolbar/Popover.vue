<template>
  <div class="popover-container">
    <feather-icon
      id="open-popover-options"
      v-b-tooltip.hover
      icon="SlidersIcon"
      size="20"
      :class="['cursor-pointer', { 'text-primary': isPopoverOpen }]"
      title="View Options"
      @click="togglePopover"
    />
    <b-popover
      target="open-popover-options"
      placement="bottom"
      boundary="scrollParent"
      custom-class="no-padding-popover low-z-index-popover"
      triggers="manual"
      :show="isPopoverOpen"
      @show="isPopoverOpen = true"
      @hide="isPopoverOpen = false"
    >
      <div class="py-1">
        <slot />
      </div>
    </b-popover>
  </div>
</template>

<script>
import { VBTooltip, BPopover } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BPopover,
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

      // Get the icon and popover elements
      const icon = document.getElementById('open-popover-options')
      const popover = document.querySelector('.popover')

      // Check if click was outside both icon and popover
      const clickedOutsideIcon = icon && !icon.contains(event.target)
      const clickedOutsidePopover = popover && !popover.contains(event.target)

      if (clickedOutsideIcon && clickedOutsidePopover) {
        this.isPopoverOpen = false
      }
    },
  },
}
</script>

<style scoped>
.popover-container {
  display: inline-block;
}

.low-z-index-popover {
  z-index: 50 !important;
}
</style>
