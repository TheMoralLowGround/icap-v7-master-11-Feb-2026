<template>
  <div>
    <h2>Other Settings</h2>
    <delete-not-in-use-batches />
  </div>
</template>

<script>
import DeleteNotInUseBatches from '@/components/Admin/OtherSettings/DeleteNotInUseBatches.vue'

export default {
  components: {
    DeleteNotInUseBatches,
  },
}
</script>
