<!--
 Organization: AIDocbuilder Inc.
 File: DefinedKey.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component is used for rendering a table row with editable key data, including a label,
   positional data, and percentages for the defined key.
   It provides functionality for user interaction with a form input and calculates positional data when a selection is made.

 Features:
   - Displays editable label for the defined key using `form-input`.
   - Renders key data including `pageIndex`, `pos`, `xPercentage`, `yPercentage`, `language`, and `style`.
   - Provides a delete icon to trigger the `deleteItem` event.
   - Deeply watches and synchronizes internal state with the parent component via `v-model`.
   - Calculates and updates positional and percentage data when `selection-input` event is triggered.

 Dependencies:
   - BootstrapVue (for UI components like table row (`b-tr`), table data (`b-td`), and tooltips)
   - Lodash (for deep cloning and comparison utilities)
   - Vuex (for fetching language data from the store)
   - Custom `FormInput` component (for user input)

 Notes:
   - Ensures that changes in key data are emitted to the parent component when updated.
   - Handles the position and percentage calculation relative to the page dimensions.
   - The component is part of a batch processing workflow where keys are defined and associated with their positional data.
-->

<template>
  <b-tr>
    <!-- Render a form input field bound to 'definedKey.label' using v-model -->
    <b-td>
      <form-input
        v-model="definedKey.label"
        type="text"
        @selection-input="onSelectionInput"
      />
    </b-td>
    <!-- Render various properties from 'definedKey.data' in table columns -->
    <b-td>{{ definedKey.data.pageIndex }}</b-td>
    <b-td>{{ definedKey.data.pos }}</b-td>
    <b-td>{{ definedKey.data.xPercentage }}</b-td>
    <b-td>{{ definedKey.data.yPercentage }}</b-td>
    <b-td>{{ definedKey.data.language }}</b-td>
    <b-td>{{ definedKey.data.style }}</b-td>
    <!-- Render a delete icon with a tooltip and trigger the 'deleteItem' event on click -->
    <b-td>
      <div>
        <feather-icon
          v-b-tooltip.hover
          title="Delete Key"
          icon="Trash2Icon"
          class="cursor-pointer mx-auto"
          size="20"
          @click.stop="$emit('deleteItem')"
        />
      </div>
    </b-td>
  </b-tr>
</template>

<script>

import { VBTooltip, BTr, BTd } from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash' // Import Lodash utilities for deep comparison and cloning
import FormInput from '@/components/UI/FormInput.vue' // Import custom FormInput component

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    FormInput,
    BTr,
    BTd,
  },
  props: {
    // Define 'value' as an Object prop that is required
    value: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      // 'definedKey' stores the internal state of the key, initialized to null
      definedKey: null,
    }
  },
  computed: {
    // 'out' is a computed property that deep clones 'definedKey'
    out() {
      return cloneDeep(this.definedKey)
    },
  },
  watch: {
    // Watch for changes in the 'out' property and emit the updated value if it differs from the original 'value'
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val) // Emit the 'input' event to update the parent component
        }
      },
      deep: true, // Deep watch to track nested changes in 'definedKey'
    },
    // Watch for changes in the 'value' prop and update 'definedKey' if it differs
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState() // Sync 'definedKey' with the 'value' prop if they are different
        }
      },
      deep: true, // Deep watch to track nested changes in 'value'
    },
  },
  created() {
    // Initialize 'definedKey' when the component is created
    this.setInternalState()
  },
  methods: {
    // Sync 'definedKey' with the 'value' prop when initializing or resetting
    setInternalState() {
      this.definedKey = cloneDeep(this.value) // Deep clone the 'value' prop into 'definedKey'
    },
    // Event handler for 'selection-input' event that calculates position and percentages for chunk data
    onSelectionInput(data) {
      // Calculate the x distance and x percentage relative to page width
      const xDistance = parseFloat(data.startPos) + ((parseFloat(data.endPos) - parseFloat(data.startPos)) / 2)
      const xPercentage = (xDistance / data.pageWidth) * 100

      // Calculate the y distance and y percentage relative to page height
      const yDistance = parseFloat(data.topPos) + ((parseFloat(data.bottomPos) - parseFloat(data.topPos)) / 2)
      const yPercentage = (yDistance / data.pageHeight) * 100

      // Update the 'definedKey.data' with new position and percentages, including pageIndex and language
      this.definedKey.data = {
        pos: `${data.startPos},${data.topPos},${data.endPos},${data.bottomPos}`,
        xPercentage,
        yPercentage,
        pageIndex: data.pageIndex,
        style: data.style,
        language: this.$store.getters['batch/selectedDocument'].language, // Fetch the language from Vuex store
      }
    },
  },
}
</script>
