<template>
  <div class="d-flex align-items-center measure-wrapper">
    <feather-icon
      v-b-tooltip.hover
      icon="ItalicIcon"
      size="22"
      class="cursor-pointer"
      :class="{
        'text-primary':enableMeasure
      }"
      title="Measure"
      @click="toggleMeasure"
    />
    <measured-distance v-if="enableMeasure" />
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import MeasuredDistance from './MeasuredDistance.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    MeasuredDistance,
  },
  computed: {
    enableMeasure() {
      return this.$store.getters['batch/enableMeasure']
    },
  },
  methods: {
    toggleMeasure() {
      this.$store.dispatch('batch/toggleMeasure')
    },
  },
}
</script>

<style scoped>
.measure-wrapper{
  column-gap: 1rem;
}
</style>
