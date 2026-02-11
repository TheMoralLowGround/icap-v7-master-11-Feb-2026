<!--
 Organization: AIDocbuilder Inc.
 File: StatusTag.vue
 Version: 1.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-11-10

 Description:
   The `StatusTag.vue` component displays a status label using a chip component.
   Based on the value of the `status` prop, it dynamically sets the chip's variant
   to reflect the appropriate status indicator (e.g., success, warning, danger, or primary).
   This component is typically used to show the status of a process, batch, or task.

 Features:
   - Displays a status tag with the status name using a custom chip component.
   - Dynamically assigns a chip variant (e.g., success, warning, danger) based on the `status` value.
   - Supports various status types including "completed", "waiting", "failed", and others.

 Dependencies:
   - `Chip`: A custom UI component for displaying status tags as chips.

 Notes:
   - The `chip` component is a reusable UI element that can be used to visually display status labels.
   - The status text is displayed inside the chip component, with the chip's color reflecting the current state.
-->

<template>
  <chip
    v-if="status"
    :variant="chipVariant"
    :status="status"
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

      if (['waiting', 'classification review', 'incomplete', 'warning', 'awaiting_agent'].includes(this.status)) {
        return 'warning'
      }

      if (['failed', 'classification error'].includes(this.status)) {
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
