<template>
  <!-- Badge component to display the batch definition version -->
  <b-badge
    v-if="batchDefintionVersion"
    v-b-tooltip.hover
    :title="tooltipText"
    variant="primary"
  >
    <!-- Displays the batch definition version as the badge text -->
    {{ batchDefintionVersion }}
  </b-badge>
</template>

<script>
import { BBadge, VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BBadge,
  },
  computed: {
    // Computes the batch definition version, converts it to uppercase, or returns null if not available.
    batchDefintionVersion() {
      return this.$store.getters['batch/batch'].definitionVersion?.toUpperCase() || null
    },
    // Generates the tooltip text using the batch definition version.
    tooltipText() {
      return `Batch tested with ${this.batchDefintionVersion} version of definition`
    },
  },
}
</script>
