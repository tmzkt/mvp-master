<template>
  <div class="chart">
    <bar-chart :height="400" :chart-data="collection"></bar-chart>
  </div>
</template>

<script>
import BarChart from "./BarChart.js";

export default {
  components: {
    BarChart,
  },
  props: {
    collection: Object,
  },
};
</script>
<style src="./chart.scss" lang="scss"></style>
