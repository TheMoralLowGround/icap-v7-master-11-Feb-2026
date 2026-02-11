<template>
  <div>
    <!-- <h2 class="mb-2">
      Assembly Settings
    </h2> -->
    <b-card class="p-2">
      <UploadedKeys />
    </b-card>
  </div>
</template>

<script>
import {
  BCard,
} from 'bootstrap-vue'
import UploadedKeys from './UploadedKeys.vue'

export default {
  components: {
    BCard,
    UploadedKeys,
  },

}
</script>
