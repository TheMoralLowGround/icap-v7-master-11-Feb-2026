<template>
  <div class="d-flex align-items-center wrapper">
    <!-- Iterate through the options array to render icons dynamically -->
    <div
      v-for="(option, index) in options"
      :key="index"
    >
      <feather-icon
        v-if="option.value !== 'chunk-data' || mainMode !== 'verification'"
        v-b-tooltip.hover
        :icon="option.icon"
        size="20"
        class="cursor-pointer"
        :class="{'text-primary': view === option.value}"
        :title="option.label"
        @click="view = option.value"
      />
    </div>
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  props: {
    imageViewerAreaContent: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      options: [
        {
          label: 'Key View',
          value: 'key',
          icon: 'KeyIcon',
        },
        {
          label: 'Table View',
          value: 'table',
          icon: 'TabletIcon',
        },
        {
          label: 'Chunk Data View',
          value: 'chunk-data',
          icon: 'PieChartIcon',
        },
      ],
    }
  },
  computed: {
    mainMode() {
      return this.$store.getters['dataView/mainMode'] // Retrieve main mode from Vuex store
    },
    view: {
      // Getter for view
      get() {
        return this.$store.getters['batch/view']
      },
      // Commit updated view to Vuex store
      set(value) {
        this.$store.commit('batch/SET_VIEW', value)
      },
    },
    // enableMeasure() {
    //   return this.$store.getters['batch/enableMeasure']
    // },

    // Check if lookup is initialized
    lookupInitialized() {
      return this.$store.getters['lookup/initialized']
    },
    // Check if lookups are enabled
    enableLookups() {
      return this.$store.getters['applicationSettings/enableLookups']
    },
  },
  watch: {
    // Watch for changes in 'view' and dispatch Vuex actions accordingly
    view(value) {
      // if (oldValue === 'analyzer') {
      //   if (this.enableMeasure) {
      //     this.$store.commit('batch/SET_ENABLE_MEASURE', false)
      //   }
      // }
      if (value === 'table' || value === 'key') {
        this.$store.dispatch('definitionSettings/setKeyOptionsForRules')
      }
    },
    // Dynamically add or remove 'chunk-data' option based on imageViewerAreaContent value
    imageViewerAreaContent(value) {
      if (value !== 'query-results') {
        this.options.push({
          label: 'Chunk Data View',
          value: 'chunk-data',
          icon: 'PieChartIcon',
        })
      } else {
        this.options = this.options.filter(option => option.value !== 'chunk-data')
      }
    },
  },
  created() {
    // Add 'Explore Lookup' option if lookups are enabled
    // if (this.enableLookups && this.mainMode !== 'verification') {
    //   this.options.push({
    //     label: 'Explore Lookup',
    //     value: 'explore-lookup',
    //     icon: 'DatabaseIcon',
    //   })
    // }
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
.wrapper {
  column-gap: .62rem !important;
}
</style>
