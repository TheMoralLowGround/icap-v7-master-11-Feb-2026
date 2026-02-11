<!--
 Organization: AIDocbuilder Inc.
 File: option.js
 Version: 1.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   This component provides a dynamic and reusable card interface for managing
   configurable options. It supports features such as adding, editing, deleting,
   and validating items dynamically. The component includes input fields for
   various types (checkbox, text, select), sorting functionality, and expand/collapse
   control for better UI management.

 Dependencies:
   - BootstrapVue: Used for card, form, and spinner components.
   - Vue-Select: For dropdowns with custom options.
   - Lodash: For deep cloning and equality checks.
   - Custom components:
     - AddItem: Button for adding new items.
     - SaveButton: Button for saving changes to the application settings.

 Main Features:
   - Dynamic input controls for text, checkbox, and select fields.
   - Expand/Collapse functionality for better UI experience.
   - Duplicate key validation with hash table tracking.
   - Sort functionality based on a specified field.
   - Integration with Vuex for retrieving and managing options.
   - Emits changes for two-way binding with the parent component.

 Core Components:
   - `<b-card>`: Main container for the card UI.
   - `<b-card-header>`: Header section with expand/collapse toggle and sorting button.
   - `<b-card-body>`: Content area with rows for dynamic fields and add/save actions.
   - `<v-select>`: Dropdown for select fields.
   - Custom AddItem and SaveButton components for adding items and persisting changes.

 Notes:
   - The component synchronizes internal state with the `value` prop for reactivity.
   - Hash-based validation prevents duplicate entries in the item list.
   - Expand/collapse state triggers hash table generation for validation purposes.
   - The `sortBy` prop is optional and adds sorting functionality if provided.
   - Inputs use debounce for performance optimization during typing.
 -->

<template>
  <!-- Card Component with No Body -->
  <b-card no-body>
    <!-- Card Header Section -->
    <b-card-header
      header-class="p-1"
      role="button"
      @click="expanded = !expanded"
    >
      <!-- Card Title -->
      <div>
        <!-- Displays the dynamic title of the card -->
        <h3 class="my-0">
          {{ title }}
        </h3>
      </div>

      <!-- Sort Button -->
      <!-- Conditionally renders if 'sortBy' is defined -->
      <b-button
        v-if="sortBy"
        size="sm"
        @click.stop="sortItems"
      >
        Sort by {{ sortBy }}
      </b-button>
    </b-card-header>

    <!-- Card Body Section -->
    <b-card-body
      v-show="expanded"
      class="table-card-body"
    >
      <div>
        <!-- Iterates over items and renders a row for each -->
        <div
          v-for="(item, index) of items"
          :key="index"
          class="field-row d-flex"
        >

          <!-- Displays the item's index (1-based) -->
          <div>
            {{ index + 1 }}
          </div>

          <!-- Iterate over fields to dynamically render input controls -->
          <div
            v-for="field of fields"
            :key="field.key"
            :class="{
              'field-wrapper': field.type !== 'checkbox',
              'field-wrapper-checkbox': field.type === 'checkbox'
            }"
          >
            <!-- Checkbox Input -->
            <b-form-group
              v-if="field.type === 'checkbox'"
              :label="field.key"
            >
              <!-- Two-way binding for checkbox value -->
              <b-form-checkbox
                v-model="items[index][field.key]"
                :value="true"
                :unchecked-value="false"
                :inline="field.key === 'export'"
                :switch="field.key === 'export'"
              />
            </b-form-group>

            <!-- Text Input -->
            <b-form-group
              v-if="field.type === 'text'"
              :label="field.key"
            >
              <div class="position-relative flex-grow-1">
                <b-form-input
                  :value="items[index][field.key]"
                  :placeholder="field.key"
                  type="text"
                  class="input-with-spinner"
                  @input="(e) => onInput(e, index, field.key)"
                  @focus="() => onFocus(index, items[index][field.key])"
                />
                <b-spinner
                  v-if="index === focusedIndex && valueKey === field.key && debounceTimeout"
                  small
                  class="position-absolute input-loader"
                  label="Input Loader"
                />
              </div>
              <p
                v-if="valueKey === field.key && hashItems[items[index][field.key]] > 1"
                class="is-duplicate"
              >
                This key already exist
              </p>
            </b-form-group>

            <!-- Select Input -->
            <b-form-group
              v-if="field.type === 'select'"
              :label="field.key"
            >
              <v-select
                v-model="items[index][field.key]"
                :label="options[field.optionsId].lableKey"
                :options="options[field.optionsId].items"
                :reduce="option => option[options[field.optionsId].valueKey]"
              />
            </b-form-group>

          </div>

          <!-- Delete Item Button -->
          <div>
            <feather-icon
              icon="Trash2Icon"
              class="delete-btn cursor-pointer mx-auto"
              size="20"
              @click="deleteItem(index)"
            />
          </div>
        </div>

        <!-- Add Item and Save Buttons -->
        <div class="add-item-row d-flex">
          <div class="add-item-btn">
            <add-item
              :label="title"
              @add="addItems"
            />
          </div>
          <!-- Save action for settings -->
          <div>
            <save-button action="applicationSettings/saveData" />
          </div>
        </div>
      </div>
    </b-card-body>
  </b-card>
</template>

<script>
import {
  BCard, BSpinner, BCardHeader, BCardBody, BFormInput, BButton, BFormGroup, BFormCheckbox,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'
import AddItem from '@/components/UI/AddItem.vue'
import SaveButton from '@/components/UI/SaveButton.vue'

export default {
  components: {
    // Registering BootstrapVue components and custom components
    BCard,
    BSpinner,
    BCardHeader,
    BCardBody,
    BButton,
    BFormInput,
    BFormGroup,
    BFormCheckbox,
    AddItem,
    vSelect,
    SaveButton,
  },
  props: {
    // Props passed from parent component
    value: {
      type: Array,
      required: true, // Expecting an array for binding
    },
    title: {
      type: String,
      required: true, // Title for the card component
    },
    fields: {
      type: Array,
      required: true, // Field definitions for dynamic item structure
    },
    sortBy: {
      type: String,
      required: false, // Field to sort items by, default is null
      default() {
        return null
      },
    },
    valueKey: {
      type: String,
      required: true, // Key used for identifying unique items
    },
  },
  data() {
    return {
      expanded: false, // State to control expand/collapse
      items: [], // Local array of items
      hashItems: {}, // Hash map for tracking duplicates
      textInput: '', // Text input for inline editing
      debounceTimeout: null, // Timeout for debounced input
      focusedIndex: null, // Index of currently focused item
    }
  },
  computed: {
    // Retrieve options from Vuex store
    options() {
      return this.$store.getters['applicationSettings/options']
    },
    // Create a deep copy of items for comparison
    out() {
      return cloneDeep(this.items)
    },
  },
  watch: {
    // Watch for changes in computed `out` and emit input events
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true, // Watch for nested changes
    },
    // Sync internal state when value prop changes
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
    // Generate hash table when expanded state changes
    expanded(newVal) {
      if (newVal) {
        this.generateHashTable()
      }
    },
  },
  created() {
    // Initialize internal state when component is created
    this.setInternalState()
  },
  methods: {
    // Sync internal state with `value` prop
    setInternalState() {
      const items = this.value.map(record => {
        const item = {}
        this.fields.forEach(field => {
          let fieldValue
          if (field.type === 'checkbox') {
            if (field.key === 'export' && typeof record.export === 'undefined') {
              fieldValue = true // Default checkbox for "export" is true
            } else {
              fieldValue = !!record[field.key] // Ensure boolean values
            }
          } else {
            fieldValue = String(record[field.key] || '') // Default to empty string
          }

          item[field.key] = fieldValue
        })
        return item
      })
      this.items = items
    },
    // Add new items with default values
    addItems(count) {
      const cols = []

      for (let i = 0; i < count; i += 1) {
        const col = {}

        this.fields.forEach(field => {
          let fieldValue

          if (field.type === 'checkbox') {
            fieldValue = field.key === 'export' // Default "export" checkbox
          } else {
            fieldValue = '' // Default text value
          }

          col[field.key] = fieldValue
        })

        cols.push(col)
      }

      this.items = this.items.concat(cols) // Append new items to the list
    },
    // Delete an item and update hash table
    deleteItem(index) {
      this.syncHashItems(index)

      this.items.splice(index, 1) // Remove item from the array

      this.focusedIndex = null
    },
    // Sort items based on `sortBy` prop
    sortItems() {
      this.items = cloneDeep(this.items).sort((a, b) => {
        const valueA = a[this.sortBy].toUpperCase()
        const valueB = b[this.sortBy].toUpperCase()

        if (valueA < valueB) { return -1 }
        if (valueA > valueB) { return 1 }
        return 0
      })
    },
    // Handle focus event for input fields
    onFocus(index, value) {
      this.focusedIndex = index
      this.textInput = value
    },
    // Handle input change with debounce
    onInput(newKeyValue, index, keyField) {
      this.textInput = newKeyValue

      clearTimeout(this.debounceTimeout)

      this.debounceTimeout = setTimeout(() => {
        const oldKeyValue = this.items[index][keyField]

        if (this.valueKey === keyField) {
          this.checkDuplicate(oldKeyValue, newKeyValue, index)
        }

        this.items[index][keyField] = this.textInput
        this.debounceTimeout = null
      }, 100)
    },
    // Generate hash table for duplicate tracking
    generateHashTable() {
      const hashItems = {}

      this.items.forEach(item => {
        if (!item[this.valueKey]) {
          return
        }

        if (!hashItems[item[this.valueKey]]) {
          hashItems[item[this.valueKey]] = 1
          return
        }

        hashItems[item[this.valueKey]] += 1
      })

      this.hashItems = hashItems
    },
    // Check and update duplicate entries
    checkDuplicate(oldKeyValue, newKeyValue) {
      const hashItems = { ...this.hashItems }

      // Add newKey or increase newKey count to hashItems
      if (!hashItems[newKeyValue]) {
        if (newKeyValue) {
          hashItems[newKeyValue] = 1
        }
      } else {
        hashItems[newKeyValue] += 1
      }

      this.hashItems = this.reduceHashItems(hashItems, oldKeyValue)
    },
    // Sync hash table when an item is deleted
    syncHashItems(index) {
      const hashItems = { ...this.hashItems }
      const hashKey = this.items[index][this.valueKey]

      this.hashItems = this.reduceHashItems(hashItems, hashKey)
    },
    // Reduce hash table counts and remove zero counts
    reduceHashItems(hashItemsParam, hashKey) {
      const hashItems = { ...hashItemsParam }

      // reduce hashKey count from hashItems if exist
      if (hashItems[hashKey]) {
        hashItems[hashKey] -= 1
      }

      // remove hashKey from hashItems if needed
      if (hashItems[hashKey] === 0) {
        delete hashItems[hashKey]
      }

      return hashItems
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style lang="scss" scoped>
.table-card-body {
  padding-top: 1.5rem !important;
}
.field-row {
  column-gap: 10px;
}
.field-wrapper {
  flex-basis: 300px;
}
.field-wrapper-checkbox {
  flex-basis: 150px;
}
.delete-btn {
  margin-top: 35px
}
.add-item-row {
  column-gap: 10px;
}
.add-item-btn {
  flex-basis:250px;
}
.is-duplicate {
  margin-top: 2px;
  color: #d6604f;
  font-weight: 500;
}

.input-with-spinner {
  padding-right: 30px;
}

.input-loader {
  top: 30%;
  right: 10px;
}

</style>
