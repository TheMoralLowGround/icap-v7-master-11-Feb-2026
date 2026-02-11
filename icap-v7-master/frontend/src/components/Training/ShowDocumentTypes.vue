<template>
  <div class="document-types-container">
    <span
      v-for="(docType, index) in displayedDocTypes"
      :key="index"
      :class="['border-primary','document-type-tag', 'mr-2', 'mb-1']"
    >
      {{ docType.name }}
      <b-badge
        v-if="docType.count > 1"
        pill
        variant="primary"
        class="ml-1 count-badge"
      >
        {{ docType.count }}
      </b-badge>
    </span>

    <!-- Show more/less button -->
    <b-badge
      v-if="uniqueDocTypes.length > maxVisible"
      pill
      variant="primary"
      class="cursor-pointer mr-1 mb-1"
      @click="toggleExpanded"
    >
      {{ isExpanded ? 'Show Less' : `+${hiddenCount} More` }}
    </b-badge>
  </div>
</template>

<script>
import { BBadge } from 'bootstrap-vue'

export default {
  name: 'DocumentTypes',
  components: {
    BBadge,
  },
  props: {
    documentTypes: {
      type: Array,
      required: true,
      default() {
        return []
      },
    },
    maxVisible: {
      type: Number,
      default: 3,
    },
  },
  data() {
    return {
      isExpanded: false,
    }
  },
  computed: {
    uniqueDocTypes() {
      if (!this.documentTypes || !Array.isArray(this.documentTypes)) {
        return []
      }

      // Count occurrences of each document type
      const typeCount = {}
      this.documentTypes.forEach(type => {
        const cleanType = String(type).trim()
        if (cleanType) {
          typeCount[cleanType] = (typeCount[cleanType] || 0) + 1
        }
      })

      // Convert to array with count information and sort alphabetically
      return Object.entries(typeCount)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => a.name.localeCompare(b.name))
    },

    displayedDocTypes() {
      if (this.isExpanded || this.uniqueDocTypes.length <= this.maxVisible) {
        return this.uniqueDocTypes
      }
      return this.uniqueDocTypes.slice(0, this.maxVisible)
    },

    hiddenCount() {
      return Math.max(0, this.uniqueDocTypes.length - this.maxVisible)
    },
  },
  methods: {
    toggleExpanded() {
      this.isExpanded = !this.isExpanded
    },
  },
}
</script>

<style scoped>
.document-types-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.document-type-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  /* background-color: #f8f9fa; */
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
}
.count-badge {
  font-size: 0.65rem;
  min-width: 20px;
  height: 20px;
}
</style>
