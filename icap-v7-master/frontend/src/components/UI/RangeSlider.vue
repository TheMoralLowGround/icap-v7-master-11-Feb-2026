<template>
  <vue-slider
    v-model="rangeValue"
    :min="min"
    :max="max"
  />
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import VueSlider from 'vue-slider-component'
import 'vue-slider-component/theme/default.css'

export default {
  components: {
    VueSlider,
  },
  props: {
    value: {
      type: Number,
      required: true,
    },
    min: {
      type: Number,
      required: false,
      default: 0,
    },
    max: {
      type: Number,
      required: false,
      default: 100,
    },
  },
  data() {
    return {
      rangeValue: 0,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.rangeValue)
    },
  },
  watch: {
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.rangeValue = cloneDeep(this.value)
    },
  },
}
</script>
