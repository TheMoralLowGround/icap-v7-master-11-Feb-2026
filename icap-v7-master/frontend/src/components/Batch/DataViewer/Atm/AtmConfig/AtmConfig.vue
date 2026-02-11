<template>
  <b-row>
    <!-- Row for Advanced Settings toggle -->

    <b-col
      cols="12"
      class="pt-1"
    >
      Advanced Settings
      <!-- ChevronDownIcon for hiding advanced settings -->
      <feather-icon
        v-if="advancedSettings"
        icon="ChevronDownIcon"
        class="cursor-pointer"
        size="20"
        @click.stop="advancedSettings = false"
      />
      <!-- ChevronUpIcon for showing advanced settings -->
      <feather-icon
        v-else
        icon="ChevronUpIcon"
        class="cursor-pointer"
        size="20"
        @click.stop="advancedSettings = true"
      />
    </b-col>
    <!-- Row for displaying configuration fields -->
    <b-col cols="12">
      <!-- Iterate over atmConfig entries -->
      <atm-config-field
        v-for="(item, i) in Object.entries(atmConfig)"
        :key="i"
        :value="item[1].value"
        :min="item[1].min"
        :label="StringCapitalize(item[0])"
        :advanced-settings="advancedSettings"
        @input="(value) => onEditConfig(item[0] , value)"
      />
    </b-col>
  </b-row>
</template>

<script>
import {
  BCol, BRow,
} from 'bootstrap-vue' // Import BootstrapVue components
import AtmConfigField from './AtmConfigField.vue' // Import AtmConfigField component

export default {
  components: {
    AtmConfigField, // Register AtmConfigField component
    BCol, // Register BCol component
    BRow, // Register BRow component
  },
  data() {
    return {
      advancedSettings: false, // Boolean to toggle advanced settings visibility
    }
  },
  computed: {
    // Get ATM configuration from Vuex store
    atmConfig() {
      return this.$store.getters['atm/atmConfig']
    },
  },
  methods: {
    /**
     * Capitalize a string by converting underscores to spaces
     * and capitalizing the first letter of each word.
     * Example: 'key_name' -> 'Key Name'
     * @param {string} str - The string to capitalize
     * @returns {string} - The capitalized string
     */
    StringCapitalize(str) {
      return str
        .split('_') // Split the string by underscores
        .map(i => i.charAt(0).toUpperCase() + i.slice(1)) // Capitalize the first letter of each word
        .join(' ') // Join the words with a space
    },

    /**
     * Handle updating the ATM configuration.
     * Commits the updated configuration to the Vuex store.
     * @param {string} key - The key of the configuration field
     * @param {any} value - The new value of the configuration field
     */
    onEditConfig(key, value) {
      const atmConfig = { ...this.atmConfig } // Clone the current atmConfig

      atmConfig[key] = { ...atmConfig[key], value } // Update the specific configuration field

      this.$store.commit('atm/SET_ATM_CONFIG', atmConfig) // Commit the updated configuration to the Vuex store
    },
  },
}
</script>
