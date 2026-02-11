<template>
  <feather-icon
    v-b-tooltip.hover
    icon="RotateCcwIcon"
    size="20"
    class="cursor-pointer"
    title="Undo Key Mapping"
    @click="undoKeyMapping"
  />
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  methods: {
    undoKeyMapping() {
      this.$emit('click')
    },
  },
}
</script>
