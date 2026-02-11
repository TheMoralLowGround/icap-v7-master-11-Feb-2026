<template>
  <span class="text-container">
    <span
      :class="{ 'truncated': !isExpanded && isTextLong }"
    >
      {{ isExpanded || !isTextLong ? text : text.slice(0, maxLength) + '...' }}
    </span>
    <b-button
      v-if="isTextLong"
      variant="link"
      size="sm"
      class="p-0 show-more-btn text-primary"
      :aria-label="`Toggle full text for ${text}`"
      @click="isExpanded = !isExpanded"
    >
      {{ isExpanded ? 'Show Less' : 'Show More' }}
    </b-button>
  </span>
</template>

<script>
import { BButton } from 'bootstrap-vue'

export default {
  components: {
    BButton,
  },
  props: {
    text: {
      type: String,
      default: '',
    },
    maxLength: {
      type: Number,
      default: 100,
    },
  },
  data() {
    return {
      isExpanded: false,
    }
  },
  computed: {
    isTextLong() {
      return this.text && this.text.length > this.maxLength
    },
  },
}
</script>

<style scoped>
.text-container {
  display: inline; /* Keep text and button inline */
}
.truncated {
  display: inline-block;
  max-width: 300px; /* Adjust based on context */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: bottom; /* Align with button */
}
.show-more-btn {
  font-size: 0.8rem;
  text-decoration: none;
  margin-left: 0.25rem; /* Small gap after text or ellipsis */
  vertical-align: baseline; /* Align with text baseline */
}
.show-more-btn:hover {
  text-decoration: underline;
}
</style>
