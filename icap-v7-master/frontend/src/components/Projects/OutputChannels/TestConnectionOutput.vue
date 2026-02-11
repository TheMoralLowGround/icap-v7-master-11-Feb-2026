<template>
  <div>
    <BCard
      class="bg-black text-light mb-4 mt-3 position-relative"
    >
      <div class="json-container">
        <pre class="mb-0"><code>{{ formattedRequestJson }}</code></pre>
      </div>
    </BCard>
  </div>
</template>
<script>
import {
  BCard,
  // BBadge,
} from 'bootstrap-vue'

export default {
  name: 'TestConnectionOutput',
  components: {
    BCard,
  },
  props: {
    testResult: {
      type: Object,
      default: () => ({}),
    },
  },

  computed: {
    formattedRequestJson() {
      return JSON.stringify(this.testResult, null, 2)
    },
  },
}
</script>
<style scoped>
/* JSON display styling - ensures readability in dark mode */
.json-container pre {
  background: transparent;
  border: none;
  padding: 1rem;
  overflow-x: auto;
  white-space: pre-wrap;
  font-size: 0.875rem;
  line-height: 1.5;
}

.json-container code {
  color: #f8f9fa; /* Light color for dark backgrounds */
  background: transparent;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
</style>
