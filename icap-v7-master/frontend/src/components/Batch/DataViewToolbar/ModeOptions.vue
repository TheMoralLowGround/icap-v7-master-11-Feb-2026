<!--
 Organization: AIDocbuilder Inc.
 File: ModeOptions.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component displays different mode options within the application for both key settings and table settings.
   It allows users to switch between various modes (e.g., 'key-items', 'table-models') by displaying buttons or dropdowns
   based on the current mode and available options. It also conditionally displays advanced options for each mode
   when available and allows for dynamic interaction with the system via Vuex actions.

 Main Features:
   - Displays mode options for both key and table settings
   - Supports both regular and advanced mode options, dynamically generated based on the settings
   - Uses dropdowns for advanced mode options when there are multiple items
   - Custom button variant styles for active modes
   - Emits mode change events through Vuex actions

 Dependencies:
   - Bootstrap Vue: For button groups, buttons, and dropdowns
   - Feather Icon: For ChevronDown icon
   - Vuex: For managing state and retrieving mode-related data

 Notes:
   - The component checks for enabled settings such as 'Lookups' before rendering mode options.
   - Conditional rendering is applied based on the current mode, enabling or disabling specific buttons.
   - Advanced options are displayed in a dropdown when available.
-->

<template>
  <b-button-group>
    <template
      v-if="displayActionableModes"
    >
      <b-button
        v-for="(modeOption, modeOptionIndex) of regularModeOptions"
        :key="modeOptionIndex"
        :variant="mode === modeOption.mode ? 'primary' : 'outline-primary'"
        @click="setMode(modeOption.mode)"
      >
        {{ modeOption.label }}
      </b-button>

      <b-dropdown
        v-if="advanceModeOptions.length > 0"
        right
        variant="outline-primary"
        no-caret
        size="sm"
      >
        <template #button-content>
          <feather-icon
            icon="ChevronDownIcon"
            size="20"
          />
        </template>

        <b-dropdown-item-button
          v-for="(modeOption, modeOptionIndex) of advanceModeOptions"
          :key="modeOptionIndex"
          button-class="w-100"
          :active="mode === modeOption.mode"
          @click="setMode(modeOption.mode)"
        >
          {{ modeOption.label }}
        </b-dropdown-item-button>
      </b-dropdown>
    </template>

    <template v-if="!displayActionableModes">
      <b-button
        v-if="mode === 'key-rules'"
        :variant="'primary'"
      >
        {{ keyRuleItem ? `Rules - ${keyRuleItem.id}` : 'Rules' }}
      </b-button>

      <!-- <b-button
        v-if="mode === 'key-lookup'"
        :variant="'primary'"
      >
        {{ keyLookupItem ? `Lookup - ${keyLookupItem.nestedLabel}` : 'Lookup' }}
      </b-button> -->

      <b-button
        v-if="mode === 'table-rules'"
        :variant="'primary'"
      >
        {{ tableRuleItem ? `Rules - ${tableRuleItem.label}` : 'Rules' }}
      </b-button>

      <b-button
        v-if="mode === 'table-lookup'"
        :variant="'primary'"
      >
        {{ tableLookupItem ? `Lookup - ${tableLookupItem.label}` : 'Lookup' }}
      </b-button>
    </template>
  </b-button-group>
</template>

<script>
import {
  VBTooltip, BDropdown, BDropdownItemButton, BButtonGroup, BButton,
} from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BButtonGroup,
    BDropdown,
    BDropdownItemButton,
    BButton,
  },
  computed: {
    // Retrieves the main mode (e.g., 'keySettings' or 'tableSettings') from Vuex store.
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },

    // Retrieves the current mode (e.g., 'key-items', 'table-models') from Vuex store.
    mode() {
      return this.$store.getters['dataView/mode']
    },

    // Checks if lookups are enabled by accessing the application settings in the Vuex store.
    enableLookups() {
      return this.$store.getters['applicationSettings/enableLookups']
    },

    // Defines available options for 'keySettings' mode.
    keyModeOptions() {
      let options = [
        {
          label: 'Keys', // Option label for display
          mode: 'key-items', // Mode identifier
          advanced: false, // Indicates if this is an advanced option
        },
        {
          label: 'Rules',
          mode: 'key-rule-items',
          advanced: false,
        },
        {
          label: 'Not in Use',
          mode: 'key-not-in-use-items',
          advanced: false,
        },
      ]

      // Adds a 'Lookups' option if lookups are enabled in the application settings.
      // if (this.enableLookups) {
      //   options.push({
      //     label: 'Lookups',
      //     mode: 'key-lookup-items',
      //     advanced: false,
      //   })
      // }

      // Appends an advanced 'Models' option to the list.
      options = options.concat([
        {
          label: 'Models',
          mode: 'key-models',
          advanced: true,
        },
      ])

      return options // Returns the complete list of key mode options.
    },

    // Defines available options for 'tableSettings' mode.
    tableModeOptions() {
      const options = [
        {
          label: 'Models',
          mode: 'table-models',
          advanced: false,
        },
        {
          label: 'Columns',
          mode: 'table-columns',
          advanced: false,
        },
        {
          label: 'Keys',
          mode: 'table-keys',
          advanced: false,
        },
        {
          label: 'Column Prompts',
          mode: 'table-column-prompts',
          advanced: false,
        },
        {
          label: 'Rules',
          mode: 'table-rule-items',
          advanced: false,
        },
        {
          label: 'Normalizer',
          mode: 'table-normalizer',
          advanced: false,
        },
        {
          label: 'Test',
          mode: 'test',
          advanced: false,
        },
      ]
      // Adds a 'Lookups' option if lookups are enabled in the application settings.
      // if (this.enableLookups) {
      //   options.push({
      //     label: 'Lookups',
      //     mode: 'table-lookup-items',
      //     advanced: false,
      //   })
      // }
      return options // Returns the list of table mode options.
    },

    // Determines the mode options based on the current main mode.
    modeOptions() {
      if (this.mainMode === 'keySettings') {
        return this.keyModeOptions
      }
      if (this.mainMode === 'tableSettings') {
        return this.tableModeOptions
      }
      return [] // Returns an empty list if no valid main mode is set.
    },

    // Filters regular (non-advanced) mode options and prefixes them with a numeric label.
    regularModeOptions() {
      return this.modeOptions.filter(modeOption => !modeOption.advanced).map((option, index) => {
        const newOption = { ...option }
        newOption.label = `${index + 1}. ${option.label}`
        return newOption
      })
    },

    // Filters advanced mode options and prefixes them with a numeric label starting after regular options.
    advanceModeOptions() {
      return this.modeOptions.filter(modeOption => modeOption.advanced).map((option, index) => {
        const newOption = { ...option }
        newOption.label = `${this.regularModeOptions.length + index + 1}. ${option.label}`
        return newOption
      })
    },

    // Checks if the current mode is included in the actionable modes.
    displayActionableModes() {
      return this.modeOptions
        .map(modeOption => modeOption.mode) // Extract mode identifiers
        .includes(this.mode) // Check if the current mode is among the actionable modes.
    },

    // Retrieves a specific key rule item from Vuex store.
    keyRuleItem() {
      return this.$store.getters['dataView/keyRuleItem']
    },

    // Retrieves a specific key lookup item from Vuex store.
    keyLookupItem() {
      return this.$store.getters['dataView/keyLookupItem']
    },
    tableLookupItem() {
      return this.$store.getters['dataView/tableLookupItem']
    },

    // Retrieves a specific table rule item from Vuex store.
    tableRuleItem() {
      return this.$store.getters['dataView/tableRuleItem']
    },
  },
  methods: {
    setMode(mode) {
      return this.$store.dispatch('dataView/setMode', mode)
    },
  },
}
</script>

<style scoped>
.btn {
  padding-left: 0.75rem !important;
  padding-right: 0.75rem !important;
  font-size: 12px;
}
</style>
