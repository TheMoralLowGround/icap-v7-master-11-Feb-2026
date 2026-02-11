<template>
  <feather-icon
    v-b-tooltip.hover
    icon="CropIcon"
    size="20"
    class="cursor-pointer"
    :class="{
      'text-primary':enableSelector
    }"
    title="Selector"
    @click="toggleSelector"
  />
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  computed: {
    // Enable selector option
    enableSelector() {
      return this.$store.getters['batch/enableSelector']
    },
  },
  methods: {
    toggleSelector() {
      this.$store.dispatch('batch/toggleSelector')
    },
  },
}
</script>
