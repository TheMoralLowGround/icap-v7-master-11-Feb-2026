<template>
  <div>
    <!-- Alert Section -->
    <b-alert
      variant="primary"
      show
    >
      <div class="alert-body">
        <p>
          <!-- Icon for expanding the list -->
          <feather-icon
            v-if="!expanded"
            icon="ChevronRightIcon"
            class="cursor-pointer"
            size="20"
            @click="expanded = true"
          />

          <!-- Icon for collapsing the list -->
          <feather-icon
            v-if="expanded"
            icon="ChevronDownIcon"
            class="cursor-pointer"
            size="20"
            @click="expanded = false"
          />

          <!-- Alert message showing the number of definitions and action mode -->
          {{ definitions.length }} Definition(s) will be {{ mode === 'new' ? 'created' : 'updated' }}
        </p>
      </div>
    </b-alert>

    <!-- Definitions List -->
    <ul
      v-if="expanded"
      class="item-list"
    >
      <!-- Dynamically render each definition -->
      <li
        v-for="(definition, definitionIndex) of definitions"
        :key="definitionIndex"
      >
        {{ definition.definition_id }} - {{ definition.type }}
      </li>
    </ul>
  </div>
</template>

<script>
import {
  BAlert,
} from 'bootstrap-vue'

export default {
  // Register the BAlert component
  components: {
    BAlert,
  },
  props: {
    // Array of definitions passed to the component
    definitions: {
      type: Array,
      required: true,
    },
    // Mode of operation: 'new' or 'updated'
    mode: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      // Tracks whether the list of definitions is expanded or collapsed
      expanded: false,
    }
  },
}
</script>

<style scoped>
/* Style for the definitions list to handle overflow and set maximum height */
.item-list {
  max-height: 150px;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
