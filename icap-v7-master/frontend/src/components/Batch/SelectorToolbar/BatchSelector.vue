<template>
  <div class="d-flex align-items-center">
    <!-- v-select for selecting a batch with a loading spinner -->
    <v-select
      ref="vSelect"
      v-model="batchId"
      :clearable="false"
      :options="batchOptions"
      :loading="dataViewLoading"
      style="width: 100%"
      class="batch-selector"
      @open="scrollToSelected"
      @option:selecting="onOptionSelecting"
    >
      <!-- Custom spinner template -->
      <template #spinner="{ loading }">
        <b-spinner
          v-if="loading"
          variant="primary"
          small
        />
      </template>
    </v-select>
  </div>
</template>

<script>
import vSelect from 'vue-select'
import {
  BSpinner,
  // BFormCheckbox,
} from 'bootstrap-vue'
import bus from '@/bus' // Import a shared event bus for communication between components

export default {
  components: {
    vSelect,
    BSpinner,
    // BFormCheckbox,
  },
  computed: {
    isTrainingMode() {
      return this.$route.query['transaction-type'] === 'training'
    },
    // Gets and sets the selected batch ID via Vuex
    batchId: {
      get() {
        return this.$store.getters['batch/batch']?.id
      },
      async set(value) {
        // Always update route query parameter to trigger node expansion
        // The route watcher will check isClickHandling flag to prevent flickering
        await this.$router.replace({
          name: this.$route.name,
          params: this.$route.params,
          query: {
            ...this.$route.query,
            'batch-id': value,
          },
        })

        this.$store.dispatch('batch/changeBatch', value)

        // this.$store.dispatch('dataView/onChangeBatch', { batchId: value, refresh: false }
      },
    },
    batch() {
      return this.$store.getters['batch/batch']
    },
    // Retrieves batch options from Vuex
    // options() {
    //   return this.$store.getters['dataView/batchesByDefinitionType']
    // },
    // Tracks loading state for batch options
    dataViewLoading() {
      return this.$store.getters['dataView/loading']
    },
    batchesIds() {
      return this.$store.getters['batch/batchesIds']
    },
    trainingBatchLinkedIds() {
      return this.$store.getters['batch/trainingBatchLinkedIds']
    },
    batchOptions() {
      const transactionId = this.$route.params.id
      // Use trainingBatchLinkedIds only if both conditions are met:
      // 1. It's in training mode
      // 2. Transaction ID starts with 'multi_'
      const options = (this.isTrainingMode && transactionId?.startsWith('multi_'))
        ? this.trainingBatchLinkedIds
        : this.batchesIds

      // Sort the options in ascending order based on numeric part after "US"
      return this.sortBatchIds(options)
    },
    selectedTransactionId() {
      return this.$store.getters['batch/selectedTransactionId']
    },
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    currentRouteName() {
      return this.$route.name // Returns the current route name from Vue Router
    },
  },
  watch: {
    // 'batch.layoutId': {
    //   async handler() {
    //     await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
    //   },
    //   deep: true,
    // },
  },
  methods: {
    // Sorts batch IDs in ascending order based on the numeric part after "US"
    // Example: M20251007.US100031 -> extracts 100031 for sorting
    sortBatchIds(batchIds) {
      if (!batchIds || !Array.isArray(batchIds)) {
        return batchIds
      }

      // Create a copy to avoid mutating the original array
      const sorted = [...batchIds]

      return sorted.sort((a, b) => {
        // Extract numeric part after "US" from each batch ID
        const extractNumericPart = batchId => {
          if (typeof batchId !== 'string') return 0
          const match = batchId.match(/US(\d+)/)
          return match ? parseInt(match[1], 10) : 0
        }

        const numA = extractNumericPart(a)
        const numB = extractNumericPart(b)

        // If both have valid numeric parts, sort numerically
        if (numA > 0 && numB > 0) {
          return numA - numB
        }

        // Fallback to string comparison if pattern doesn't match
        return String(a).localeCompare(String(b))
      })
    },
    async onOptionSelecting(selectedOption) {
      const transactionId = this.$route.params.id
      // In training mode, handle API call before selection
      if (this.isTrainingMode && transactionId?.startsWith('multi_')) {
        // Update route query with new batch ID
        await this.$router.replace({
          name: this.$route.name,
          query: {
            ...this.$route.query,
            'link-batch-id': selectedOption,
          },
        })
        this.$store.commit('batch/SET_TRAINING_LINK_BATCH_ID', selectedOption)
        await this.$store.dispatch('batch/fetchBatch', {
          selectedTransaction: transactionId,
          selectFirstDocument: true,
        })
        bus.$emit('getNewTrainingLinkedBatch')
      }
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs.vSelect.$refs.dropdownMenu
        const selectedIndex = this.batchOptions?.indexOf(this.batchId)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.batchOptions.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
