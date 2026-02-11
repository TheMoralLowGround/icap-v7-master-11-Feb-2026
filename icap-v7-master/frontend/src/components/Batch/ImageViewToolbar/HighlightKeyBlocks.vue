<template>
  <feather-icon
    v-b-tooltip.hover
    icon="GridIcon"
    size="22"
    class="cursor-pointer"
    :class="{
      'text-primary':highlightKeyBlocks
    }"
    title="Highlight Key Blocks"
    @click="toggleHightlightKeyBlocks"
  />
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  computed: {
    // Get highlight Key Blocks
    highlightKeyBlocks() {
      return this.$store.getters['batch/highlightKeyBlocks']
    },
  },
  methods: {
    // dispatch toggle Highlight Key Blocks
    toggleHightlightKeyBlocks() {
      this.$store.dispatch('batch/toggleHighlightKeyBlocks')
    },
  },
}
</script>
