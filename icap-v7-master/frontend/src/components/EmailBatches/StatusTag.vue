<template>
  <chip
    v-if="status"
    :variant="chipVariant"
  >
    {{ formattedStatus }}
  </chip>
</template>

<script>
import Chip from '@/components/UI/Chip.vue'

export default {
  components: {
    Chip,
  },
  props: {
    status: {
      type: String,
      required: true,
    },
  },
  computed: {
    chipVariant() {
      if (this.status === 'completed') {
        return 'success'
      }

      if (['waiting', 'warning', 'awaiting_agent'].includes(this.status)) {
        return 'warning'
      }

      if (this.status === 'failed') {
        return 'danger'
      }

      return 'primary'
    },
    formattedStatus() {
      return this.status
        ?.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ') || ''
    },
  },
}
</script>
