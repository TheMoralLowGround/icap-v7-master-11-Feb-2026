<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="40"
    height="40"
    viewBox="0 0 24 24"
  >
    <!-- Gradient Definition -->
    <defs>
      <linearGradient
        id="robotGradient"
        x1="0%"
        y1="0%"
        x2="100%"
        y2="100%"
      >
        <stop
          offset="0%"
          :stop-color="robotColor.start"
        />
        <stop
          offset="100%"
          :stop-color="robotColor.end"
        />
      </linearGradient>
    </defs>

    <!-- Robot Head -->
    <path
      fill="url(#robotGradient)"
      d="M5 21q-.425 0-.712-.288T4 20v-4q0-.825.588-1.412T6 14h12q.825 0 1.413.588T20 16v4q0 .425-.288.713T19 21zm4-8q-2.075 0-3.537-1.463T4 8t1.463-3.537T9 3h6q2.075 0 3.538 1.463T20 8t-1.463 3.538T15 13zm-3 6h12v-3H6z"
    />

    <!-- Eyes -->
    <circle
      cx="9"
      cy="8"
      r="1.2"
      :fill="eyeColor"
    />
    <circle
      cx="15"
      cy="8"
      r="1.2"
      :fill="eyeColor"
    />

    <!-- Antenna -->
    <rect
      x="11"
      y="1"
      width="2"
      height="3"
      rx="1"
      :fill="antennaColor"
    />

    <!-- Glowing effect when blinking -->
    <circle
      v-if="shouldBlink"
      cx="12"
      cy="2.5"
      r="1.5"
      fill="orange"
      opacity="0.8"
      filter="url(#glow)"
    />

    <!-- Optional Glow Effect -->
    <filter id="glow">
      <feGaussianBlur
        stdDeviation="1.5"
        result="coloredBlur"
      />
      <feMerge>
        <feMergeNode in="coloredBlur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </svg>
</template>

<script>
import { mapState } from 'vuex'

export default {
  props: {
    renderedKeyNodes: {
      type: [String, Number],
      default: () => 0,
    },
  },
  computed: {
    ...mapState('batch', ['isAgentBlink']),

    shouldBlink() {
      return this.isAgentBlink && Number(this.renderedKeyNodes || 1) > 0
    },

    robotColor() {
      return {
        start: this.shouldBlink ? '#ff9800' : '#9e9e9e',
        end: this.shouldBlink ? '#ff5722' : '#616161',
      }
    },

    eyeColor() {
      return this.shouldBlink ? '#ffeb3b' : '#37474f'
    },

    antennaColor() {
      return this.shouldBlink ? '#ff5722' : '#616161'
    },
  },
}
</script>
