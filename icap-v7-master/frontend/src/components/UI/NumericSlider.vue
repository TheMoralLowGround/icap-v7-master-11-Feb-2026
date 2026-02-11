<template>
  <div class="d-flex align-items-center slider-container">
    <div>{{ inputValue }}</div>
    <RangeSlider
      v-model="inputValue"
      class="w-100 mx-1"
      :min="parseInt(field.minValue, 10)"
      :max="parseInt(field.maxValue, 10)"
    />
  </div>
</template>

<script>
import RangeSlider from '@/components/UI/RangeSlider.vue'

export default {
  components: {
    RangeSlider,
  },
  props: {
    value: {
      type: [String, Number],
      required: false,
      default() {
        return 0
      },
    },
    field: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      inputValue: 0,
    }
  },
  computed: {
    out() {
      return this.inputValue
    },
  },
  watch: {
    out: {
      handler(val) {
        if (val !== this.value) {
          this.$emit('input', val)
        }
      },
    },
    value: {
      handler(val) {
        if (val !== this.out) {
          this.setInternalState()
        }
      },
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.inputValue = parseInt(this.value, 10)
    },
  },
}
</script>

<style lang="scss" scoped>
.slider-container {
  margin-top: 0.5rem;
}
</style>
