<template>
  <div
    id="donutchart"
    style="width: 900px; height: 500px;"
  />
</template>

<script>
import { GoogleCharts } from 'google-charts'

export default {
  mounted() {
    this.loadGoogleCharts()
  },
  methods: {
    loadGoogleCharts() {
      GoogleCharts.load(this.drawChart)
    },
    drawChart() {
      const data = GoogleCharts.api.visualization.arrayToDataTable([
        ['Task', 'Hours per Day'],
        ['Work', 8],
        ['Eat', 2],
        ['TV', 4],
        ['Gym', 2],
        ['Sleep', 8],
      ])

      const options = {
        title: 'My Daily Activities',
        pieHole: 0.4, // This makes it a Donut Chart
      }

      const chart = new GoogleCharts.api.visualization.PieChart(document.getElementById('donutchart'))
      chart.draw(data, options)
    },
  },
}
</script>
