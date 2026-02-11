<!--
 Organization: AIDocbuilder Inc.
 File: KeyItems.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component manages a list of key items and allows users to interact with individual key items in a draggable list.
   It supports adding, deleting, and validating key items, as well as anchor highlighting and scrolling to specific items.

 Main Features:
   - Draggable list of key items with `vuedraggable`.
   - Tooltip support using `v-b-tooltip` from Bootstrap-Vue.
   - Validation for key items using `vee-validate`.
   - Dynamic addition of key items with a configurable count.
   - Support for scrolling to specific key items or compound key items.
   - Emits events for key deletion, anchor highlighting, and dropdown opening.

 Dependencies:
   - `vuedraggable` - For drag-and-drop functionality.
   - `vee-validate` - For form validation.
   - `bootstrap-vue` - For tooltips and UI components.
   - `lodash` - For utility functions like deep cloning and comparison.

 Notes:
   - Ensure that `keyItem` values passed to `KeyItem.vue` are properly normalized and validated.
   - The component listens to global events through the event bus to add keys and validate items.
-->

<template>
  <div class="h-100">
    <div class="key-items-container d-flex flex-column h-100">
      <div>
        <div class="heading-row d-flex">
          <div class="regular-column-key-fiels flex-grow-1">
            <span
              v-b-tooltip.hover
              class="text-capitalize"
              title="Refer to the Yellow Book iCap Reference Files to check mapping to CW1 Fields"
            >
              Key Field Name
            </span>
          </div>
          <div class="regular-column flex-grow-1">
            <span
              v-b-tooltip.hover
              class="text-capitalize"
              title="Becomes available only for FieldNames with multiple Options. Choose, when Activated"
            >
              Qualifier
            </span>
          </div>
          <div class="regular-column flex-grow-1">
            <span
              v-b-tooltip.hover
              class="text-capitalize"
              title=""
            >
              Type
            </span>
          </div>
          <div class="regular-column flex-grow-1">
            <span
              v-b-tooltip.hover
              class="text-capitalize"
              title="Mark Label against which value of the Key Point Pair can be found"
            >
              Label
            </span>
          </div>
          <div class="regular-column flex-grow-1">
            <span
              v-b-tooltip.hover
              class="text-capitalize"
              title="Mark Label Value against which value of the Key Point Pair can be found"
            >
              Value
            </span>
          </div>
          <div class="action-column" />
        </div>
      </div>
      <div
        ref="keyItemsWrapper"
        class="flex-grow-1 key-items-wrapper"
      >
        <validation-observer
          ref="keyItemsForm"
          mode="eager"
        >
          <!-- <pre>{{ keys.length }}</pre> -->
          <draggable
            v-model="keys"
            tag="div"
            handle=".handle"
            v-bind="dragOptions"
          >
            <!-- <pre>{{ keyItemsDefinition.length }}</pre> -->
            <!-- <pre>{{ keys }}</pre> -->
            <key-item
              v-for="(keyItem, keyItemIndex) of keys"
              :key="keyItem.id"
              v-model="keys[keyItemIndex]"
              class="key-item-main"
              :auto-expand-input-section-fields="autoExpandInputSectionFields"
              @deleteItem="deleteKey(keyItemIndex, keyItem.id)"
              @highlightAnchors="onHightlightAnchors(keyItem.id, $event)"
              @highlightAnchorsCompoundItem="onHightlightAnchors($event.keyItemId, $event.data)"
              @dropdownOpen="scrollToIndex(keyItemIndex)"
              @dropdownOpenCompoundItem="scrollToCompoundItem"
            />
          </draggable>
        </validation-observer>
      </div>
    </div>
  </div>
</template>

<script>
import {
  VBTooltip, // Bootstrap-Vue directive for tooltips
} from 'bootstrap-vue'
import draggable from 'vuedraggable' // Draggable component for drag-and-drop functionality
import { ValidationObserver } from 'vee-validate' // Validation observer for form validation

import { isEqual, cloneDeep } from 'lodash' // Utility functions for deep comparison and cloning
import bus from '@/bus' // Event bus for cross-component communication
import KeyItem from './KeyItem.vue' // Child component for individual key items

import { getDefaultKeys, normalizeKeyItemValues } from './key-helper' // Utility functions for keys

export default {
  directives: {
    'b-tooltip': VBTooltip, // Register tooltip directive
  },
  components: {
    KeyItem, // Component for rendering individual key items
    draggable, // Component for drag-and-drop functionality
    ValidationObserver, // Observer for form validation
  },
  props: {
    // Array of key items passed from the parent component
    value: {
      type: Array,
      required: true,
    },
    // Source identifier, typically used for context or logging
    source: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      keys: [], // Internal state representing the key items
      autoExpandInputSectionFields: false, // Boolean to toggle input field expansion
      isUpdating: false, // Flag to prevent circular update loops
    }
  },
  computed: {
    keyItemsDefinition() {
      return this.$store.getters['dataView/keyItems']
    },
    // Returns a deep clone of the `keys` array, useful for avoiding mutations
    out() {
      return cloneDeep(this.keys)
    },
    // Dragging options for `vuedraggable`, like animations and styling
    dragOptions() {
      return {
        animation: 0, // No animation during dragging
        ghostClass: 'draggable-ghost', // Class applied to the element being dragged
      }
    },
    // Determines if the current batch is an Excel batch from Vuex store
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    // Fetches key options from the Vuex store
    optionsKeyItems() {
      return this.$store.getters['definitionSettings/options']['options-keys'].items
    },

  },
  watch: {
    // Watches `out` computed property and emits an input event if it changes
    out: {
      handler(val) {
        if (this.isUpdating) return // Prevent circular updates

        if (!isEqual(val, this.value)) { // Checks for deep equality
          this.isUpdating = true
          this.$emit('input', val) // Emits the updated value
          this.$nextTick(() => {
            this.isUpdating = false
          })
        }
      },
      deep: true, // Deep watch to track nested changes
    },
    // Watches the `value` prop and updates internal state if it changes
    value: {
      handler(val) {
        if (this.isUpdating) return // Prevent circular updates

        if (!isEqual(val, this.out)) {
          this.isUpdating = true
          this.setInternalState() // Synchronizes internal state with `value`
          this.$nextTick(() => {
            this.isUpdating = false
          })
        }
      },
      deep: true, // Deep watch for nested changes
    },
  },
  created() {
    this.setInternalState() // Initialize internal state with `value`

    // Listen for events to add keys or validate key items
    bus.$on('dataView/addKeys', this.addKeys)
    bus.$on('validateKeyItems', this.validateKeyItems)

    // Expand input section fields after the component is mounted
    this.$nextTick(() => {
      this.autoExpandInputSectionFields = true
    })
  },
  destroyed() {
    // Remove event listeners when the component is destroyed
    bus.$off('dataView/addKeys', this.addKeys)
    bus.$off('validateKeyItems', this.validateKeyItems)
  },
  methods: {
    // Synchronizes internal state (`keys`) with the `value` prop
    setInternalState() {
      this.keys = normalizeKeyItemValues(this.value, this.optionsKeyItems)
    },
    // Adds new key items to the list
    addKeys(payload) {
      // Handle both old format (just count) and new format ({ count, mode })
      const count = typeof payload === 'object' ? payload.count : payload
      const mode = typeof payload === 'object' ? payload.mode : null

      // Only add keys if this component matches the mode
      if (mode) {
        // Map modes to their corresponding sources
        const modeSourceMap = {
          'table-keys': 'tableKeyItems',
          'table-column-prompts': 'tableColumnPrompts',
          'key-items': 'keyItems',
        }

        const expectedSource = modeSourceMap[mode]
        // If mode has a mapping and this component's source doesn't match, skip
        if (expectedSource && this.source !== expectedSource) {
          return
        }
      }

      const lastRowIndex = this.keys.length - 1 // Get the index of the last key item
      // Use 'prompt' as default type for table settings view, otherwise use default behavior
      const defaultType = this.source === 'tableColumnPrompts' ? 'prompt' : null
      this.keys = this.keys.concat(getDefaultKeys(count, this.isExcelBatch, defaultType)) // Append default keys

      // Scroll to the first newly added key item
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },
    // Scrolls to the key item at the specified index
    scrollToIndex(index) {
      const { keyItemsWrapper } = this.$refs // Reference to the wrapper element
      const keyModelItem = keyItemsWrapper.querySelectorAll('.key-item-main')[index]
      keyItemsWrapper.scrollTop = keyModelItem.offsetTop - 8 // Scroll to the item's position
    },
    // Scrolls to a specific compound key item by its ID
    scrollToCompoundItem(id) {
      const { keyItemsWrapper } = this.$refs
      const keyModelItem = keyItemsWrapper.querySelector(`#key-item-${id}`)
      keyItemsWrapper.scrollTop = keyModelItem.offsetTop - 8
    },
    // Deletes a key item at the specified index
    deleteKey(index, keyItemId) {
      // Clear anchor highlights if the deleted key is currently highlighted
      if (keyItemId === this.$store.getters['batch/highlightKeyAnchorsData'].keyItemId) {
        this.$store.dispatch('batch/clearAnchorHighlights')
      }
      this.keys.splice(index, 1) // Remove the key item from the array
    },
    // Handles anchor highlighting for a specific key item
    onHightlightAnchors(keyItemId, selectedAnchor) {
      this.$store.commit('batch/SET_HIGHLIGHT_KEY_ANCHORS_DATA', { keyItemId, selectedAnchor, source: this.source })
    },
    // Validates all key items and executes a callback with the result
    validateKeyItems(callback) {
      this.$refs.keyItemsForm.validate().then(success => {
        callback(success) // Call the callback with the validation result
      })
    },
  },
}
</script>

<style scoped>
.key-items-container {
  overflow: hidden;
}

.heading-row {
  padding: 0.4rem;
  background-color: #f3f2f7;
  border-bottom: 2px solid #ebe9f1;
  column-gap: 10px;
}

.heading-row span {
  font-weight: bold;
  color: #6e6b7b;
  font-size: .857rem;
}

.key-items-wrapper {
  overflow: auto;
  position:relative;
}

.key-items-wrapper ::v-deep.key-item-main:last-child .key-item-separator {
  display: none;
}

.regular-column {
  flex-basis:250px;
}
.regular-column-key-fiels {
  flex-basis:300px;
}

.action-column {
  flex-basis:90px;
}
</style>
