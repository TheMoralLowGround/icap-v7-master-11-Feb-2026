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

            <!-- Qualifier Input -->
            <b-form-group
              v-if="field.type === 'qualifier'"
              :label="field.key"
            >
              <v-select
                v-model="items[index][field.key]"
                :options="qualifierOptions"
              />
            </b-form-group>

            <!-- compoundKeys Input -->
            <b-form-group
              v-if="field.type === 'compoundKeys'"
              :label="field.key"
            >
              <v-select
                v-model="items[index][field.key]"
                :options="compoundKeyOptions"
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
            <save-button action="definitionSettings/saveData" />
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
    // Array of items passed to the component
    value: {
      type: Array, // Must be an array
      required: true, // Value is mandatory
    },
    // Title for the component, displayed in the UI
    title: {
      type: String, // Must be a string
      required: true, // Title is mandatory
    },
    // List of fields describing the structure of items
    fields: {
      type: Array, // Must be an array
      required: true, // Fields are mandatory
    },
    // Optional property to specify sorting criteria
    sortBy: {
      type: String, // Must be a string
      required: false, // Sorting is optional
      default() {
        return null // Default value is null if not provided
      },
    },
    // Key used to uniquely identify items
    valueKey: {
      type: String, // Must be a string
      required: true, // ValueKey is mandatory
    },
  },
  data() {
    return {
      expanded: false, // Tracks whether the component is expanded or collapsed
      items: [], // Internal representation of the items
      hashItems: {}, // Hash table for faster lookup of items
      textInput: '', // Input field for text (e.g., search or filtering)
      debounceTimeout: null, // Timeout for debouncing input events
      focusedIndex: null, // Tracks which item is currently focused
    }
  },
  computed: {
    // Retrieves options from the Vuex store
    options() {
      return this.$store.getters['definitionSettings/options']
    },
    // Returns a deep copy of `items` to avoid direct mutation
    out() {
      return cloneDeep(this.items)
    },
    // Retrieves key qualifiers from the Vuex store
    keyQualifiers() {
      return this.$store.getters['definitionSettings/keyQualifiers']
    },
    // Maps key qualifiers to their names for display or selection
    qualifierOptions() {
      return this.keyQualifiers.map(qualifier => qualifier.name)
    },
    // Retrieves compound keys from the Vuex store
    compoundKeys() {
      return this.$store.getters['definitionSettings/compoundKeys']
    },
    // Maps compound keys to their names for display or selection
    compoundKeyOptions() {
      return this.compoundKeys.map(compoundKey => compoundKey.name)
    },
  },
  watch: {
    // Watches changes to `out` (deep comparison)
    out: {
      handler(val) {
        // If `out` changes and differs from `value`, emit the updated value
        if (!isEqual(val, this.value)) {
          this.$emit('input', val) // Triggers the `input` event for v-model
        }
      },
      deep: true, // Watches nested changes in `out`
    },
    // Watches changes to the `value` prop (deep comparison)
    value: {
      handler(val) {
        // If `value` changes and differs from `out`, sync internal state
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true, // Watches nested changes in `value`
    },
    // Watches the `expanded` state
    expanded(newVal) {
      // When the component is expanded, generate a hash table for items
      if (newVal) {
        this.generateHashTable()
      }
    },
  },
  created() {
    // Initializes the internal state when the component is created
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

      // Remove item from the array
      this.items.splice(index, 1)

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
