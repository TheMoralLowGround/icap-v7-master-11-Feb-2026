<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="40"
    height="40"
    viewBox="0 0 24 24"
  >
    <defs>
      <linearGradient
        id="robotGradient2"
        x1="0%"
        y1="0%"
        x2="100%"
        y2="100%"
      >
        <stop
          offset="0%"
          stop-color="#cccccc"
        />
        <stop
          offset="100%"
          stop-color="#a0a0a0"
        />
      </linearGradient>
    </defs>

    <path
      fill="url(#robotGradient2)"
      d="M5 21q-.425 0-.712-.288T4 20v-4q0-.825.588-1.412T6 14h12q.825 0 1.413.588T20 16v4q0 .425-.288.713T19 21zm4-8q-2.075 0-3.537-1.463T4 8t1.463-3.537T9 3h6q2.075 0 3.538 1.463T20 8t-1.463 3.538T15 13zm-3 6h12v-3H6z"
    />
    <circle
      cx="9"
      cy="8"
      r="1.2"
      fill="#546e7a"
    />
    <circle
      cx="15"
      cy="8"
      r="1.2"
      fill="#546e7a"
    />
    <rect
      x="11"
      y="1"
      width="2"
      height="3"
      rx="1"
      fill="#a0a0a0"
    />
  </svg>
</template>

<script>
export default {
  name: 'RobotIcon',
}
</script>
