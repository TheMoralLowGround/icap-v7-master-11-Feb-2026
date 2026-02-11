<template>
  <!-- v-select for selecting a definition type with a loading spinner -->
  <v-select
    v-model="selectedDefinitionType"
    :clearable="false"
    :options="options"
    :loading="dataViewLoading"
    class="definition-type-selector"
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
      <div style="width: 90%;">
        <p style="white-space: nowrap; margin: 0; overflow: hidden; text-overflow: ellipsis">
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
    // Computed property for the selected definition type
    selectedDefinitionType: {
      get() {
        const selectedDefinition = this.$store.getters['dataView/selectedDefinition']

        if (selectedDefinition.type_seq_no) {
          return `${selectedDefinition.type} ${selectedDefinition.type_seq_no}`
        }

        return selectedDefinition.type
      },
      set(value) {
        this.$store.dispatch('dataView/onChangeDefinitionType', value)
      },
    },
    // Get all definitions from store
    options() {
      return this.$store.getters['dataView/typesByDefinition']
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

.definition-type-selector {
  width: 205px;

  .vs__selected-options {
    overflow: hidden;

    .vs__selected {
      width: 87%;
    }
  }
}
</style>
