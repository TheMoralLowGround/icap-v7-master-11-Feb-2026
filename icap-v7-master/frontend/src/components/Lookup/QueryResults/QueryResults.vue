<template>
  <div
    class="query-results-container"
  >
    <b-overlay
      class="h-100"
      :show="executingLookup"
      :opacity="0.6"
    >
      <template #overlay>
        &nbsp;
      </template>

      <div
        class="query-results-content"
      >
        <div
          v-if="results.length === 0"
          class="text-center"
        >
          Run lookup to see the results
        </div>
        <query-result
          v-if="resultIndex != null"
          :result="results[resultIndex]"
          :search="search"
        />
      </div>
    </b-overlay>
  </div>
</template>

<script>
import { BOverlay } from 'bootstrap-vue'
import QueryResult from './QueryResult.vue'

export default {
  components: {
    QueryResult,
    BOverlay,
  },
  computed: {
    resultIndex() {
      return this.$store.getters['lookup/resultIndex']
    },
    results() {
      return this.$store.getters['lookup/results']
    },
    search() {
      return this.$store.getters['lookup/search']
    },
    executingLookup() {
      return this.$store.getters['lookup/executing']
    },
  },
}
</script>

<style scoped lang="scss">
.query-results-container {
    height: 100%;
    position: relative;
}
.query-results-content {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
}
</style>
