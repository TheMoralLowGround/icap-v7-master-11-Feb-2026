<template>
  <b-modal
    :visible="visible"
    title="Manage Columns"
    size="lg"
    scrollable
    centered
    ok-title="Save"
    cancel-title="Cancel"
    modal-class="party-columns-modal"
    :no-close-on-backdrop="deletingColumnIndex !== null || isSaving"
    :no-close-on-esc="deletingColumnIndex !== null || isSaving"
    @ok="handleSave"
    @hidden="handleClose"
  >
    <b-overlay
      :show="deletingColumnIndex !== null || isSaving"
      rounded="sm"
      opacity="0.6"
      spinner-variant="primary"
      spinner-type="grow"
    >
      <template #overlay>
        <div class="text-center">
          <b-spinner
            variant="primary"
            style="width: 3rem; height: 3rem;"
          />
          <p class="mt-3 mb-0 font-weight-bold">
            {{ deletingColumnIndex !== null ? 'Deleting column...' : 'Saving changes...' }}
          </p>
          <p class="text-muted small mb-0">
            Please wait, do not close this dialog
          </p>
        </div>
      </template>
      <div class="party-columns-container">
      <!-- Existing Columns List -->
      <div
        v-if="columns.length > 0"
        class="columns-list mb-3"
      >
        <h6 class="mb-2">
          Columns
        </h6>
        <div
          v-for="(column, index) in columns"
          :key="index"
          class="d-flex align-items-center mb-2 p-2 border rounded"
        >
          <!-- Column Name -->
          <div class="flex-grow-1 mr-2">
            <v-select
              v-model="column.selectedKey"
              :options="filteredAvailableColumns"
              :reduce="option => option.keyValue"
              label="label"
              placeholder="Select column..."
              :clearable="false"
              :disabled="column.isFirstColumn"
            >
              <template #option="{ label }">
                <span>{{ label }}</span>
              </template>
              <template #selected-option="{ label }">
                <span>{{ label }}</span>
              </template>
            </v-select>
          </div>

          <!-- Delete Button -->
          <div>
            <b-button
              v-if="column.isdeletable"
              variant="outline-danger"
              size="sm"
              :disabled="deletingColumnIndex === index || isSaving"
              @click="removeColumn(index)"
            >
              <b-spinner
                v-if="deletingColumnIndex === index"
                small
                class="mr-1"
              />
              <feather-icon
                v-else
                icon="TrashIcon"
                size="16"
              />
            </b-button>
            <b-button
              v-else
              v-b-tooltip.hover
              variant="outline-secondary"
              size="sm"
              disabled
              :title="column.isFirstColumn ? 'First column cannot be deleted' : 'Fixed column cannot be deleted'"
            >
              <feather-icon
                icon="LockIcon"
                size="16"
              />
            </b-button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else
        class="text-center text-muted my-4"
      >
        <p>No columns added yet. Click "Add New Column" to get started.</p>
      </div>

      <!-- Add New Column Button -->
      <div class="mt-3">
        <b-button
          variant="outline-primary"
          size="md"
          block
          :disabled="deletingColumnIndex !== null || isSaving"
          @click="addNewColumn"
        >
          <feather-icon
            icon="PlusIcon"
            size="16"
            class="mr-1"
          />
          Add New Column
        </b-button>
      </div>

      <!-- Validation Error -->
      <b-alert
        v-if="validationError"
        variant="danger"
        show
        class="mt-3 p-1"
        @dismissed="validationError = ''"
      >
        {{ validationError }}
      </b-alert>

      <!-- Save Error -->
      <b-alert
        v-if="saveError"
        variant="danger"
        show
        class="mt-3 p-1"
        @dismissed="saveError = ''"
      >
        {{ saveError }}
      </b-alert>
      </div>
    </b-overlay>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="outline-secondary"
        :disabled="isSaving || deletingColumnIndex !== null"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="columns.length === 0 || isSaving || deletingColumnIndex !== null"
        @click="ok()"
      >
        <b-spinner
          v-if="isSaving"
          small
          class="mr-1"
        />
        Save
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BModal,
  BButton,
  BAlert,
  BSpinner,
  BOverlay,
  VBTooltip,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

export default {
  name: 'PartyColumnsDialog',

  directives: {
    'b-tooltip': VBTooltip,
  },

  components: {
    BModal,
    BButton,
    BAlert,
    BSpinner,
    BOverlay,
    vSelect,
  },

  props: {
    visible: {
      type: Boolean,
      required: true,
    },
    partyName: {
      type: String,
      default: '',
    },
    currentColumns: {
      type: Array,
      required: true,
      default: () => [],
    },
    availableKeyItems: {
      type: Array,
      required: true,
      default: () => [],
    },
  },

  data() {
    return {
      columns: [],
      validationError: '',
      deletingColumnIndex: null, // Track which column is being deleted
      isSaving: false, // Track if save operation is in progress
      saveError: '', // Error message from save operation
    }
  },

  computed: {
    filteredAvailableColumns() {
      // Filter availableKeyItems based on party/table name
      // Only show keys where:
      // 1. type === 'addressBlockPartial'
      // 2. keyValue starts with partyName (case-insensitive)
      // 3. Not already selected in the columns list
      if (!this.availableKeyItems || !this.partyName) {
        return []
      }

      const partyNameLower = this.partyName.toLowerCase()

      // Get all currently selected column keys
      const selectedKeys = this.columns
        .map(col => col.selectedKey)
        .filter(key => key) // Remove null/undefined values
        .map(key => key.toLowerCase())

      // Return filtered items with proper structure for v-select
      // v-select expects: { keyValue: '...', label: '...' }
      return this.availableKeyItems
        .filter(item => {
          if (!item || !item.keyValue) return false

          const keyValueLower = item.keyValue.toLowerCase()
          return (
            item.type === 'addressBlockPartial'
            && keyValueLower.startsWith(partyNameLower)
            && !selectedKeys.includes(keyValueLower) // Exclude already selected columns
          )
        })
        .map(item => ({
          keyValue: item.keyValue,
          label: item.label || item.keyValue,
        }))
    },
  },

  watch: {
    visible(newVal) {
      if (newVal) {
        this.initializeColumns()
      }
    },
  },

  methods: {
    initializeColumns() {
      // Initialize columns from currentColumns
      if (this.currentColumns && this.currentColumns.length > 0) {
        this.columns = this.currentColumns.map((col, index) => ({
          selectedKey: col.key,
          isFirstColumn: index === 0, // First column is locked (same as party name)
          isFixed: col.isFixed || false, // Preserve isFixed property from backend
          isdeletable: col.isdeletable || false, // Preserve isdeletable property from backend
          customSearch: col.customSearch !== undefined ? col.customSearch : true, // Default to true (searchable) if not specified
        }))
      } else {
        // If no columns, add the first column (party name)
        this.columns = [
          {
            selectedKey: this.partyName,
            isFirstColumn: true,
            isFixed: true,
            isdeletable: false,
            customSearch: true, // Enable search for first column
          },
        ]
      }
      this.validationError = ''
    },

    addNewColumn() {
      // Add a new empty column
      this.columns.push({
        selectedKey: null,
        isFirstColumn: false,
        isFixed: false,
        isdeletable: false,
        customSearch: true, // Enable search for new columns by default
      })
    },

    async removeColumn(index) {
      // Don't allow removing the first column
      if (index === 0) {
        this.validationError = 'Cannot delete the first column (it matches the party name)'
        return
      }

      // Prevent multiple deletions at once
      if (this.deletingColumnIndex !== null) {
        return
      }

      const columnToDelete = this.columns[index]

      // Check if this column exists in the current columns (already saved to backend)
      const existsInBackend = this.currentColumns.some(col => col.key === columnToDelete.selectedKey)

      if (existsInBackend && columnToDelete.selectedKey) {
        // Set loading state
        this.deletingColumnIndex = index
        this.validationError = ''

        // Call API to delete the column from backend
        try {
          await this.$store.dispatch('profile/deletePartyColumn', {
            tableName: this.partyName,
            columnKey: columnToDelete.selectedKey,
          })

          // Show success toast
          this.$bvToast.toast('Column deleted successfully', {
            title: 'Success',
            variant: 'success',
            solid: true,
            autoHideDelay: 3000,
          })
        } catch (error) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete column from backend'
          this.validationError = errorMessage
          this.deletingColumnIndex = null

          // Show error toast
          this.$bvToast.toast(
            errorMessage,
            {
              title: 'Error',
              variant: 'danger',
              solid: true,
              autoHideDelay: 5000,
            },
          )
          return
        } finally {
          this.deletingColumnIndex = null
        }
      }

      // Remove from local columns array
      this.columns.splice(index, 1)
    },

    handleSave(bvModalEvent) {
      // Prevent modal from closing immediately
      if (bvModalEvent) {
        bvModalEvent.preventDefault()
      }

      // Set loading state
      this.isSaving = true
      this.validationError = ''

      const partyNameLower = this.partyName.toLowerCase()

      // Convert columns to the format expected by parent
      // All columns have ismandatory: false by default
      // Filter out blank columns (columns without a name/selectedKey)
      const columnsData = this.columns
        .filter(col => col.selectedKey && col.selectedKey.trim() !== '') // Auto-remove blank columns
        .map(col => {
          let columnKey = col.selectedKey

          // Ensure column key has the table name prefix in lowercase
          if (columnKey && !columnKey.toLowerCase().startsWith(partyNameLower)) {
            columnKey = partyNameLower + columnKey
          }

          // Convert the final key to lowercase
          columnKey = columnKey.toLowerCase()

          return {
            key: columnKey,
            label: columnKey,
            sortable: true,
            ismandatory: false, // Always false for parties
            isFixed: col.isFixed || false, // Include isFixed property
            isdeletable: col.isdeletable || false, // Include isdeletable property
            customSearch: col.customSearch !== undefined ? col.customSearch : true, // Default to true (searchable)
          }
        })

      this.$emit('save', columnsData)
    },

    // Called by parent when save succeeds
    onSaveSuccess() {
      this.isSaving = false
      this.saveError = ''
      this.$emit('close')
    },

    // Called by parent when save fails
    onSaveError(errorMessage) {
      this.isSaving = false
      this.saveError = errorMessage
    },

    handleClose() {
      this.validationError = ''
      this.saveError = ''
      this.deletingColumnIndex = null
      this.isSaving = false
      this.$emit('close')
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';

// Only limit modal height to 90vh - scrollable prop handles the rest
::v-deep .party-columns-modal {
  .modal-dialog {
    max-height: 90vh;
  }

  .modal-body {
    max-height: calc(90vh - 160px); // Subtract header and footer height
  }
}
</style>
