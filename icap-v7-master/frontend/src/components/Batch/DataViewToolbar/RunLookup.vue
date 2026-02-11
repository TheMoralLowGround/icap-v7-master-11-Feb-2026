<!--
 Organization: AIDocbuilder Inc.
 File: RunLookup.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component provides a button to trigger the "Run Lookup" action within the application. The button is
   disabled while a lookup process is executing or if the form is not ready for submission. A spinner is displayed
   next to the button when the lookup is being processed. This component communicates with Vuex and utilizes
   an event bus to trigger the lookup action.

 Main Features:
   - Displays a button for initiating the lookup process.
   - Button is disabled when a lookup is running or when submission is not enabled.
   - Shows a spinner next to the button while the lookup is being executed.
   - Uses Vuex to track the executing state and button enablement status.
   - Emits the `runLookup` event via the event bus when the button is clicked.

 Dependencies:
   - Bootstrap Vue: For button and spinner components
   - Vuex: For managing state related to executing the lookup and enabling the button
   - Event Bus: For emitting the lookup action trigger

 Notes:
   - The component listens for state changes in Vuex to determine if the lookup is executing or if the button should be enabled.
   - The `runLookup` method triggers the lookup process by emitting an event through the event bus.
-->

<template>
  <!-- Button to trigger the "Run Lookup" action -->
  <b-button
    variant="outline-primary"
    :disabled="executingLookup || !enableSubmit"
    @click="runLookup"
  >
    Run Lookup
    <!-- Spinner displayed while the lookup process is executing -->
    <b-spinner
      v-if="executingLookup"
      small
      label="Small Spinner"
    />
  </b-button>
</template>

<script>
import bus from '@/bus'
import { BButton, BSpinner } from 'bootstrap-vue'

export default {
  components: {
    BButton,
    BSpinner,
  },
  computed: {
    // Getter to determine if the lookup process is currently executing
    executingLookup() {
      return this.$store.getters['lookup/executing']
    },
    // Getter to determine if the "Run Lookup" button should be enabled
    enableSubmit() {
      return this.$store.getters['lookup/enableSubmit']
    },
  },
  methods: {
    // Method to trigger the lookup process via the event bus
    runLookup() {
      bus.$emit('dataView/runLookup')
    },
  },
}
</script>
