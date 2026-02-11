<template>
  <!-- Vue-select dropdown component -->
  <v-select
    v-model="resultIndex"
    :options="queryResultOptions"
    label="label"
    :reduce="option => option.value"
    :clearable="false"
  />
</template>

<script>
// Importing the vue-select component
import vSelect from 'vue-select'

export default {
  components: {
    vSelect,
  },
  data() {
    return {
      search: null, // Placeholder property; not currently used in this implementation
    }
  },
  computed: {
    // Computed property for the selected result index
    resultIndex: {
      // Getter retrieves the current index from the Vuex store
      get() {
        return this.$store.getters['lookup/resultIndex']
      },
      // Setter updates the index in the Vuex store
      set(value) {
        this.$store.commit('lookup/SET_RESULT_INDEX', value)
      },
    },
    results() {
      return this.$store.getters['lookup/results']
    },
    // Computed property for the list of results from options
    queryResultOptions() {
      const options = []
      for (let index = 0; index < this.results.length; index += 1) {
        options.push({
          label: `Query Result #${index + 1}`,
          value: index,
        })
      }
      return options
    },
  },
  watch: {
    // watcher for the list of results from options
    queryResultOptions: {
      deep: true,
      handler() {
        if (this.resultIndex > this.queryResultOptions.length - 1) {
          this.resultIndex = null
        }

        if (this.resultIndex === null && this.queryResultOptions.length > 0) {
          this.resultIndex = 0
        }
      },
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
