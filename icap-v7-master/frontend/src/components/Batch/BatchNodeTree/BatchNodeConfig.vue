<!--
 Organization: AIDocbuilder Inc.
 File: BatchNodeConfig.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   - A Vue component to manage and display configuration options for a specific node.
   - Provides a dropdown to change configurations such as 'Rules', 'Not in Use', 'Lookup', and 'Add to DB'.
   - The component interacts with Vuex store to retrieve and set configuration values.

 Features:
   - Dynamic rendering of dropdown options based on available configurations.
   - Disabling options based on the comparison of batch and selected definition versions.
   - Event handling to trigger actions such as adding items to "Not in Use", switching modes, and displaying forms.

 Dependencies:
   - bootstrap-vue - For dropdown components and UI elements.
   - feather-icons - For the dropdown toggle button icon.
   - Vuex - For managing application and batch state.

 Notes:
   - Ensure that Vuex store getters and actions are properly configured for batch and node-related state management.
-->
<template>
  <!-- Wrapper for the dropdown -->
  <div class="d-inline-block">
    <!-- Display the current configuration value -->
    <span class="font-italic mr-25">{{ configValue }}</span>

    <!-- Bootstrap Vue dropdown menu -->
    <b-dropdown
      dropleft
      no-flip
      no-caret
      variant="link"
      toggle-class="text-decoration-none"
      boundary="window"
      class="text-primary compact-dropdown"
      offset="-10"
    >
      <!-- Slot for the dropdown toggle button -->
      <template #button-content>
        <!-- Icon used as the dropdown button -->
        <feather-icon
          icon="MoreVerticalIcon"
          size="20"
          class="align-middle text-body"
        />
      </template>
      <!-- Dropdown items rendered dynamically from the options array -->
      <b-dropdown-item
        v-for="option of options"
        :key="option.value"
        :active="configValue === option"
        :disabled="option.disabled"
        @click.stop="option.value !== 'hideEmptyKeys' ? setConfigValue(option.value) : null"
      >
        <div
          v-if="option.value === 'hideEmptyKeys'"
          @click.stop
        >
          <b-form-checkbox
            v-model="hideEmptyAutoExtrationKeys"
            inline
          >
            {{ option.label }}
          </b-form-checkbox>
        </div>
        <span v-else>{{ option.label }}</span>
      </b-dropdown-item>
      <!-- <b-dropdown-item
        v-if="isProfileKeyFound && !['auto_extraction_parent','vendor','process_keys_parent'].includes(type) || isAddressBlockPartial"
        @click="triggerAddKeyToProfile"
      >
        Add To Process
        <AddKeyToProfile
          ref="addKeyToProfile"
          :label="isAddressBlockPartial ? formattedLabel : label"
          :document-id="documentId"
          :batch-id="batchId"
        />
      </b-dropdown-item> -->
      <b-dropdown-item
        v-if="(isLabelMapped || isKeyFromTable) && !['auto_extraction_parent','vendor','process_keys_parent'].includes(type)"
        @click="triggerResetMappedKey"
      >
        Reset Mapped Key
        <ResetMappedKey
          ref="resetMappedKey"
          :label="label"
          :original-key-label="originalKeyLabel"
          :nested-label="nestedLabel"
          :is-address-block-partial="isAddressBlockPartial"
          style="display: none;"
          :is-table-key="false"
          :document-id="documentId"
          :batch-id="batchId"
          @reset-success="handleResetSuccess"
        />
      </b-dropdown-item>
      <!-- Fallback item if there are no available options -->
      <b-dropdown-item
        v-if="options.length === 0"
        disabled
      >
        No Options <!-- Display message when no options are available -->
      </b-dropdown-item>
    </b-dropdown>
  </div>
</template>

<script>
import { BDropdownItem, BDropdown, BFormCheckbox } from 'bootstrap-vue' // Import Bootstrap Vue dropdown components
import bus from '@/bus' // Import a shared event bus for communication between components
// import AddKeyToProfile from './AddKeyToProfile.vue'
import ResetMappedKey from './ResetMappedKey.vue'

export default {
  components: {
    BDropdownItem,
    BDropdown,
    // AddKeyToProfile,
    ResetMappedKey,
    BFormCheckbox,
  },
  props: {
    // The unique identifier for the node
    nodeId: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      default: '',
    },
    documentId: {
      type: String,
      default: '',
    },
    batchId: {
      type: String,
      default: '',
    },
    type: {
      type: String, // Expects a string
      default: '',
    },
    isAddressBlockPartial: {
      type: Boolean,
      default: () => false,
    },
    // Label for nested configuration
    nestedLabel: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    // Identifier for the key
    keyId: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    // Configuration data for the node
    configData: {
      type: Object,
      required: true,
    },
    isProfileKeyFound: {
      type: Boolean,
      requred: false,
    },
    isLabelMapped: {
      type: Boolean,
      required: false,
      default: false,
    },
    isKeyFromTable: {
      type: Boolean,
      required: false,
      default: false,
    },
    originalKeyLabel: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    selectedDefintionVersion() {
      // Retrieve the selected definition version from Vuex store
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },
    batchDefinitionVersion() {
      // Retrieve the batch's definition version from Vuex store
      return this.$store.getters['batch/batch'].definitionVersion
    },
    batchTestedWithDiffrentVersion() {
      // Check if the selected and batch definition versions differ
      return this.selectedDefintionVersion !== this.batchDefinitionVersion
    },
    enableLookups() {
      // Determine if lookup functionality is enabled from application settings
      return this.$store.getters['applicationSettings/enableLookups']
    },
    options() {
      // Dynamically generate configuration options based on `configData.options`
      const configOptions = this.configData.options
      const options = []

      if (configOptions.includes('hideEmptyAutoExtrationKeys')) {
        // Add a "Rules" option
        options.push({
          label: 'Hide Empty Keys',
          value: 'hideEmptyKeys',
        })
      }

      if (configOptions.includes('rules')) {
        // Add a "Rules" option
        options.push({
          label: 'Rules',
          value: 'rules',
          disabled: false, // Disable if versions differ
        })
      }

      if (configOptions.includes('notInUse')) {
        // Add a "Not in Use" option
        options.push({
          label: 'Not in Use',
          value: 'notInUse',
          disabled: false,
        })
      }

      if (configOptions.includes('lookup') && this.enableLookups) {
        // Add a "Lookup" option if lookups are enabled
        options.push({
          label: 'Lookup',
          value: 'lookup',
          disabled: this.batchTestedWithDiffrentVersion,
        })
      }

      if (configOptions.includes('addToDB') && this.enableLookups) {
        // Add an "Add to DB" option if lookups are enabled
        options.push({
          label: 'Add to DB',
          value: 'addToDB',
          disabled: false,
        })
      }

      return options // Return the array of options
    },
    configValue() {
      // Retrieve the current configuration value for this node from Vuex store
      return this.$store.getters['batch/nodeConfig'][this.nodeId]
    },
    hideEmptyAutoExtrationKeys: {
      get() {
        const hideEmptyAutoExtrationKeys = this.$store.getters['batch/hideEmptyAutoExtrationKeys']
        // Check if this nodeId exists in the object, otherwise default to true
        return hideEmptyAutoExtrationKeys?.[this.nodeId] ?? true
      },
      set(value) {
        const currentSettings = this.$store.getters['batch/hideEmptyAutoExtrationKeys']
        // Create new object to avoid mutating the getter result
        const updatedSettings = {
          ...currentSettings,
          [this.nodeId]: value,
        }
        this.$store.commit('batch/SET_HIDE_EMPTY_AUTO_EXTRACTION_KEYS', updatedSettings)
      },
    },
    formattedLabel() {
      // Format label for address block partial nodes
      // If isAddressBlockPartial is true and nestedLabel exists,
      // transform "supplier.postalcode" to "supplier [address] postalcode"
      if (this.isAddressBlockPartial && this.nestedLabel) {
        const parts = this.nestedLabel.split('.')
        if (parts.length > 1) {
          // Insert [address] between the parts
          return `${parts[0]} [address] ${parts.slice(1).join('.')}`
        }
      }
      return this.nestedLabel
    },
  },
  methods: {
    setConfigValue(value) {
      // Handle different configuration values and trigger appropriate actions
      if (value === 'rules') {
        // Set key rule item and switch to 'key-rules' mode
        this.$store.dispatch('dataView/setKeyRuleItem', {
          id: this.nestedLabel,
          keyId: this.keyId,
        })
        this.$store.dispatch('dataView/setMode', 'key-rules')
      } else if (value === 'notInUse') {
        // Emit event to add the item to "Not in Use" and switch to the mode
        bus.$emit('addNotInUseItem', {
          keyId: this.keyId,
          nestedLabel: this.nestedLabel,
        })
        this.$store.dispatch('dataView/setMode', 'key-not-in-use-items')
      } else if (value === 'lookup') {
        // Switch to "key" view if not already in it and set key lookup item
        const batchView = this.$store.getters['batch/view']
        if (batchView !== 'key') {
          this.$store.commit('batch/SET_VIEW', 'key')
        }

        this.$nextTick(() => {
          // Set lookup item and switch to 'key-lookup' mode
          this.$store.dispatch('dataView/setKeyLookupItem', {
            keyId: this.keyId,
            nestedLabel: this.nestedLabel,
          })

          this.$store.dispatch('dataView/setMode', 'key-lookup')
        })
      } else if (value === 'addToDB') {
        // Emit event to display form for adding record to database
        const defaultData = this.configData.addToDBData
        bus.$emit('lookup/displayAddRecordForm', {
          record: defaultData.record,
          tableName: defaultData.tableName,
        })
      } else {
        // Reserved for additional configurations or actions
        // this.$store.dispatch('batch/setNodeConfig', { id: this.nodeId, value })
      }
    },
    triggerAddKeyToProfile() {
      // eslint-disable-next-line no-unused-expressions
      this.$refs.addKeyToProfile?.addToProfile()
    },
    triggerResetMappedKey() {
      // eslint-disable-next-line no-unused-expressions
      this.$refs.resetMappedKey?.openDialog()
    },
    handleResetSuccess(label) {
      // Emit event to parent component when reset is successful
      this.$emit('reset-mapped-key-success', label)
    },
  },
}
</script>

<style lang="scss" scoped>
.compact-dropdown {
  ::v-deep .dropdown-toggle {
    padding: 0 !important;
    margin: 0 !important;
    min-width: auto !important;
    line-height: 1 !important;
  }
}
</style>
