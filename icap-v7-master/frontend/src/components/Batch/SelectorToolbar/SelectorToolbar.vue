<template>
  <div class="">
    <!-- Main container for the toolbar or header area -->
    <div class="d-flex align-items-center wrapper mb-1">
      <!-- Display the definition selector if the current route is not 'template-batch' -->
      <div
        v-if="currentRouteName !== 'template-batch'"
        class="definition-selector-wrapper"
      >
        <definition-selector />
      </div>

      <!-- Display the definition type selector if the current route is not 'template-batch' -->
      <div
        v-if="currentRouteName !== 'template-batch'"
        class="definition-type-selector-wrapper"
      >
        <definition-type-selector />
      </div>

      <!-- Always display the batch selector -->
      <div class="batch-selector-wrapper">
        <batch-selector />
      </div>

      <!-- Always display the document selector -->
      <div class="document-selector-wrapper">
        <document-selector />
      </div>

      <!-- Always display the definition version selector -->
      <div class="definition-version-selector-wrapper">
        <definition-version-selector />
      </div>

      <!-- Show query results-related components only if the imageViewerAreaContent is 'query-results' -->
      <template v-if="imageViewerAreaContent === 'query-results'">
        <!-- Query result selector -->
        <div class="query-result-selector">
          <query-result-selector />
        </div>
        <!-- Query result search bar -->
        <div class="query-result-search">
          <query-result-search />
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import DefinitionSelector from './DefinitionSelector.vue'
import DefinitionTypeSelector from './DefinitionTypeSelector.vue'
import BatchSelector from './BatchSelector.vue'
import DocumentSelector from './DocumentSelector.vue'
import DefinitionVersionSelector from './DefinitionVersionSelector.vue'

import QueryResultSelector from './Lookup/QueryResultSelector.vue'
import QueryResultSearch from './Lookup/QueryResultSearch.vue'

export default {
  components: {
    DefinitionSelector,
    DefinitionTypeSelector,
    BatchSelector,
    DocumentSelector,
    DefinitionVersionSelector,
    QueryResultSelector,
    QueryResultSearch,
  },
  props: {
    imageViewerAreaContent: {
      type: String,
      required: true,
    },
  },
  computed: {
    // Current route name
    currentRouteName() {
      return this.$route.name
    },
  },
}
</script>

<style scoped>
.wrapper {
    column-gap: 1rem;
}
.mode-selector-wrapper {
    flex-basis: 150px;
}
.definition-selector-wrapper {
  flex-basis: 210px;
}
.definition-type-selector-wrapper, .batch-selector-wrapper {
  flex-basis: 205px;
}
.document-selector-wrapper {
  flex-basis: 270px;
}
.definition-version-selector-wrapper {
  flex-basis: 130px;
}
.query-result-selector {
    flex-basis: 200px;
}
.query-result-search {
   flex-basis: 200px;
}
</style>
