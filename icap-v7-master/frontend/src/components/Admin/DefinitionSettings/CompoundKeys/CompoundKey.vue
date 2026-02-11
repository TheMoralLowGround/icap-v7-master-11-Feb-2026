<template>
  <b-card no-body>
    <b-card-header
      header-class="p-1"
      role="button"
      @click="$emit('toggle-expand')"
    >
      <h3 class="my-0">
        {{ title }}
      </h3>
      <div>
        <feather-icon
          v-b-tooltip.hover
          title="Delete Compound Key"
          icon="Trash2Icon"
          class="cursor-pointer"
          size="22"
          @click.stop="$emit('delete')"
        />
      </div>
    </b-card-header>

    <b-card-body
      v-show="expanded"
    >
      <b-row>
        <b-col lg="2">
          <b-form-group
            label="Name"
          >
            <b-form-input
              v-model="compoundKey.name"
              type="text"
              placeholder="Name"
            /></b-form-group>
        </b-col>
      </b-row>

      <label
        class="mb-b"
        style="font-size:inherit;"
      >Keys</label>
      <b-row>
        <b-col
          v-for="(compoundKeyOptions, index) of compoundKey.keyItems"
          :key="index"
          lg="12"
        >
          <div
            class="fields-row d-flex align-items-center"
          >
            <div>
              {{ index + 1 }}
            </div>

            <div class="field-wrapper">
              <b-form-group
                label="keyLabel"
              >
                <b-form-input
                  v-model="compoundKey.keyItems[index].keyLabel"
                  type="text"
                  placeholder="keyLabel"
                />
              </b-form-group>
            </div>
            <div class="field-wrapper">
              <b-form-group
                label="keyValue"
              >
                <div class="position-relative flex-grow-1">
                  <b-form-input
                    :value="compoundKey.keyItems[index].keyValue"
                    type="text"
                    placeholder="keyValue"
                    class="input-with-spinner"
                    @input="(e) => onInput(e, index)"
                    @focus="() => onFocus(index, compoundKey.keyItems[index].keyValue)"
                  />
                  <b-spinner
                    v-if="index === focusedIndex && debounceTimeout"
                    small
                    class="position-absolute input-loader"
                    label="Input Loader"
                  />
                </div>
                <p
                  v-if="hashItems[compoundKey.keyItems[index].keyValue] > 1"
                  class="is-duplicate"
                >
                  This key already exist
                </p>
              </b-form-group>
            </div>

            <div class="field-wrapper">
              <b-form-group
                label="type"
              >
                <v-select
                  v-model="compoundKey.keyItems[index].type"
                  :label="options['options-col-type'].lableKey"
                  :options="options['options-col-type'].items"
                  :reduce="option => option[options['options-col-type'].valueKey]"
                />
              </b-form-group>
            </div>

            <div class="field-wrapper">
              <b-form-group
                label="qualifier"
              >
                <v-select
                  v-model="compoundKey.keyItems[index].qualifier"
                  :options="qualifierOptions"
                />
              </b-form-group>
            </div>

            <div class="field-wrapper">
              <b-form-group
                label="modType"
              >
                <v-select
                  v-model="compoundKey.keyItems[index].modType"
                  :label="options['options-col-modType'].lableKey"
                  :options="options['options-col-modType'].items"
                  :reduce="option => option[options['options-col-modType'].valueKey]"
                />
              </b-form-group>
            </div>

            <feather-icon
              v-b-tooltip.hover
              title="Delete Key"
              icon="Trash2Icon"
              class="cursor-pointer ml-1"
              size="22"
              @click.stop="deleteOption(index)"
            />
          </div>
        </b-col>
      </b-row>

      <b-row class="mt-1">
        <b-col lg="2">
          <add-item
            label="Key"
            @add="addKeyItem"
          />
        </b-col>
        <save-button action="definitionSettings/saveData" />
      </b-row>
    </b-card-body>
  </b-card>
</template>

<script>

import {
  BCard, BSpinner, BCardHeader, BCardBody, VBTooltip, BRow, BCol, BFormGroup, BFormInput,
} from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import vSelect from 'vue-select'

import AddItem from '@/components/UI/AddItem.vue'
import SaveButton from '@/components/UI/SaveButton.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BCard,
    BSpinner,
    BCardHeader,
    BCardBody,
    BRow,
    BCol,
    BFormGroup,
    BFormInput,
    AddItem,
    SaveButton,
    vSelect,
  },
  props: {
    // The `value` prop holds the object to be edited or displayed in the component
    value: {
      type: Object,
      required: true,
    },
    // The unique ID of the component or compound key
    id: {
      type: Number,
      required: true,
    },
    // Controls whether the component is expanded or collapsed
    expanded: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      // Internal representation of the compound key
      compoundKey: {},
      // Stores hash items for quick lookup
      hashItems: {},
      // Stores the current text input from the user
      textInput: '',
      // Timeout ID for the debounce logic to optimize input handling
      debounceTimeout: null,
      // Tracks the index of the currently focused item in the UI
      focusedIndex: null,
    }
  },
  computed: {
    // Dynamically determines the title based on the compound key name or falls back to a default value
    title() {
      return this.compoundKey.name ? this.compoundKey.name : `Compound Key ${this.id}`
    },
    // Fetches options from the Vuex store for definition settings
    options() {
      return this.$store.getters['definitionSettings/options']
    },
    // Creates a deep clone of the `compoundKey` to emit as output
    out() {
      return cloneDeep(this.compoundKey)
    },
    // Retrieves the key qualifiers from the Vuex store
    keyQualifiers() {
      return this.$store.getters['definitionSettings/keyQualifiers']
    },
    // Maps key qualifiers to their names to create options for selection
    qualifierOptions() {
      return this.keyQualifiers.map(qualifier => qualifier.name)
    },
  },
  watch: {
    // Watches for changes in the `out` computed property
    out: {
      handler(val) {
        // Emits the updated value if it differs from `keyValue`
        if (!isEqual(val, this.keyValue)) {
          this.$emit('input', val)
        }
      },
      deep: true, // Ensures nested changes are detected
    },
    // Watches for changes in the `value` prop
    value: {
      handler(val) {
        // Updates the internal state if the new value differs from `out`
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true, // Detects deep changes in the `value` object
    },
    // Watches for changes in the `expanded` prop
    expanded(newVal) {
      // Generates a hash table when the component is expanded
      if (newVal) {
        this.generateHashTable()
      }
    },
  },
  created() {
    // Initializes the internal state of the component on creation
    this.setInternalState()
  },
  methods: {
    // Sets the internal state of the component by deep cloning the value prop
    setInternalState() {
      this.compoundKey = cloneDeep(this.value)
    },

    // Adds a specified number of new key items to the `keyItems` array in `compoundKey`
    addKeyItem(count) {
      const keyItems = []
      for (let i = 0; i < count; i += 1) {
        keyItems.push({
          keyLabel: '', // Label of the key
          keyValue: '', // Value of the key
          type: '', // Type of the key
          qualifier: '', // Qualifier for the key
          modType: '', // Modification type of the key
        })
      }
      // Concatenates the new key items with the existing `keyItems` array
      this.compoundKey.keyItems = this.compoundKey.keyItems.concat(keyItems)
    },

    // Deletes a key item at a specified index and updates the hash table
    deleteOption(index) {
      this.syncHashItems(index) // Updates the hash items to reflect the deletion
      this.compoundKey.keyItems.splice(index, 1) // Removes the key item
      this.focusedIndex = null // Clears the focus
    },

    // Handles the focus event on a key item, storing its index and value
    onFocus(index, value) {
      this.focusedIndex = index
      this.textInput = value
    },

    // Handles input changes on a key item with debounce logic
    onInput(newKeyValue, index) {
      this.textInput = newKeyValue
      clearTimeout(this.debounceTimeout) // Clears any existing timeout
      this.debounceTimeout = setTimeout(() => {
        const oldKeyValue = this.compoundKey.keyItems[index].keyValue
        this.checkDuplicate(oldKeyValue, newKeyValue, index) // Checks for duplicates
        this.compoundKey.keyItems[index].keyValue = this.textInput // Updates the value
        this.debounceTimeout = null
      }, 100) // Debounce delay of 100ms
    },

    // Generates a hash table to track the occurrence of each `keyValue`
    generateHashTable() {
      const hashItems = {}

      this.compoundKey.keyItems.forEach(item => {
        if (!item.keyValue) {
          return
        }

        if (!hashItems[item.keyValue]) {
          hashItems[item.keyValue] = 1 // Adds the key to the hash table
          return
        }
        hashItems[item.keyValue] += 1 // Increments the count for the key
      })

      this.hashItems = hashItems
    },

    // Checks for duplicates and updates the hash table with the new and old key values
    checkDuplicate(oldKeyValue, newKeyValue) {
      const hashItems = { ...this.hashItems }
      // Add or increment the count of the new key value
      if (!hashItems[newKeyValue]) {
        if (newKeyValue) {
          hashItems[newKeyValue] = 1
        }
      } else {
        hashItems[newKeyValue] += 1
      }
      this.hashItems = this.reduceHashItems(hashItems, oldKeyValue) // Reduces the old key value count
    },

    // Synchronizes the hash table when a key item is deleted
    syncHashItems(index) {
      const hashItems = { ...this.hashItems }
      const hashKey = this.compoundKey.keyItems[index].keyValue
      this.hashItems = this.reduceHashItems(hashItems, hashKey) // Reduces the hash count for the deleted key
    },

    // Reduces the count of a specified key in the hash table and removes it if the count reaches 0
    reduceHashItems(hashItemsParam, hashKey) {
      const hashItems = { ...hashItemsParam }

      // reduce hashKey count from hashItems if exist
      if (hashItems[hashKey]) {
        hashItems[hashKey] -= 1 // Decreases the count
      }

      // remove hashKey from hashItems if needed
      if (hashItems[hashKey] === 0) {
        delete hashItems[hashKey] // Removes the key from the hash table if the count is 0
      }

      return hashItems
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style scoped>
.fields-row {
  column-gap: 1rem;
}
.field-wrapper {
  flex-basis: 300px;
}
.isDuplicate{
  color: #d6604f;
  font-weight: 500;
}
.input-with-spinner {
  padding-right: 30px;
}
.is-duplicate {
  margin-top: 2px;
  color: #d6604f;
  font-weight: 500;
}
.input-loader {
  top: 30%;
  right: 10px;
}
</style>
