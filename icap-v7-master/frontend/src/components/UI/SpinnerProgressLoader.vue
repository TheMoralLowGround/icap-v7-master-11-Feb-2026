<template>
  <div class="demo-vertical-spacing d-flex flex-column justify-content-center align-items-center">
    <b-spinner
      :height="status === 'inprogress' ? '12px' : ''"
      variant="primary"
    />

    <strong
      v-if="status === 'inprogress'"
      style="color: #7367F0;"
    >
      {{ elapsedTime }} / {{ totalTime }}
    </strong>
  </div>
</template>
<script>
import { BSpinner } from 'bootstrap-vue'

export default {
  components: {
    BSpinner,
  },
  props: {
    max: {
      type: Number,
      required: true,
    },
    status: {
      type: String,
      required: false,
      default: 'completed',
    },
  },
  data() {
    return {
      value: 0,
      timer: null,
    }
  },
  computed: {
    elapsedTime() {
      return this.getTime(this.value)
    },
    totalTime() {
      return this.getTime(this.max + 3)
    },
  },
  watch: {
    status(newVal) {
      if (newVal !== 'inprogress') {
        clearInterval(this.timer)

        return
      }

      this.timer = setInterval(() => {
        if (this.value <= Math.ceil(this.max)) {
          this.value += 1
        }
      }, 1000)
    },
  },
  beforeDestroy() {
    clearInterval(this.timer)
  },
  methods: {
    getTime(secs) {
      const minutes = Math.floor(secs / 60)
      const seconds = Math.ceil(secs - minutes * 60)

      if (minutes === 0) {
        return `${seconds}s`
      }

      return `${minutes}m ${seconds}s`
    },
  },
}
</script>
