<template>
  <div>
    <div
      v-if="tableColumns && tableColumns.length > 0"
      class="lookup-data-section mt-2"
    >
      <h6 class="mb-2">
        Lookup Results
      </h6>
      <!-- Loading state -->
      <div
        v-if="loading"
        class="text-center my-3"
      >
        <b-spinner class="mr-2" />
        <span>Running lookup...</span>
      </div>

      <!-- Results table -->
      <b-table
        v-else
        :items="lookupResults"
        :fields="tableFields"
        responsive
        striped
        small
        show-empty
      >
        <!-- Empty state -->
        <template #empty>
          <div class="pl-5 text-muted py-2">
            No results found
          </div>
        </template>
      </b-table>
    </div>
  </div>

</template>

<script>
import { BTable, BSpinner } from 'bootstrap-vue'

export default {
  components: {
    BTable,
    BSpinner,
  },
  props: {
    lookupResults: {
      type: Array,
      default: () => [],
    },
    tableColumns: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    tableFields() {
      if (!this.tableColumns || this.tableColumns.length === 0) {
        return []
      }

      // Get all unique keys from the results
      return this.tableColumns
    },
  },
  methods: {
    // formatLabel(key) {
    //   // Convert snake_case or camelCase to Title Case
    //   return key
    //     .replace(/_/g, ' ')
    //     .replace(/([A-Z])/g, ' $1')
    //     .trim()
    //     .split(' ')
    //     .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    //     .join(' ')
    // },
  },
}
</script>

<style scoped>
.lookup-data-section {
  border: 1px solid #dee2e6;
  border-radius: 5px;
  padding: 15px;
}

.lookup-results-table {
  margin-bottom: 0;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
