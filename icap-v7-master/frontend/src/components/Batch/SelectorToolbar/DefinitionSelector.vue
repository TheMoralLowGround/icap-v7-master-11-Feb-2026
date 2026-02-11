<template>
  <!-- v-select for selecting a definition with a loading spinner -->
  <v-select
    v-model="selectedDefinition"
    :clearable="false"
    :options="options"
    :loading="dataViewLoading"
    class="definition-selector"
  >
    <!-- Custom spinner template -->
    <template #spinner="{ loading }">
      <b-spinner
        v-if="loading"
        variant="primary"
        small
      />
    </template>

    <template #selected-option="option">
      <div style="width: 100%;">
        <p style="white-space: nowrap; margin: 0; overflow: hidden; text-overflow: ellipsis">
          {{ option.label }}
        </p>
      </div>
    </template>

    <template #option="option">
      <div style="width: 90%">
        <p style="margin: 0; overflow: hidden; text-overflow: ellipsis">
          {{ option.label }}
        </p>
      </div>
    </template>
  </v-select>
</template>

<script>
import vSelect from 'vue-select'
import { BSpinner } from 'bootstrap-vue'

export default {
  components: {
    vSelect,
    BSpinner,
  },
  computed: {
    // Computed property for the selected definition
    selectedDefinition: {
      get() {
        return this.$store.getters['dataView/selectedDefinition'].definition_id
      },
      set(value) {
        this.$store.dispatch('dataView/onChangeDefinition', value)
      },
    },
    // Get selected view mode
    view() {
      return this.$store.getters['batch/view']
    },
    // Get all definitions from store
    options() {
      return this.$store.getters['dataView/allDefinitions']
    },
    // Return Loading status from store
    dataViewLoading() {
      return this.$store.getters['dataView/loading']
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';

.definition-selector {
  width: 210px;

  .vs__selected-options {
    overflow: hidden;

    .vs__selected {
      width: 88%;
    }
  }
}
</style>
