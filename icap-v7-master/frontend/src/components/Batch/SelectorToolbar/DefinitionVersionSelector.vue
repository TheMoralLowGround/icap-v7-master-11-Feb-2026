<template>
  <!-- Vue-select dropdown component -->
  <div>
    <v-select
      v-model="selectedDefinitionVersion"
      :clearable="false"
      :options="definitionVersionOptions"
      :reduce="option => option.value"
    />
  </div>
</template>

<script>
import vSelect from 'vue-select'
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
  },
  computed: {
    // Computed property for the list of definition Versions
    definitionVersions() {
      return this.$store.getters['applicationSettings/definitionVersions']
    },
    // Get default Definition Version
    defaultDefinitionVersion() {
      return this.$store.getters['applicationSettings/defaultDefinitionVersion']
    },
    // Get the list of definition Versions
    definitionVersionOptions() {
      return this.definitionVersions.map(definitionVersion => ({
        label: definitionVersion.toUpperCase(),
        value: definitionVersion,
      }))
    },
    tables() {
      return this.$store.getters['batch/selectedDocument']?.tables || []
    },
    table() {
      return this.$store.getters['dataView/table'] || []
    },

    // Gatter and setter for selected definition
    selectedDefinitionVersion: {
      get() {
        return this.$store.getters['dataView/selectedDefinitionVersion']
      },
      set(value) {
        this.$store.commit('dataView/SET_SELECTED_DEFINITION_VERSION', value)
      },
    },
  },
  watch: {
    // Watches for changes in the selected document ID.
    selectedDefinitionVersion(oldVal, newVal) {
      if (oldVal !== newVal) {
      // Resets the selected table ID to 0.
        this.$store.commit('dataView/IS_CHANGE_DEFINITION_VERSION', true)
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
