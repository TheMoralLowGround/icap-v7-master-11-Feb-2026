<!--
 Organization: AIDocbuilder Inc.
 File: ChunkdataWithPlainText.vue
 Version: 7.0

 Authors:
   - Ali - Initial implementation

 Last Updated By: Ali
 Last Updated At: 2025-06-20

 Description:
   This component renders a pre that displays chunked data dynamically based on the `chunkData` from Vuex.

 Main Features:
   - Show plain text from chunk data.

 Dependencies:
   - nothing

 Notes:
   ---
-->

<template>
  <div class="chunk-data-container">
    <b-alert
      variant="danger"
      :show="error !== null ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ error }} <!-- Displays the error message -->
        </p>
      </div>
    </b-alert>
    <!-- <pre>{{ dummyData }}</pre> -->
    <pre class="mb-0">{{ chunkDataWithPlainText }}</pre>
  </div>
</template>

<script>
import {
  BAlert,
} from 'bootstrap-vue'

export default {
  components: {
    BAlert,
  },
  props: {
    error: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
  },
  computed: {
    // Fetches the chunkData from the store
    chunkDataWithPlainText() {
      return this.$store.getters['batch/chunkDataWithPlainText']
    },
  },
}
</script>
