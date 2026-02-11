<template>
  <b-modal
    :visible="visible"
    title="Manage Columns"
    size="lg"
    scrollable
    centered
    modal-class="party-columns-modal"
    ok-title="Save"
    cancel-title="Cancel"
    :no-close-on-backdrop="deletingColumnIndex !== null || saving"
    :no-close-on-esc="deletingColumnIndex !== null || saving"
    @ok="handleSave"
    @hidden="handleClose"
  >
    <b-overlay
      :show="deletingColumnIndex !== null"
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
            Deleting column...
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
              :options="availableKeyItems"
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

          <!-- Is Required Checkbox -->
          <div class="mr-2">
            <b-form-checkbox
              v-model="column.ismandatory"
              class="mt-1"
            >
              Mandatory
            </b-form-checkbox>
          </div>

          <!-- Character Length Input -->
          <div class="mr-2" style="width: 100px;">
            <small class="text-muted" style="font-size: 0.75rem;">Character Length</small>
            <b-form-input
              v-model.number="column.characterLimit"
              type="number"
              size="sm"
              placeholder="Character Length"
              min="1"
            />
          </div>

          <!-- Delete Button -->
          <div class="mt-1">
            <b-button
              v-if="!column.isFirstColumn"
              variant="outline-danger"
              size="sm"
              :disabled="deletingColumnIndex === index"
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
              title="First column cannot be deleted"
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
          :disabled="deletingColumnIndex !== null"
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
      <!-- {{ currentColumns }} -->

      <!-- Validation Error -->
      <b-alert
        v-if="validationError"
        variant="danger"
        show
        class="mt-3"
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
        :disabled="deletingColumnIndex !== null || saving"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="columns.length === 0 || deletingColumnIndex !== null || saving"
        @click="ok()"
      >
        <b-spinner
          v-if="saving"
          small
          class="mr-1"
        />
        {{ saving ? 'Saving...' : 'Save' }}
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BModal,
  // BFormGroup,
  BButton,
  BFormCheckbox,
  BFormInput,
  BAlert,
  BSpinner,
  BOverlay,
  VBTooltip,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

export default {
  name: 'DictionaryColumnsDialog',

  directives: {
    'b-tooltip': VBTooltip,
  },

  components: {
    BModal,
    // BFormGroup,
    BButton,
    BFormCheckbox,
    BFormInput,
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
    dictionaryName: {
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
      saving: false, // Track save operation
      saveError: '', // Error message from save operation
    }
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
          ismandatory: col.ismandatory || false,
          characterLimit: col.characterLimit ?? null,
          isFirstColumn: index === 0, // First column is locked (same as dictionary name)
        }))
      } else {
        // If no columns, add the first column (dictionary name)
        this.columns = [
          {
            selectedKey: this.dictionaryName,
            ismandatory: false,
            characterLimit: null,
            isFirstColumn: true,
          },
        ]
      }
      this.validationError = ''
    },

    addNewColumn() {
      // Add a new empty column
      this.columns.push({
        selectedKey: null,
        ismandatory: false,
        characterLimit: null,
        isFirstColumn: false,
      })
    },

    async removeColumn(index) {
      // Don't allow removing the first column
      if (index === 0) {
        this.validationError = 'Cannot delete the first column (it matches the dictionary name)'
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
          await this.$store.dispatch('profile/deleteDictionaryColumn', {
            tableName: this.dictionaryName,
            columnKey: columnToDelete.selectedKey,
          })

          // Show success toast
          this.$bvToast.toast('Column deleted successfully', {
            title: 'Success',
            variant: 'success',
            solid: true,
            autoHideDelay: 3000,
          })

          // Refresh dictionaries to get updated data
          // await this.$store.dispatch('profile/fetchAllDictionaries')
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

    // validateColumns() {
    //   // Check if all columns have a selected key
    //   const hasEmptyColumn = this.columns.some(col => !col.selectedKey)
    //   if (hasEmptyColumn) {
    //     this.validationError = 'Please select a name for all columns or remove empty columns'
    //     return false
    //   }

    //   // Check for duplicate columns
    //   const keys = this.columns.map(col => col.selectedKey)
    //   const duplicates = keys.filter((key, index) => keys.indexOf(key) !== index)
    //   if (duplicates.length > 0) {
    //     this.validationError = `Duplicate column detected: ${duplicates[0]}`
    //     return false
    //   }

    //   this.validationError = ''
    //   return true
    // },

    handleSave(bvModalEvt) {
      // Prevent modal from closing - we'll close it manually on success
      if (bvModalEvt) {
        bvModalEvt.preventDefault()
      }

      // if (!this.validateColumns()) {
      //   return
      // }

      // Clear any previous save error
      this.saveError = ''
      this.saving = true

      // Convert columns to the format expected by parent
      const columnsData = this.columns.map(col => ({
        key: col.selectedKey,
        label: col.selectedKey,
        sortable: true,
        ismandatory: col.ismandatory,
        characterLimit: col.characterLimit ?? null,
      }))

      this.$emit('save', columnsData)
    },

    // Called by parent when save succeeds
    onSaveSuccess() {
      this.saving = false
      this.saveError = ''
      this.$emit('close')
    },

    // Called by parent when save fails
    onSaveError(errorMessage) {
      this.saving = false
      this.saveError = errorMessage
    },

    handleClose() {
      this.validationError = ''
      this.saveError = ''
      this.saving = false
      this.deletingColumnIndex = null
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
