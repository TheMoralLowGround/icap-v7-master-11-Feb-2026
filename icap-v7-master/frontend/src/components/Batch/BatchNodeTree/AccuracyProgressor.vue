<template>
  <div class="d-flex justify-content-center align-items-center">
    <div
      class="accuracy-circle"
      :style="circleStyle"
    >
      <svg
        viewBox="0 0 36 36"
        class="circular-chart"
        :class="circleColor"
      >
        <path
          class="circle-bg"
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
        />
        <path
          class="circle"
          :stroke-dasharray="`${percentage}, 100`"
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
        />
        <text
          x="18"
          y="20.35"
          class="percentage-text"
          :class="circleColor"
        >{{ percentage }}</text>
      </svg>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AccuracyCircle',
  props: {
    percentage: {
      type: Number,
      default: 80,
      validator: value => value >= 0 && value <= 100,
    },
    lowThreshold: {
      type: Number,
      default: 50,
    },
    mediumThreshold: {
      type: Number,
      default: 80,
    },
    lowColor: {
      type: String,
      default: 'danger',
    },
    mediumColor: {
      type: String,
      default: 'warning',
    },
    highColor: {
      type: String,
      default: 'success',
    },
  },
  computed: {
    circleColor() {
      if (this.percentage < this.lowThreshold) return this.lowColor
      if (this.percentage < this.mediumThreshold) return this.mediumColor
      return this.highColor
    },
    circleStyle() {
      return {
        width: '28px',
        height: '28px',
      }
    },
  },
}
</script>

<style scoped>
.circular-chart {
  width: 100%;
  height: 100%;
  transform: rotate(0deg);
}
.circle-bg {
  fill: none;
  stroke: #eee;
  stroke-width: 3.8;
}
.circle {
  fill: none;
  stroke-width: 3.8;
  stroke-linecap: round;
  stroke: currentColor;
  transition: stroke-dasharray 0.5s ease;
}
.percentage-text {
  /* fill: #6e6b7b;   */
  font-size: 13px;
  font-weight: bold;
  text-anchor: middle;
}
.success {
  color: #28a745;
  fill: #28a745; /* <-- Add this */
}
.warning {
  color: #ffc107;
  fill: #ffc107; /* <-- Add this */
}
.danger {
  color: #dc3545;
  fill: #dc3545; /* <-- Add this */
}
</style>
