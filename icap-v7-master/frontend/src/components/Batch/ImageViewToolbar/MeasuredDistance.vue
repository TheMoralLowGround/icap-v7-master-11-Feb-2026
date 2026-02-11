<template>
  <div
    class="d-flex align-items-center measured-data"
  >
    <label for="x-distance">X Distance</label>
    <b-form-input
      id="x-distance"
      v-model="xDistance"
      class="special-width"
      readonly
    />

    <label for="y-distance">Y Distance</label>
    <b-form-input
      id="y-distance"
      v-model="yDistance"
      class="special-width"
      readonly
    />
  </div>
</template>

<script>
import {
  BFormInput,
} from 'bootstrap-vue'

export default {
  components: {
    BFormInput,
  },
  computed: {
    mesasuredDistance() {
      return this.$store.getters['batch/measuredDistance']
    },
    xDistance() {
      if (this.mesasuredDistance) {
        return this.mesasuredDistance.xDistance
      }
      return ''
    },
    yDistance() {
      if (this.mesasuredDistance) {
        return this.mesasuredDistance.yDistance
      }
      return ''
    },
  },
}
</script>

<style lang="scss" scoped>
.measured-data {
  column-gap: 1rem;

  ::v-deep .special-width {
    width: 100px;
  }
}
</style>
