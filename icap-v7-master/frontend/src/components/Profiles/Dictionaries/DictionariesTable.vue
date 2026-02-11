<template>
  <div class="mb-4">
    <div class="mb-4 d-flex justify-content-end">
      <b-button
        variant="outline-primary"
        size="md"
        class="mr-1"
        @click="openCreateDictionaryDialog"
      >
        Create New Dictionary
      </b-button>
      <ImportAllDictionaries
        @import-success="handleImportAllSuccess"
      />
      <ExportAllDictionaries />
      <!-- <b-button
        variant="success"
        size="md"
        class="mr-1"
        @click="handleSaveDictionaries"
      >
        Save
      </b-button> -->
    </div>

    <!-- Loading state for initial load -->
    <div
      v-if="loading"
      class="text-center my-5"
    >
      <b-spinner class="mr-2" />
      <span>Loading dictionaries...</span>
    </div>
    <!-- <pre>
      {{ dictionaries }}
    </pre> -->

    <!-- Dictionary Tables -->
    <div
      v-for="(dictionary, tableIndex) in dictionaries"
      :key="dictionary.name"
      class="my-6 mt-4"
    >
      <!-- Table Header with Title and Actions -->
      <div class="d-flex justify-content-between align-items-center mb-1 mt-6">
        <h4 class="mb-0">
          {{ dictionary.name }}
        </h4>
        <div class="d-flex">
          <!-- <b-button
            v-if="tableStates[dictionary.name] && tableStates[dictionary.name].selectedRecords && tableStates[dictionary.name].selectedRecords.length > 0"
            variant="outline-danger"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(dictionary.name)"
            @click="openBulkDeleteDialog(dictionary.name)"
          >
            Delete Selected
          </b-button> -->
          <b-button
            variant="outline-primary"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(dictionary.name)"
            @click="openRecordDialog(dictionary.name, 'add')"
          >
            Add New
          </b-button>
          <b-button
            variant="outline-primary"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(dictionary.name)"
            @click="openDescriptionDialog(dictionary.name)"
          >
            Description
          </b-button>
          <b-button
            variant="outline-primary"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(dictionary.name)"
            @click="openImportDialog(dictionary.name)"
          >
            Import
          </b-button>
          <import-dictionary
            v-if="showImportDialog[dictionary.name]"
            v-model="showImportDialog[dictionary.name]"
            :table-name="dictionary.name"
            @import-success="handleImportSuccess()"
          />
          <!-- <b-button
            variant="outline-success"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(dictionary.name)"
          >
            Export
          </b-button> -->
          <ExportDictionary
            :table-name="dictionary.name"
          />
          <b-button
            variant="outline-secondary"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(dictionary.name)"
            @click="openColumnsDialog(dictionary.name)"
          >
            Columns
          </b-button>
          <div
            v-if="tableStates[dictionary.name]"
            class="mx-2"
          >
            <label>Show</label>
            <v-select
              v-model="tableStates[dictionary.name].perPage"
              :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
              :options="tableStates[dictionary.name].perPageOptions"
              :clearable="false"
              class="per-page-selector d-inline-block mx-50"
              @input="handlePerPageChange(dictionary.name, $event)"
            />
            <label>entries</label>
          </div>
          <feather-icon
            v-b-tooltip.hover
            icon="TrashIcon"
            class="cursor-pointer mt-delete-icon text-danger"
            size="22"
            title="Delete Dictionary"
            @click.stop="openDeleteDictionaryDialog(dictionary.name)"
          />
        </div>
      </div>
      <!-- <pre>
        {{ dictionaries }}
      </pre> -->

      <!-- Table Content -->
      <b-table-simple
        :busy="isTableLoading(dictionary.name)"
        responsive
        striped
        class="mb-4 mt-6"
      >
        <b-thead>
          <b-tr>
            <b-th>
              <b-form-checkbox
                :checked="isAllSelected(dictionary.name)"
                @change="toggleSelectAll(dictionary.name, $event)"
              />
            </b-th>
            <b-th
              v-for="column in getVisibleColumns(dictionary.name)"
              :key="column.key"
              :class="{
                'cursor-pointer' : column.sortable,
                '' : !column.sortable,
                'text-danger' : column.ismandatory,
                'text-success' : !column.ismandatory,
              }"
              @click="column.sortable && customSort(dictionary.name, column.key)"
            >
              {{ column.label }}
              <feather-icon
                v-if="column.sortable && tableStates[dictionary.name].sortBy === column.key"
                :icon="tableStates[dictionary.name].sortDesc ? 'ChevronDownIcon' : 'ChevronUpIcon'"
                size="14"
              />
            </b-th>
            <b-th>Actions</b-th>
          </b-tr>
          <b-tr>
            <b-th />
            <b-th
              v-for="column in getVisibleColumns(dictionary.name)"
              :key="column.key"
            >
              <b-form-input
                v-if="column.key !== 'action'"
                :value="getSearchValue(dictionary.name, column.key)"
                :disabled="isTableLoading(dictionary.name)"
                placeholder="Search..."
                size="sm"
                @input="updateSearchValue(dictionary.name, column.key, $event)"
              />
            </b-th>
            <b-th />
          </b-tr>
        </b-thead>

        <b-tbody v-if="!isTableLoading(dictionary.name)">
          <b-tr
            v-for="(record, recordIndex) in getCurrentTableData(dictionary.name)"
            :key="record.id || recordIndex"
          >
            <b-td>
              <b-form-checkbox
                :checked="isRecordSelected(dictionary.name, record.id || recordIndex)"
                @change="toggleRecordSelection(dictionary.name, record.id || recordIndex, $event)"
              />
            </b-td>
            <b-td
              v-for="column in getVisibleColumns(dictionary.name)"
              :key="column.key"
            >
              {{ record[column.key] || '-' }}
            </b-td>
            <b-td class="text-nowrap">
              <feather-icon
                v-b-tooltip.hover
                icon="EditIcon"
                size="18"
                class="mr-1 cursor-pointer text-primary"
                title="Edit Record"
                @click.stop="openRecordDialog(dictionary.name, 'edit', record)"
              />
              <feather-icon
                v-b-tooltip.hover
                icon="TrashIcon"
                class="cursor-pointer text-danger"
                size="18"
                title="Delete Record"
                @click.stop="openDeleteDialog(dictionary.name, record)"
              />
            </b-td>
          </b-tr>
        </b-tbody>

        <b-tbody v-else>
          <b-tr>
            <b-td
              :colspan="dictionary.columns.length + 2"
              class="text-start py-2"
            >
              <b-spinner class="ml-8" />
            </b-td>
          </b-tr>
        </b-tbody>

        <b-tbody v-if="!isTableLoading(dictionary.name) && getCurrentTableData(dictionary.name).length === 0">
          <b-tr>
            <b-td
              :colspan="dictionary.columns.length + 2"
              class="text-center text-muted"
            >
              No records found for {{ dictionary.name }}
            </b-td>
          </b-tr>
        </b-tbody>
      </b-table-simple>

      <!-- Pagination -->
      <div
        v-if="!isTableLoading(dictionary.name) && getCurrentTableData(dictionary.name).length > 0"
        class="mx-2 mb-2"
      >
        <detailed-pagination
          :per-page="getTableState(dictionary.name).perPage"
          :current-page="getTableState(dictionary.name).currentPage"
          :total-records="getTotalRecords(dictionary.name)"
          :local-records="getCurrentTableData(dictionary.name).length"
          @page-changed="pageChanged(dictionary.name, $event)"
        />
      </div>

      <!-- Record Modal (Add/Edit) -->
      <b-modal
        :id="`record-modal-${dictionary.name}`"
        :title="modalMode === 'add' ? `Create Record - ${dictionary.name}` : `Edit Record - ${dictionary.name}`"
        :ok-title="modalMode === 'add' ? 'Add' : 'Update'"
        :ok-disabled="isFormEmpty"
        size="md"
        scrollable
        centered
        cancel-title="Cancel"
        @ok="handleRecordSubmit(dictionary.name, $event)"
        @hidden="resetRecordForm"
      >
        <validation-observer :ref="`formObserver_${dictionary.name}`">
          <b-form>
            <b-form-group
              v-for="column in dictionary.columns"
              :key="column.key"
            >
              <validation-provider
                #default="{ errors }"
                :name="column.label"
                :rules="getValidationRules(column)"
                mode="eager"
              >
              <b-form-group
                :label-for="`field-${column.key}`"
              >
                <template #label>
                  {{ column.label }}
                  <span
                    v-if="column.ismandatory && !column.key.toLowerCase().includes('addressshortcode')"
                    class="text-danger"
                  >*</span>
                </template>
                <b-form-input
                  v-model="formData[column.key]"
                  :disabled="isTableLoading(dictionary.name)"
                  :state="errors.length > 0 ? false : null"
                />
                <!-- Character count and error message -->
                <div
                  v-if="column.characterLimit"
                  class="d-flex justify-content-between align-items-start mt-1"
                >
                  <small class="text-danger">{{ errors[0] }}</small>
                  <small
                    :class="{
                      'text-danger font-weight-bold': getCharacterCount(column.key) > column.characterLimit,
                      'text-muted': getCharacterCount(column.key) <= column.characterLimit
                    }"
                  >
                    {{ getCharacterCount(column.key) }} / {{ column.characterLimit }}
                  </small>
                </div>
                <small
                  v-else
                  class="text-danger"
                >{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-form-group>
          </b-form>
        </validation-observer>

      </b-modal>

      <!-- Delete Confirmation Modal -->
      <DeleteModal
        :id="`delete-modal-${dictionary.name}`"
        :dictionary-to-delete="dictionaryToDelete"
        title="Confirm Delete Dictionary"
        @delete="handleDeleteSubmit(dictionary.name)"
      />

      <!-- Description Modal -->
      <b-modal
        :id="`description-modal-${dictionary.name}`"
        v-model="showDescriptionDialog[dictionary.name]"
        title="Description"
        size="md"
        centered
        cancel-title="Cancel"
        ok-title="Add"
        @ok="handleDescriptionUpdate(dictionary.name)"
        @hidden="resetDescriptionForm"
      >
        <b-form-group label="Description">
          <b-form-textarea
            v-model="descriptionFormData"
            rows="5"
            placeholder="Enter description..."
          />
        </b-form-group>
      </b-modal>

      <!-- Bulk Delete Modal -->
      <!-- <BulkDeleteModal
        :id="`bulk-delete-modal-${dictionary.name}`"
        title="Confirm Bulk Delete"
        ok-title="Delete"
        ok-variant="danger"
        @delete="handleBulkDeleteSubmit(dictionary.name)"
      /> -->

      <!-- Divider between tables -->
      <hr
        v-if="tableIndex < dictionaries.length - 1"
        class="mb-6"
      >
    </div>

    <!-- Create Dictionary Dialog -->
    <create-new-dictionary
      :visible="showCreateDictionaryDialog"
      :lists="availableDictionaries"
      @close="showCreateDictionaryDialog = false"
      @create="handleCreateDictionaryFromModal"
    />

    <!-- Delete Dictionary Dialog -->
    <b-modal
      v-model="showDeleteDictionaryDialog"
      title="Confirm Delete Dictionary"
      ok-title="Delete"
      ok-variant="danger"
      cancel-title="Cancel"
      centered
      @ok="handleDeleteDictionary"
    >
      <p>Are you sure you want to delete the dictionary "{{ dictionaryToDelete }}"?</p>
      <p class="text-danger">
        This will permanently delete all records in this dictionary.
      </p>
    </b-modal>

    <!-- Columns Dialog -->
    <dictionary-columns-dialog
      ref="columnsDialog"
      :visible="showColumnsDialog"
      :dictionary-name="currentColumnsDialogTable"
      :current-columns="currentDictionaryColumns"
      :available-key-items="availableDictionaries"
      @save="handleSaveColumns"
      @close="closeColumnsDialog"
    />
  </div>
</template>

<script>
import {
  BFormInput,
  BFormCheckbox,
  BFormTextarea,
  BSpinner,
  BTableSimple,
  BTbody,
  BTd,
  BTh,
  BThead,
  BTr,
  BButton,
  VBTooltip,
  BModal,
  BForm,
  BFormGroup,
} from 'bootstrap-vue'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import vSelect from 'vue-select'
// import { v4 as uuidv4 } from 'uuid'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'
import CreateNewDictionary from './CreateNewDictionary.vue'
import DictionaryColumnsDialog from './DictionaryColumnsDialog.vue'
// import BulkDeleteModal from './BulkDeleteModal.vue'
import DeleteModal from './DeleteModal.vue'
import ExportDictionary from './ExportDictionary.vue'
import ExportAllDictionaries from './ExportAllDictionaries.vue'
import ImportDictionary from './ImportDictionary.vue'
import ImportAllDictionaries from './ImportAllDictionaries.vue'
// eslint-disable-next-line no-unused-vars

export default {
  name: 'DictionariesTable',

  directives: {
    'b-tooltip': VBTooltip,
  },

  components: {
    BSpinner,
    BFormCheckbox,
    BFormTextarea,
    DetailedPagination,
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTbody,
    BFormInput,
    BTd,
    BButton,
    BModal,
    BForm,
    BFormGroup,
    vSelect,
    CreateNewDictionary,
    DictionaryColumnsDialog,
    // BulkDeleteModal,
    DeleteModal,
    ExportDictionary,
    ExportAllDictionaries,
    ImportDictionary,
    ImportAllDictionaries,
    ValidationProvider,
    ValidationObserver,
  },

  data() {
    return {
      loading: true,
      dictionariesLoaded: false,
      tableStates: {},
      // Track visible columns for each dictionary
      visibleColumns: {},
      formData: {},
      currentRecord: null,
      currentDeleteRecord: null,
      currentTableName: null,
      modalMode: 'add',
      showCreateDictionaryDialog: false,
      showDeleteDictionaryDialog: false,
      showColumnsDialog: false,
      currentColumnsDialogTable: null,
      dictionaryToDelete: '',
      newDictionaryName: '',
      showImportDialog: {},
      showDescriptionDialog: {},
      descriptionFormData: '',
      currentDescriptionTableName: null,
    }
  },

  computed: {
    // Get dictionaries from store
    dictionaries() {
      return this.$store.getters['profile/dictionaries'] || []
    },

    availableDictionaries() {
      return this.$store.state.profile.keys
    },

    isFormEmpty() {
      if (!this.formData) return true
      const filledFieldsCount = Object.values(this.formData).filter(value => {
        if (value === '' || value === null || value === undefined) return false
        if (typeof value === 'string' && value.trim() === '') return false
        return true
      }).length
      return filledFieldsCount < 1
    },

    currentDictionaryColumns() {
      if (!this.currentColumnsDialogTable) return []
      const dictionary = this.getDictionary(this.currentColumnsDialogTable)
      return dictionary ? dictionary.columns : []
    },
  },

  watch: {
    // Initialize table states when dictionaries are loaded from API
    dictionaries: {
      handler(newDictionaries) {
        if (newDictionaries && newDictionaries.length > 0) {
          newDictionaries.forEach(dictionary => {
            // Only initialize if not already initialized
            if (!this.tableStates[dictionary.name] && dictionary.columns) {
              this.initializeDictionaryState(dictionary.name, dictionary.columns)
            }
          })
        }
      },
      immediate: true,
    },
    // Watch for process name and load dictionaries when available
    '$store.state.profile.selecedProcessName': {
      async handler(newProcessName) {
        // Only load if we haven't loaded yet and process name is now available
        if (newProcessName && !this.dictionariesLoaded) {
          await this.loadDictionaries()
        }
      },
      immediate: true,
    },
  },

  mounted() {},

  methods: {
    // Load dictionaries from API
    async loadDictionaries() {
      if (this.dictionariesLoaded) return

      try {
        // First ensure the process exists
        await this.$store.dispatch('profile/ensureDictionariesProcessExists').catch(error => {
          this.showToast(error.response?.data?.detail || error.message || 'Failed to initialize dictionaries process', 'danger', 'AlertTriangleIcon')
          throw error
        })

        // Then fetch all dictionaries for this process
        await this.$store.dispatch('profile/fetchAllDictionaries').catch(error => {
          this.showToast(error.response?.data?.detail || error.message || 'Failed to load dictionaries', 'danger', 'AlertTriangleIcon')
          throw error
        })

        // Initialize table states for loaded dictionaries
        this.initializeTableStates()

        // Mark as loaded
        this.dictionariesLoaded = true
      } catch (error) {
        // Error already shown via toast
      } finally {
        // Always set loading to false after API calls complete or fail
        this.loading = false
      }
    },

    // Initialize table states for all dictionaries in store
    initializeTableStates() {
      this.dictionaries.forEach(dictionary => {
        if (dictionary.columns) {
          this.initializeDictionaryState(dictionary.name, dictionary.columns)
        }
      })
    },

    // Helper: Initialize table state for a dictionary
    initializeDictionaryState(dictionaryName, columns) {
      // Initialize table state
      this.$set(this.tableStates, dictionaryName, {
        currentPage: 1,
        perPage: 5,
        perPageOptions: [5, 10, 25, 50, 100],
        totalRecords: 0,
        sortBy: '',
        sortDesc: false,
        searchBy: {},
        selectedRecords: [],
        selectAll: false,
        isLoading: false,
      })

      // Initialize search fields
      const searchObj = {}
      columns.forEach(col => {
        searchObj[col.key] = ''
      })
      this.tableStates[dictionaryName].searchBy = searchObj

      // Initialize visible columns (all columns visible by default)
      this.$set(this.visibleColumns, dictionaryName, columns.map(col => col.key))
    },

    // Helper method: Get dictionary by name
    getDictionary(dictionaryName) {
      return this.dictionaries.find(dict => dict.name === dictionaryName) || null
    },

    // Get default structure for creating new dictionary
    // Returns a dictionary with one column (same name as dictionary) and empty data
    getDictionaryData(dictionaryName) {
      return {
        columns: [
          {
            key: dictionaryName,
            label: dictionaryName,
            sortable: true,
            ismandatory: true,
          },
        ],
        data: [],
      }
    },

    // Adjust page number after deleting a record to avoid empty pages
    adjustPageAfterDelete(dictionaryName) {
      const dictionary = this.getDictionary(dictionaryName)
      const state = this.tableStates[dictionaryName]

      if (!dictionary || !state) return

      const totalRecords = dictionary.data ? dictionary.data.length : 0
      const totalPages = Math.ceil(totalRecords / state.perPage)

      // If current page is greater than total pages, go to last valid page
      if (state.currentPage > totalPages) {
        this.$set(this.tableStates[dictionaryName], 'currentPage', Math.max(1, totalPages))
      }
    },

    filterAndSortData(dictionaryName) {
      const state = this.tableStates[dictionaryName]
      if (!state) return []

      // Get dictionary data from unified structure
      const dictionary = this.getDictionary(dictionaryName)
      if (!dictionary) return []

      let data = [...(dictionary.data || [])]

      // Apply search filters
      Object.keys(state.searchBy).forEach(key => {
        const searchValue = state.searchBy[key]
        if (searchValue && searchValue.trim() !== '') {
          data = data.filter(item => {
            const value = item[key]
            return value && value.toString().toLowerCase().includes(searchValue.toLowerCase())
          })
        }
      })

      // Apply sorting
      if (state.sortBy) {
        data.sort((a, b) => {
          const aVal = a[state.sortBy] || ''
          const bVal = b[state.sortBy] || ''
          const comparison = aVal.toString().localeCompare(bVal.toString())
          return state.sortDesc ? -comparison : comparison
        })
      }

      return data
    },

    getCurrentTableData(dictionaryName) {
      const filtered = this.filterAndSortData(dictionaryName)
      const state = this.tableStates[dictionaryName]
      if (!state) return []

      const start = (state.currentPage - 1) * state.perPage
      const end = start + state.perPage
      return filtered.slice(start, end)
    },

    getTotalRecords(dictionaryName) {
      return this.filterAndSortData(dictionaryName).length
    },

    getTableState(dictionaryName) {
      return this.tableStates[dictionaryName] || {}
    },

    isTableLoading(dictionaryName) {
      return this.getTableState(dictionaryName).isLoading || false
    },

    getSearchValue(dictionaryName, key) {
      return this.tableStates[dictionaryName]?.searchBy[key] || ''
    },

    updateSearchValue(dictionaryName, key, value) {
      if (this.tableStates[dictionaryName]) {
        this.$set(this.tableStates[dictionaryName].searchBy, key, value)
      }
    },

    handlePerPageChange(dictionaryName, newPerPage) {
      if (this.tableStates[dictionaryName]) {
        this.$set(this.tableStates[dictionaryName], 'perPage', newPerPage)
        this.$set(this.tableStates[dictionaryName], 'currentPage', 1)
      }
    },

    customSort(dictionaryName, key) {
      const state = this.tableStates[dictionaryName]
      if (!state) return
      if (state.sortBy === key) {
        state.sortDesc = !state.sortDesc
      } else {
        state.sortBy = key
        state.sortDesc = false
      }
    },

    pageChanged(dictionaryName, page) {
      if (this.tableStates[dictionaryName]) {
        this.tableStates[dictionaryName].currentPage = page
      }
    },

    isAllSelected(dictionaryName) {
      const state = this.tableStates[dictionaryName]
      const data = this.getCurrentTableData(dictionaryName)
      return state?.selectAll && data.length > 0
    },

    isRecordSelected(dictionaryName, recordId) {
      const state = this.tableStates[dictionaryName]
      return state?.selectedRecords.includes(recordId) || false
    },

    toggleSelectAll(dictionaryName, isSelected) {
      if (this.tableStates[dictionaryName]) {
        this.tableStates[dictionaryName].selectAll = isSelected
        if (isSelected) {
          this.tableStates[dictionaryName].selectedRecords = this.getCurrentTableData(dictionaryName).map(
            record => record.id || 0,
          )
        } else {
          this.tableStates[dictionaryName].selectedRecords = []
        }
      }
    },

    toggleRecordSelection(dictionaryName, recordId, isSelected) {
      if (!this.tableStates[dictionaryName]) return
      const { selectedRecords } = this.tableStates[dictionaryName]
      if (isSelected) {
        if (!selectedRecords.includes(recordId)) {
          selectedRecords.push(recordId)
        }
      } else {
        const index = selectedRecords.indexOf(recordId)
        if (index > -1) {
          selectedRecords.splice(index, 1)
        }
        this.tableStates[dictionaryName].selectAll = false
      }
    },

    openRecordDialog(dictionaryName, mode, record = null) {
      this.currentTableName = dictionaryName
      this.modalMode = mode
      this.currentRecord = record
      this.formData = mode === 'edit' && record ? { ...record } : {}
      this.$bvModal.show(`record-modal-${dictionaryName}`)
    },

    openDeleteDialog(dictionaryName, record) {
      this.currentTableName = dictionaryName
      this.currentDeleteRecord = record
      this.$bvModal.show(`delete-modal-${dictionaryName}`)
    },

    // openBulkDeleteDialog(dictionaryName) {
    //   this.currentTableName = dictionaryName
    //   this.$bvModal.show(`bulk-delete-modal-${dictionaryName}`)
    // },

    openCreateDictionaryDialog() {
      this.newDictionaryName = ''
      this.showCreateDictionaryDialog = true
    },

    openDeleteDictionaryDialog(dictionaryName) {
      this.dictionaryToDelete = dictionaryName
      this.showDeleteDictionaryDialog = true
    },

    resetRecordForm() {
      this.formData = {}
      this.currentRecord = null
      this.currentTableName = null
      this.modalMode = 'add'
    },

    getValidationRules(column) {
      const rules = {}

      // Add required rule if column is mandatory
      if (column.ismandatory) {
        rules.required = true
      }

      // Add max length rule if character limit is specified
      if (column.characterLimit && column.characterLimit > 0) {
        rules.max = column.characterLimit
      }

      return rules
    },

    getCharacterCount(columnKey) {
      const value = this.formData[columnKey]
      return value ? value.length : 0
    },

    async handleRecordSubmit(dictionaryName, bvModalEvt) {
      // Prevent modal from closing
      if (bvModalEvt) {
        bvModalEvt.preventDefault()
      }

      // Check if form has data
      if (!this.formData || Object.keys(this.formData).length === 0) {
        this.showToast('Please fill in at least one field', 'danger', 'AlertTriangleIcon')
        return
      }

      // Get validation observer
      const refName = `formObserver_${dictionaryName}`
      let observer = this.$refs[refName]

      // Handle array refs
      if (Array.isArray(observer)) {
        [observer] = observer
      }

      // Validate form
      if (!observer || !observer.validate) {
        this.showToast('Validation not available', 'danger', 'AlertTriangleIcon')
        return
      }

      const isValid = await observer.validate()
      if (!isValid) return

      const dictionary = this.getDictionary(dictionaryName)
      if (!dictionary) return

      const isEdit = this.modalMode === 'edit'

      try {
        if (isEdit) {
          await this.$store.dispatch('profile/updateDictionaryRecord', {
            tableName: dictionaryName,
            recordId: this.currentRecord.id,
            record: this.formData,
          })
          this.showToast('Record updated successfully', 'success')
        } else {
          await this.$store.dispatch('profile/addDictionaryRecord', {
            tableName: dictionaryName,
            record: this.formData,
          })
          this.showToast('Record created successfully', 'success')
        }

        await this.$store.dispatch('profile/fetchAllDictionaries')
        this.$bvModal.hide(`record-modal-${dictionaryName}`)
        this.resetRecordForm()
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || `Failed to ${isEdit ? 'update' : 'create'} record`, 'danger', 'AlertTriangleIcon')
      }
    },

    async handleDeleteSubmit(dictionaryName) {
      try {
        // Call API to delete record
        await this.$store.dispatch('profile/deleteDictionaryRecord', {
          tableName: dictionaryName,
          rowId: this.currentDeleteRecord.id,
        })

        this.showToast('Record deleted successfully', 'success')

        // Refresh all dictionaries to get updated data with correct IDs from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        // Adjust page number if current page is now empty
        this.adjustPageAfterDelete(dictionaryName)

        this.$bvModal.hide(`delete-modal-${dictionaryName}`)
        this.currentDeleteRecord = null
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || 'Failed to delete record', 'danger', 'AlertTriangleIcon')
      }
    },

    // async handleBulkDeleteSubmit(dictionaryName) {
    //   const dictionaries = [...this.dictionaries]
    //   const dictIndex = dictionaries.findIndex(d => d.name === dictionaryName)
    //   if (dictIndex === -1) return

    //   try {
    //     // Call API to delete each selected record
    //     const deletePromises = this.tableStates[dictionaryName].selectedRecords.map(rowId => this.$store.dispatch('profile/deleteDictionaryRecord', {
    //       tableName: dictionaryName,
    //       rowId,
    //     }))

    //     await Promise.all(deletePromises)

    //     // Update local state
    //     dictionaries[dictIndex].data = dictionaries[dictIndex].data.filter(
    //       record => !this.tableStates[dictionaryName].selectedRecords.includes(record.id),
    //     )
    //     this.updateDictionariesInStore(dictionaries)

    //     this.tableStates[dictionaryName].selectedRecords = []
    //     this.tableStates[dictionaryName].selectAll = false
    //     this.showToast('Selected records deleted successfully', 'success')
    //     this.$bvModal.hide(`bulk-delete-modal-${dictionaryName}`)
    //   } catch (error) {
    //     this.showToast(error.message || 'Failed to delete records', 'danger', 'AlertTriangleIcon')
    //   }
    // },

    async handleCreateDictionaryFromModal(dictionaryData) {
      // Handle both old (string) and new (object) formats for backward compatibility
      const dictionaryName = typeof dictionaryData === 'string' ? dictionaryData : dictionaryData.name
      const description = typeof dictionaryData === 'string' ? `${dictionaryData} table` : dictionaryData.description

      if (!dictionaryName || dictionaryName.trim() === '') {
        this.showToast('Please select a valid dictionary', 'danger', 'AlertTriangleIcon')
        return
      }

      // Check if dictionary already exists
      // if (this.dictionaries.some(dict => dict.name === dictionaryName)) {
      //   this.showToast('Dictionary already exists', 'danger', 'AlertTriangleIcon')
      //   return
      // }

      try {
        // Get dictionary data (will use default structure for new dictionaries)
        // First column will have the same name as the dictionary
        const response = this.getDictionaryData(dictionaryName)

        // Call API to create table
        await this.$store.dispatch('profile/createDictionaryTable', {
          name: dictionaryName,
          description,
          columns: response.columns,
        })

        this.showToast(`Dictionary "${dictionaryName}" created successfully`, 'success')

        // Refresh all dictionaries to get updated data with correct IDs from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        // Initialize table state and visible columns for the new dictionary
        this.initializeDictionaryState(dictionaryName, response.columns)

        this.showCreateDictionaryDialog = false
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || 'Failed to create dictionary', 'danger', 'AlertTriangleIcon')
      }
    },

    handleCreateDictionary() {
      if (!this.newDictionaryName || this.newDictionaryName.trim() === '') {
        this.showToast('Please enter a dictionary name', 'danger', 'AlertTriangleIcon')
        return
      }

      // Use the new method
      this.handleCreateDictionaryFromModal(this.newDictionaryName)
      this.newDictionaryName = ''
    },

    async handleDeleteDictionary() {
      try {
        // Call API to delete dictionary table
        await this.$store.dispatch('profile/deleteDictionaryTable', {
          tableName: this.dictionaryToDelete,
        })

        this.showToast('Dictionary deleted successfully', 'success')

        // Refresh all dictionaries to get updated data from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        // Clean up state for the deleted dictionary
        // delete this.tableStates[this.dictionaryToDelete]
        // delete this.visibleColumns[this.dictionaryToDelete]

        this.showDeleteDictionaryDialog = false
        this.dictionaryToDelete = ''
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || 'Failed to delete dictionary', 'danger', 'AlertTriangleIcon')
      }
    },

    // Get visible columns for a dictionary
    getVisibleColumns(dictionaryName) {
      const dictionary = this.getDictionary(dictionaryName)
      if (!dictionary) return []

      const visibleKeys = this.visibleColumns[dictionaryName] || []
      return dictionary.columns.filter(col => visibleKeys.includes(col.key))
    },

    // Open columns dialog
    openColumnsDialog(dictionaryName) {
      this.currentColumnsDialogTable = dictionaryName
      this.showColumnsDialog = true
    },

    // Save column data (columns with ismandatory field)
    async handleSaveColumns(columnsData) {
      if (!this.currentColumnsDialogTable) return

      const dictionaryName = this.currentColumnsDialogTable

      try {
        // Note: Column deletions are handled immediately in DictionaryColumnsDialog.removeColumn()
        // Call API to update column schema
        await this.$store.dispatch('profile/updateDictionaryColumns', {
          tableName: dictionaryName,
          columns: columnsData,
        })

        this.showToast('Columns updated successfully', 'success')

        // Refresh all dictionaries to get updated data with correct IDs from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        // Update visible columns (all columns visible by default)
        this.$set(this.visibleColumns, dictionaryName, columnsData.map(col => col.key))

        // Update search fields for new columns
        const searchObj = {}
        columnsData.forEach(col => {
          searchObj[col.key] = this.tableStates[dictionaryName]?.searchBy[col.key] || ''
        })
        this.$set(this.tableStates[dictionaryName], 'searchBy', searchObj)

        // Notify dialog of success - this will close it
        if (this.$refs.columnsDialog) {
          this.$refs.columnsDialog.onSaveSuccess()
        }
        this.currentColumnsDialogTable = null
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || 'Error saving columns'
        // Show toast notification
        this.showToast(errorMessage, 'danger', 'AlertTriangleIcon')
        // Notify dialog of error - keep it open and show error inside
        if (this.$refs.columnsDialog) {
          this.$refs.columnsDialog.onSaveError(errorMessage)
        }
      }
    },

    // Close columns dialog
    closeColumnsDialog() {
      this.showColumnsDialog = false
      this.currentColumnsDialogTable = null
    },

    // Open import dialog
    openImportDialog(dictionaryName) {
      this.$set(this.showImportDialog, dictionaryName, true)
    },

    openDescriptionDialog(dictionaryName) {
      const dictionary = this.getDictionary(dictionaryName)
      this.currentDescriptionTableName = dictionaryName
      this.descriptionFormData = dictionary?.description || ''
      this.$set(this.showDescriptionDialog, dictionaryName, true)
    },

    async handleDescriptionUpdate(dictionaryName) {
      try {
        // Call API to update description
        await this.$store.dispatch('profile/updateDictionaryDescription', {
          tableName: dictionaryName,
          description: this.descriptionFormData,
        })

        this.showToast('Description updated successfully', 'success')

        // Refresh all dictionaries to get updated data from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        this.$set(this.showDescriptionDialog, dictionaryName, false)
        this.resetDescriptionForm()
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || 'Failed to update description', 'danger', 'AlertTriangleIcon')
      }
    },

    resetDescriptionForm() {
      this.descriptionFormData = ''
      this.currentDescriptionTableName = null
    },

    // Handle import success
    async handleImportSuccess() {
      try {
        // Refresh all dictionaries to get updated data from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        // Update local state (visibleColumns and searchBy) for all dictionaries
        this.refreshLocalStateAfterImport()

        this.showToast('Dictionary imported successfully', 'success')
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || 'Failed to refresh dictionary data', 'danger', 'AlertTriangleIcon')
      }
    },

    // Handle import all success
    async handleImportAllSuccess() {
      try {
        // Refresh all dictionaries to get updated data from API
        await this.$store.dispatch('profile/fetchAllDictionaries')

        // Update local state (visibleColumns and searchBy) for all dictionaries
        this.refreshLocalStateAfterImport()

        this.showToast('All dictionaries imported successfully', 'success')
      } catch (error) {
        this.showToast(error.response?.data?.detail || error.message || 'Failed to refresh dictionary data', 'danger', 'AlertTriangleIcon')
      }
    },

    // Refresh local state after import to reflect new columns
    refreshLocalStateAfterImport() {
      this.dictionaries.forEach(dictionary => {
        if (dictionary.columns && dictionary.columns.length > 0) {
          // Update visible columns to include all columns from the imported data
          this.$set(this.visibleColumns, dictionary.name, dictionary.columns.map(col => col.key))

          // Update search fields for the new columns
          if (this.tableStates[dictionary.name]) {
            const searchObj = {}
            dictionary.columns.forEach(col => {
              // Preserve existing search values if column already existed
              searchObj[col.key] = this.tableStates[dictionary.name].searchBy[col.key] || ''
            })
            this.$set(this.tableStates[dictionary.name], 'searchBy', searchObj)
          } else {
            // Initialize state if dictionary is new
            this.initializeDictionaryState(dictionary.name, dictionary.columns)
          }
        }
      })
    },

    showToast(title, variant = 'success', icon = 'CheckIcon') {
      this.$toast({
        component: ToastificationContent,
        props: { title, icon, variant },
      })
    },

    // Save dictionaries - emit event to parent (ProfileFormV7)
    handleSaveDictionaries() {
      this.$emit('save-dictionaries')
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';

.per-page-selector {
  width: 7rem;
}

.mt-delete-icon {
  margin-top: 6px;
}
</style>
