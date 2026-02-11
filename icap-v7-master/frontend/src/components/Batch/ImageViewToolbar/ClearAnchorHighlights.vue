<template>
  <!-- Feather icon with tooltip to Clear Anchor Highlights -->
  <feather-icon
    v-b-tooltip.hover
    icon="AnchorIcon"
    size="22"
    class="cursor-pointer text-primary"
    title="Clear Anchor Highlights"
    @click="clear"
  />
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  methods: {
    // clear anchor highlights
    clear() {
      this.$store.dispatch('batch/clearAnchorHighlights')
    },
  },
}
</script>
