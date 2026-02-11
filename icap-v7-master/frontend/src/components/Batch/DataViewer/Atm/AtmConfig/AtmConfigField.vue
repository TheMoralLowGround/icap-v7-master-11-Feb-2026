<template>
  <!-- Display the row only if advancedSettings is true and label is not "Record Line" -->
  <b-row
    v-if="advancedSettings && label !== 'Record Line'"
    class="my-1 w-75"
  >
    <b-col class="mr-2">
      <!-- Flex container for label, value, and slider -->
      <div class="d-flex w-100 align-items-center">
        <!-- Label and value display -->
        <p class="mb-0 mr-2 no-wrap">
          <span class="mr-1">{{ label + ': ' }}</span> <!-- Display the label -->
          {{ inputValue }} <!-- Display the current value -->
        </p>
        <!-- Range slider for adjusting the value -->
        <RangeSlider
          v-model="inputValue"
          class="w-100"
          :min="min"
        />
      </div>
    </b-col>
  </b-row>
</template>

<script>
import { BCol, BRow } from 'bootstrap-vue' // Import BootstrapVue components
import RangeSlider from '@/components/UI/RangeSlider.vue' // Import the custom RangeSlider component

export default {
  components: {
    BCol,
    BRow,
    RangeSlider, // RangeSlider component
  },
  props: {
    // The current value of the slider, required
    value: {
      type: Number,
      required: true,
    },
    // The label to display beside the slider, required
    label: {
      type: String,
      required: true,
    },
    // Minimum value for the slider, optional with a default of 0
    min: {
      type: Number,
      required: false,
      default: 0,
    },
    // Boolean indicating if advanced settings are enabled
    advancedSettings: {
      type: Boolean,
    },
  },
  data() {
    return {
      // Internal state for the slider value
      inputValue: 0,
    }
  },
  watch: {
    /**
     * Watcher for inputValue to emit updates to the parent component.
     * Converts the value to an integer before emitting.
     */
    inputValue(newVal) {
      this.$emit('input', parseInt(newVal, 10)) // Emit the updated value to the parent
    },
  },
  created() {
    // Initialize inputValue with the value prop
    this.inputValue = this.value
  },
}
</script>

<style lang="scss" scoped>
.form-input {
  width: 80px; /* Set a fixed width for input elements */
}

.no-wrap {
  white-space: nowrap /* Prevent text wrapping */
}

input[type='number']::-webkit-inner-spin-button,
input[type='number']::-webkit-outer-spin-button {
  -webkit-appearance: button; /* Style the spin buttons for number inputs */
}
</style>
