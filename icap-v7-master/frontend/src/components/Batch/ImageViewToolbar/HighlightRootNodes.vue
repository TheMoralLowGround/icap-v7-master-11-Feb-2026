<template>
  <feather-icon
    v-b-tooltip.hover
    icon="MenuIcon"
    size="22"
    class="cursor-pointer"
    :class="{
      'text-primary':highlightRootNodes
    }"
    title="Highlight Root Nodes"
    @click="toggleHightlightRootNodes"
  />
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  computed: {
    highlightRootNodes() {
      return this.$store.getters['batch/highlightRootNodes']
    },
  },
  methods: {
    toggleHightlightRootNodes() {
      this.$store.dispatch('batch/toggleHighlightRootNodes')
    },
  },
}
</script>
