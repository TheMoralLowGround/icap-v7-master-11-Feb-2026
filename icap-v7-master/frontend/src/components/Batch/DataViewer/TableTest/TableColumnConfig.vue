<!--
 Organization: AIDocbuilder Inc.
 File: BatchNodeTree.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component represents a batch node tree structure, which is used to display
   and manage hierarchical data related to nodes in a batch. The tree component allows
   users to interact with and manage batch nodes, supporting features like node selection,
   filtering, and actions based on user input.

 Features:
   - Dynamic rendering of batch nodes in a tree structure.
   - Support for node selection and action triggering.
   - Integration with Vuex for state management of selected nodes and other actions.
   - Performance optimization for handling large datasets.
   - User-friendly interface with expandable/collapsible node functionality.

 Dependencies:
   - BootstrapVue (for UI components like buttons, dropdowns, etc.)
   - Vuex (for managing the state of selected nodes and batch data)
   - [Other dependencies, if any]

 Notes:
   - Ensure that the tree is optimized for handling large numbers of nodes.
   - The component integrates with batch-related Vuex modules to handle data and actions.
   - Used in batch management workflows for visualization and interaction with nodes.

-->

<template>
  <div class="d-inline-block">
    <b-dropdown
      right
      no-caret
      variant="link"
      block
      toggle-class="p-0"
    >
      <template #button-content>
        <slot>
        <!-- <feather-icon
          icon="SettingsIcon"
          size="16"
          class="cursor-pointer"
        /> -->
        </slot>
      </template>

      <template v-if="!isColumnMappedToKey">
        <b-dropdown-item
          v-for="option of options"
          :key="option.value"
          @click.stop="selectOption(option.value)"
        >
          {{ option.label }}
        </b-dropdown-item>
      </template>
      <b-dropdown-item
        v-if="!isColumnMappedToKey && !isLabelMapped"
        @click="triggerAddKeyToProfile"
      >
        Map to Column
        <AddKeyToProfile
          ref="addKeyToProcess"
          :label="label"
          add-type="table"
          type="table"
          title="Add  Mapped Column To Project"
          :is-table-key="false"
          :batch-id="selectedBatchId"
          :document-id="selectedDocumentId"
        />
      </b-dropdown-item>
      <b-dropdown-item
        v-if="!isColumnMappedToKey && !isLabelMapped"
        @click="triggerAddKeyAsColumnToProfile"
      >
        Map to Keys
        <AddKeyToProfile
          ref="addCloumnKeyToProcess"
          :label="label"
          type="key"
          add-type="table"
          title="Add Mapped Keys To Project"
          :is-table-key="true"
          :reverse="true"
          :batch-id="selectedBatchId"
          :document-id="selectedDocumentId"
        />
      </b-dropdown-item>
      <b-dropdown-item
        v-if="isColumnMappedToKey || isLabelMapped"
        @click="triggerResetMappedKey"
      >
        Reset Mapped {{ isColumnMappedToKey ? 'Key' : 'Column' }}
        <ResetMappedKey
          ref="resetMappedKey"
          :label="label"
          :original-key-label="currentField.originalKey"
          :batch-id="selectedBatchId"
          :document-id="selectedDocumentId"
          @reset-success="handleResetSuccess"
        />
      </b-dropdown-item>
    </b-dropdown>
  </div>
</template>

<script>
import { BDropdownItem, BDropdown } from 'bootstrap-vue'
import AddKeyToProfile from '@/components/Batch/BatchNodeTree/AddKeyToProfile.vue'
import ResetMappedKey from '@/components/Batch/BatchNodeTree/ResetMappedKey.vue'

export default {
  components: {
    BDropdownItem,
    BDropdown,
    AddKeyToProfile,
    ResetMappedKey,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    tableFields: {
      type: Array,
      required: true,
    },
    isColumnMappedToKey: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      options: [
        {
          label: 'Rules',
          value: 'rules',
        },
        {
          label: 'Lookup',
          value: 'lookup',
        },
      ],
    }
  },
  computed: {
    configValue() {
      return this.$store.getters['batch/nodeConfig'][this.nodeId]
    },
    currentField() {
      return this.tableFields.find(field => field.label === this.label) || {}
    },
    isLabelMapped() {
      return this.currentField.isLabelMapped || false
    },
    selectedBatchId() {
      return this.$store.getters['batch/selectedBatchId']
    },
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },
  },
  methods: {
    triggerAddKeyToProfile() {
      // eslint-disable-next-line no-unused-expressions
      this.$refs.addKeyToProcess?.addToProfile()
    },
    triggerResetMappedKey() {
      // eslint-disable-next-line no-unused-expressions
      this.$refs.resetMappedKey?.openDialog()
    },
    handleResetSuccess(label) {
      // Emit event to parent component when reset is successful
      this.$emit('reset-mapped-key-success', label)
    },
    triggerAddKeyAsColumnToProfile() {
      // eslint-disable-next-line no-unused-expressions
      this.$refs.addCloumnKeyToProcess?.addToProfile()
    },
    selectOption(value) {
      if (value === 'rules') {
        this.$store.dispatch('dataView/setTableRuleItem', {
          label: this.label,
        })
        this.$store.dispatch('dataView/setMode', 'table-rules')
      } else if (value === 'lookup') {
        // Switch to "table" view if not already in it and set key lookup item
        const batchView = this.$store.getters['batch/view']
        if (batchView !== 'table') {
          this.$store.commit('batch/SET_VIEW', 'table')
        }
        this.$nextTick(() => {
          // Set lookup item and switch to 'key-lookup' mode
          this.$store.dispatch('dataView/setTableLookupItem', {
            label: this.label,
          })

          this.$store.dispatch('dataView/setMode', 'table-lookup')
          // Extract labels from tableFields objects for backward compatibility
          const fieldLabels = this.tableFields.map(field => field?.label || field)
          this.$store.commit('dataView/SET_TABLE_FIELDS', fieldLabels)
        })
      } else if (value === 'addToProfile') {
        // console.log('test')
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.config-dropdown {
    opacity: 0;

    &.show {
        opacity: 1;
    }

    &:hover {
        opacity: 1;
    }

    ::v-deep .btn {
        padding: 0px !important;
    }
}
.custom-btn-css {
  padding: 4px !important;
}
</style>
