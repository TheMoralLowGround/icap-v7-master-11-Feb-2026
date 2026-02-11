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
          title="Delete Qualifier"
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
              v-model="qualifier.name"
              type="text"
              placeholder="Name"
            /></b-form-group>
        </b-col>
      </b-row>

      <label
        class="mb-b"
        style="font-size:inherit;"
      >Options</label>
      <b-row>
        <b-col
          v-for="(qualifierOptions, index) of qualifier.options"
          :key="index"
          lg="12"
        >
          <div
            class="d-flex align-items-center"
            style="column-gap: 1rem;"
          >
            <div style="flex-basis: 25px">
              {{ index + 1 }}
            </div>
            <div style="flex-basis: 400px">
              <b-form-group
                label="Option Label"
              >
                <b-form-input
                  v-model="qualifier.options[index].label"
                  type="text"
                  placeholder="Option Label"
                />
              </b-form-group>
            </div>
            <div style="flex-basis: 400px">
              <b-form-group
                label="Option Value"
              >
                <div class="position-relative flex-grow-1">
                  <b-form-input
                    :value="qualifier.options[index].value"
                    type="text"
                    placeholder="Option Value"
                    class="input-with-spinner"
                    @input="(e) => onInput(e, index)"
                    @focus="() => onFocus(index, qualifier.options[index].value)"
                  />
                  <b-spinner
                    v-if="index === focusedIndex && debounceTimeout"
                    small
                    class="position-absolute input-loader"
                    label="Input Loader"
                  />
                </div>
                <p
                  v-if="hashItems[qualifier.options[index].value] > 1"
                  class="is-duplicate"
                >
                  This key already exist
                </p>
              </b-form-group>
            </div>
            <div style="flex-basis: 400px">
              <b-form-group
                label="type"
              >
                <v-select
                  v-model="qualifier.options[index].type"
                  :label="options['options-col-type'].lableKey"
                  :options="options['options-col-type'].items"
                  :reduce="option => option[options['options-col-type'].valueKey]"
                />
              </b-form-group>
            </div>
            <div style="flex-basis: 400px">
              <b-form-group
                label="modType"
              >
                <v-select
                  v-model="qualifier.options[index].modType"
                  :label="options['options-col-modType'].lableKey"
                  :options="options['options-col-modType'].items"
                  :reduce="option => option[options['options-col-modType'].valueKey]"
                />
              </b-form-group>
            </div>
            <feather-icon
              v-b-tooltip.hover
              title="Delete Option"
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
            label="Option"
            @add="addOption"
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
import AddItem from '@/components/UI/AddItem.vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'
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
    // Object representing the qualifier data, passed from the parent component
    value: {
      type: Object,
      required: true,
    },
    // Numeric ID for the component instance
    id: {
      type: Number,
      required: true,
    },
    // Boolean indicating whether the component is expanded
    expanded: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      qualifier: {}, // Local copy of the qualifier object
      hashItems: {}, // Hash table to track duplicates in options
      textInput: '', // Stores the current text input for an option
      debounceTimeout: null, // Timeout ID for debouncing input events
      focusedIndex: null, // Index of the currently focused option
    }
  },
  computed: {
    // Returns the title for the qualifier; uses its name if available, otherwise a default title
    title() {
      return this.qualifier.name ? this.qualifier.name : `Qualifier ${this.id}`
    },
    // Retrieves options from the Vuex store
    options() {
      return this.$store.getters['definitionSettings/options']
    },
    // Creates a deep clone of the qualifier for comparison purposes
    out() {
      return cloneDeep(this.qualifier)
    },
  },
  watch: {
    // Emits updated value to the parent when the qualifier changes
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    // Updates the internal state when the input value changes
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
    // Generates the hash table when the component is expanded
    expanded(newVal) {
      if (newVal) {
        this.generateHashTable()
      }
    },
  },
  created() {
    this.setInternalState() // Sets the initial state when the component is created
  },
  methods: {
    // Initializes the internal state of the component with a deep clone of the prop value
    setInternalState() {
      this.qualifier = cloneDeep(this.value)
    },

    // Adds a specified number of empty options to the qualifier
    addOption(count) {
      const options = []
      for (let i = 0; i < count; i += 1) {
        options.push({
          label: null,
          value: null,
          type: '',
          modType: '',
        })
      }
      this.qualifier.options = this.qualifier.options.concat(options)
    },

    // Deletes an option at the specified index and synchronizes the hash table
    deleteOption(index) {
      this.syncHashItems(index) // Updates the hash table for duplicates
      this.qualifier.options.splice(index, 1) // Removes the option
      this.focusedIndex = null // Resets the focused index
    },

    // Updates the focused index and stores the current text input
    onFocus(index, value) {
      this.focusedIndex = index
      this.textInput = value
    },

    // Handles input changes with a debounce mechanism and updates the qualifier
    onInput(newKeyValue, index) {
      this.textInput = newKeyValue
      clearTimeout(this.debounceTimeout) // Clears any previous timeout
      this.debounceTimeout = setTimeout(() => {
        const oldKeyValue = this.qualifier.options[index].value
        this.checkDuplicate(oldKeyValue, newKeyValue, index) // Checks for duplicates
        this.qualifier.options[index].value = this.textInput // Updates the qualifier
        this.debounceTimeout = null
      }, 100) // Debounce delay of 100ms
    },

    // Generates a hash table to track the frequency of option values
    generateHashTable() {
      const hashItems = {}

      this.qualifier.options.forEach(item => {
        if (!item.value) return
        hashItems[item.value] = (hashItems[item.value] || 0) + 1
      })

      this.hashItems = hashItems
    },

    // Updates the hash table to account for old and new values during input changes
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

    // Synchronizes the hash table when an option is deleted
    syncHashItems(index) {
      const hashItems = { ...this.hashItems }
      const hashKey = this.qualifier.options[index].value

      this.hashItems = this.reduceHashItems(hashItems, hashKey)
    },

    // Reduces the count of a hash key or removes it from the hash table if its count is zero
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
