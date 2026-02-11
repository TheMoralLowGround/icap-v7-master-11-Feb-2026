<!--
 Organization: AIDocbuilder Inc.
 File: CompoundKeys.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   This component manages a list of compound keys and allows users to interact with individual key items.
   Each key item is rendered using the `KeyItem` component, and various events such as adding, deleting,
   or interacting with key anchors are emitted. The component supports dynamic behavior,
   including auto-expanding input sections and normalizing key values.

 Main Features:
   - Displays a list of compound key items and renders them dynamically using the `KeyItem` component.
   - Supports deleting individual key items and triggers necessary actions to clear highlights if the deleted key is highlighted.
   - Automatically updates the internal state based on changes in the `value` prop and emits updates back to the parent component.
   - Supports auto-expanding input section fields for better user interaction.
   - Fetches key item label options based on the current compound key setting and syncs it with the Vuex store.
   - Handles watching changes in the key items and updates the `value` prop in real-time.

 Dependencies:
   - Vuex (for fetching `optionsKeyItems`, `compoundKeys`, and other batch-related data)
   - Lodash (for deep comparisons using `isEqual` and cloning using `cloneDeep`)
   - KeyItem (dynamic import for rendering key items)
   - `normalizeKeyItemValues` (helper function for normalizing key item values)

 Notes:
   - The `setInternalState` method normalizes the key item values using the helper function `normalizeKeyItemValues`.
   - The component emits events such as `dropdownOpen` and `highlightAnchors` to handle interactions with external components and provide dynamic behavior.
   - The component ensures that any changes made to the key items are synchronized with the parent component using the `input` event.
-->

<template>
  <div class="mx-1">
    <key-item
      v-for="(keyItem, keyItemIndex) in keys"
      :key="keyItem.id"
      v-model="keys[keyItemIndex]"
      :parent="compoundKeySettingName"
      :auto-expand-input-section-fields="autoExpandInputSectionFields"
      :key-lable-options="keyLableOptions"
      @deleteItem="deleteKey(keyItem.id)"
      @dropdownOpen="$emit('dropdownOpen', keyItem.id)"
      @highlightAnchors="$emit('highlightAnchors', { keyItemId: keyItem.id, data: $event})"
    />
  </div>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import { normalizeKeyItemValues } from './key-helper'

export default {
  components: {
    // Dynamically import the KeyItem component for use within this component
    KeyItem: () => import('@/components/Batch/DataViewer/KeyItems/KeyItem.vue'),
  },
  props: {
    // 'value' is an array prop that is required for the component's functionality
    value: {
      type: Array,
      required: true,
    },
    // 'autoExpandInputSectionFields' is a boolean prop that is required for auto-expanding the input section
    autoExpandInputSectionFields: {
      type: Boolean,
      required: true,
    },
    // 'compoundKeySettingName' is an optional string prop with a default empty string if not provided
    compoundKeySettingName: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
  },
  data() {
    return {
      // 'keys' will store the list of keys for the current component
      keys: [],
    }
  },
  computed: {
    // 'out' is a computed property that clones 'keys' to avoid direct mutation
    out() {
      return cloneDeep(this.keys)
    },
    // 'isExcelBatch' checks if the current batch is an Excel batch using Vuex getter
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    // 'keyLableOptions' returns a list of key items for the compound key setting based on the current compound key setting name
    keyLableOptions() {
      const compoundKeySettings = this.$store.getters['definitionSettings/compoundKeys']
      const compoundKeySetting = compoundKeySettings.find(item => item.name === this.compoundKeySettingName)
      const keyItems = compoundKeySetting ? compoundKeySetting.keyItems : []
      return keyItems
    },
    // 'optionsKeyItems' returns options for key items from the store
    optionsKeyItems() {
      return this.$store.getters['definitionSettings/options']['options-keys'].items
    },
  },
  watch: {
    // Watch for changes in 'out' and emit the new value if it differs from the input value
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val) // Emit the 'input' event to sync the value with the parent
        }
      },
      deep: true,
    },
    // Watch for changes in 'value' prop and update internal state if needed
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState() // Call 'setInternalState' to normalize the value
        }
      },
      deep: true,
    },
  },
  created() {
    // Initialize the component state when it is created
    this.setInternalState()
  },
  methods: {
    // 'setInternalState' method normalizes the 'value' prop and updates the internal 'keys' state
    setInternalState() {
      this.keys = normalizeKeyItemValues(this.value, this.optionsKeyItems)
    },
    deleteKey(keyItemId) {
      // Check if the key being deleted is the highlighted key and clear highlights if necessary
      if (keyItemId === this.$store.getters['batch/highlightKeyAnchorsData'].keyItemId) {
        this.$store.dispatch('batch/clearAnchorHighlights')
      }

      // Find the index of the keyItem based on the keyItemId
      const index = this.keys.findIndex(keyItem => keyItem.id === keyItemId)

      // Only proceed if the keyItem was found
      if (index !== -1) {
        this.keys.splice(index, 1) // Remove the key from the array
      }
    },
  },
}
</script>
