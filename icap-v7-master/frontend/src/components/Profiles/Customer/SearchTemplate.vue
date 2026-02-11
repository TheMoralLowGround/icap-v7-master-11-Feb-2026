<template>
  <div class="mb-4">
    <div class="mb-4 d-flex justify-content-end">
      <b-button
        variant="outline-primary"
        size="md"
        class="mr-1"
        @click="openCreatePartyDialog"
      >
        Create New Party
      </b-button>
      <import-all-parties
        @import-success="handleImportAllSuccess"
      />
      <export-all-parties />
    </div>
    <!-- Loading state for initial load -->
    <div
      v-if="loading && tableTemplate.length === 0"
      class="text-center my-5"
    >
      <b-spinner class="mr-2" />
      <span>Loading tables...</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!loading && tableTemplate.length === 0"
      class="text-center my-5"
    >
      <span>No table templates available.</span>
    </div>

    <!-- Tables -->
    <div
      v-for="(template, tableIndex) in tableTemplate"
      :key="template.name"
      class="my-6"
    >
      <!-- Table Header with Title and Actions -->
      <div class="d-flex justify-content-between align-items-center mb-1 mt-6">
        <h4 class="mb-0">
          {{ template.name }}
        </h4>
        <div class="d-flex">
          <!-- <b-button
            v-if="tableStates[template.name] && tableStates[template.name].selectedRecords && tableStates[template.name].selectedRecords.length > 0"
            variant="outline-danger"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(template.name)"
            @click="openBulkDeleteDialog(template.name)"
          >
            Delete Selected
          </b-button> -->
          <b-button
            variant="outline-primary"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(template.name)"
            @click="openRecordDialog(template.name, 'add')"
          >
            Add New
          </b-button>
          <b-button
            variant="outline-primary"
            size="md"
            class="mr-1"
            :disabled="isTableLoading(template.name)"
            @click="openImportDialog(template.name)"
          >
            Import
          </b-button>
          <export-to-excel
            :table-name="template.name"
            :disabled="isTableLoading(template.name)"
          />
          <import-parties
            v-if="importPartiesState[template.name]"
            :table-name="template.name"
            @modal-closed="closeImportDialog(template.name)"
            @uploaded="importExcel(template.name)"
          />
          <!-- COMMENTED OUT: Now using Manage Columns dialog instead -->
          <!-- <b-button
            variant="outline-secondary"
            size="md"
            class="ml-1"
            :disabled="isTableLoading(template.name)"
            @click="openColumnsDialog(template.name, template.columns)"
          >
            Columns
          </b-button> -->
          <b-button
            variant="outline-primary"
            size="md"
            class="ml-1"
            :disabled="isTableLoading(template.name)"
            @click="openManageColumnsDialog(template.name)"
          >
            Columns
          </b-button>
          <div class="mx-2">
            <label>Show</label>
            <v-select
              v-model="tableStates[template.name].perPage"
              :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
              :options="tableStates[template.name].perPageOptions"
              :clearable="false"
              class="per-page-selector d-inline-block mx-50"
              @input="handlePerPageChange(template.name, $event)"
            />
            <label>entries</label>
          </div>
          <feather-icon
            v-b-tooltip.hover
            icon="TrashIcon"
            class="cursor-pointer mt-delete-icon text-danger"
            size="22"
            title="Delete Party"
            @click.stop="openDeletePartyDialog(template.name)"
          />
        </div>

      </div>

      <!-- Table Content -->
      <b-table-simple
        :busy="isTableLoading(template.name)"
        responsive
        striped
        class="mb-4"
      >
        <b-thead>
          <b-tr>
            <b-th>
              <b-form-checkbox
                :checked="isAllSelected(template.name)"
                @change="toggleSelectAll(template.name, $event)"
              />
            </b-th>
            <b-th
              v-for="column in visibleColumns(template.columns)"
              :key="column.key"
              :class="column.sortable ? 'cursor-pointer' : ''"
              :aria-sort="column.sortable ? getSortState(template.name, column.key) : null"
              @click="column.sortable && customSort(template.name, column.key)"
            >
              {{ column.label }}
            </b-th>
          </b-tr>
          <b-tr v-if="hasSearchableColumns(template.columns)">
            <b-th />
            <b-th
              v-for="column in visibleColumns(template.columns)"
              :key="column.key"
            >
              <b-form-input
                v-if="column.key !== 'action'"
                :value="getSearchValue(template.name, column.key)"
                :disabled="isTableLoading(template.name)"
                placeholder="Search..."
                size="sm"
                @input="updateSearchValue(template.name, column.key, $event)"
                @keyup.enter="searchTable(template.name)"
              />
            </b-th>
          </b-tr>
        </b-thead>

        <b-tbody v-if="!isTableLoading(template.name)">
          <b-tr
            v-for="(record, recordIndex) in getCurrentTableData(template.name)"
            :key="record.id || recordIndex"
          >
            <b-td>
              <b-form-checkbox
                :checked="isRecordSelected(template.name, record.ID || record.id || recordIndex)"
                @change="toggleRecordSelection(template.name, record.ID || record.id || recordIndex, $event)"
              />
            </b-td>
            <b-td
              v-for="column in visibleColumns(template.columns)"
              :key="column.key"
              :class="column.key === 'action' ? 'text-nowrap' : ''"
            >
              <div
                v-if="column.key === 'action'"
                class="text-nowrap"
              >
                <feather-icon
                  v-b-tooltip.hover
                  icon="EditIcon"
                  size="18"
                  class="mr-1 cursor-pointer"
                  title="Edit Record"
                  @click.stop="openRecordDialog(template.name, 'edit', record)"
                />
                <feather-icon
                  v-b-tooltip.hover
                  icon="TrashIcon"
                  class="cursor-pointer"
                  size="18"
                  title="Delete Record"
                  @click.stop="openDeleteDialog(template.name, record)"
                />
              </div>
              <span v-else-if="column.type === 'DateTimeField' || isDateColumn(column.key)">
                {{ formatDate(record[column.key]) }}
              </span>
              <span v-else>
                {{ getColumnValue(record, column.key) }}
              </span>
            </b-td>
          </b-tr>
        </b-tbody>

        <b-tbody v-else>
          <b-tr>
            <b-td
              :colspan="template.columns.length + 1"
              class="text-start py-2"
            >
              <b-spinner
                class="ml-8"
              />
              <!-- Loading... -->
            </b-td>
          </b-tr>
        </b-tbody>

        <b-tbody v-if="!isTableLoading(template.name) && getCurrentTableData(template.name).length === 0">
          <b-tr>
            <b-td
              :colspan="template.columns.length + 1"
              class="text-center text-muted"
            >
              No records found for {{ template.name }}
            </b-td>
          </b-tr>
        </b-tbody>
      </b-table-simple>

      <!-- Pagination -->
      <div
        v-if="!isTableLoading(template.name) && getCurrentTableData(template.name).length > 0"
        class="mx-2 mb-2"
      >
        <detailed-pagination
          :per-page="getTableState(template.name).perPage"
          :current-page="getTableState(template.name).currentPage"
          :total-records="getTableState(template.name).totalRecords"
          :local-records="getCurrentTableData(template.name).length"
          @page-changed="pageChanged(template.name, $event)"
        />
      </div>
      <div v-if="template.name === 'CUSTOM_MASTER'">
        <LookupManager
          @refresh-table="handleLookupRefresh"
          @remove-lookup="handleLookupRefresh"
        />
      </div>
      <!-- Record Modal (Add/Edit) -->
      <b-modal
        :id="`record-modal-${template.name}`"
        :title="modalMode === 'add' ? `Create Record - ${template.name}` : `Edit Record - ${template.name}`"
        :ok-title="modalMode === 'add' ? 'Create' : 'Save'"
        :ok-disabled="isFormEmpty"
        size="md"
        scrollable
        cancel-title="Cancel"
        @ok="handleRecordSubmit(template.name, $event)"
        @hidden="resetRecordForm"
      >
        <validation-observer :ref="`formObserver_${template.name}`">
          <b-form>
            <validation-provider
              v-for="column in editableColumns(template.columns)"
              :key="column.key"
              #default="{ errors }"
              :name="column.label"
              :rules="column.isdeletable === false && !column.key.toLowerCase().includes('addressshortcode') ? 'required' : ''"
            >
              <b-form-group
                :label-for="`field-${column.key}`"
              >
                <template #label>
                  {{ column.label }}
                  <span
                    v-if="column.isdeletable === false && !column.key.toLowerCase().includes('addressshortcode')"
                    class="text-danger"
                  >*</span>
                </template>
                <b-form-input
                  :id="`field-${column.key}`"
                  v-model="formData[column.key]"
                  :disabled="isTableLoading(template.name)"
                  :state="errors.length > 0 ? false : null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-form>
        </validation-observer>
      </b-modal>

      <!-- Delete Confirmation Modal -->
      <b-modal
        :id="`delete-modal-${template.name}`"
        title="Confirm Delete"
        ok-title="Delete"
        ok-variant="danger"
        cancel-title="Cancel"
        centered
        @ok="handleDeleteSubmit(template.name)"
      >
        <p>Are you sure you want to delete this record?</p>
      </b-modal>
      <b-modal
        :id="`bulk-delete-modal-${template.name}`"
        title="Confirm Bulk Delete"
        ok-title="Delete"
        ok-variant="danger"
        cancel-title="Cancel"
        centered
        @ok="handleBulkDeleteSubmit(template.name)"
      >
        <p>Are you sure you want to delete selected record(s)?</p>
      </b-modal>
      <!-- Divider between tables -->
      <hr
        v-if="tableIndex < tableTemplate.length - 1"
        class="mb-6"
      >
    </div>

    <!-- COMMENTED OUT: Now using Manage Columns dialog instead -->
    <!-- <add-parties-table-columns
      v-model="showColumnsDialog"
      :table-name="currentTableName"
      :column-options="currentTableColumns"
      :project-key-items="projectKeyItems"
      :selected-columns="getSelectedColumnsForTable(currentTableName)"
      @save="saveTableColumns"
      @modal-closed="showColumnsDialog = false"
    /> -->

    <!-- Create Party Dialog -->
    <create-new-party
      :visible="showCreatePartyDialog"
      :existing-parties="existingPartyNames"
      :lists="entities"
      @close="showCreatePartyDialog = false"
      @party-created="handlePartyCreated"
    />

    <!-- Delete Party Dialog -->
    <delete-new-party
      :visible="showDeletePartyDialog"
      :party-name="partyToDelete"
      @close="showDeletePartyDialog = false"
      @party-deleted="handlePartyDeleted"
    />

    <!-- Manage Columns Dialog -->
    <party-columns-dialog
      ref="partyColumnsDialog"
      :visible="showManageColumnsDialog"
      :party-name="currentManageColumnsTable"
      :current-columns="currentPartyColumns"
      :available-key-items="processKeyItems"
      @save="handleSaveColumns"
      @close="closeManageColumnsDialog"
    />
    <!-- <pre>
      {{ tableTemplate }}
    </pre> -->
  </div>
</template>

<script>
import {
  BFormInput,
  BFormCheckbox,
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
  // BRow,
  // BCol,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import vSelect from 'vue-select'
import bus from '@/bus'
import ImportParties from './ImportParties.vue'
import ExportToExcel from './ExportToExcel.vue'
import LookupManager from './CustomLookup/LookupManager.vue'
// COMMENTED OUT: Now using Manage Columns dialog instead
// import AddPartiesTableColumns from './AddPartiesTableColumns.vue'
import PartyColumnsDialog from './Parties/PartyColumnsDialog.vue'
import CreateNewParty from './Parties/CreateNewParty.vue'
import DeleteNewParty from './Parties/DeleteNewParty.vue'
import ImportAllParties from './Parties/ImportAllParties.vue'
import ExportAllParties from './Parties/ExportAllParties.vue'

export default {
  name: 'SearchTemplate',

  directives: {
    'b-tooltip': VBTooltip,
  },

  components: {
    BSpinner,
    BFormCheckbox,
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
    // BRow,
    // BCol,
    vSelect,
    ValidationProvider,
    ValidationObserver,
    ImportParties,
    ExportToExcel,
    LookupManager,
    // COMMENTED OUT: Now using Manage Columns dialog instead
    // AddPartiesTableColumns,
    PartyColumnsDialog,
    CreateNewParty,
    DeleteNewParty,
    ImportAllParties,
    ExportAllParties,
  },

  data() {
    return {
      loading: false,
      importPartiesState: {},
      error: null,
      tableTemplate: [],
      tableStates: {},
      tableData: {},
      formData: {},
      currentRecord: null,
      currentDeleteRecord: null,
      currentTableName: null,
      modalMode: 'add', // 'add' or 'edit'
      abortControllers: {},
      isComponentMounted: false,
      showColumnsDialog: false,
      showManageColumnsDialog: false,
      currentManageColumnsTable: null,
      showCreatePartyDialog: false,
      showDeletePartyDialog: false,
      partyToDelete: '',
      currentTableColumns: [],
      appliedLookupData: {}, // Store applied lookup data per table
    }
  },

  computed: {
    entities() {
      // Get all address block entities
      const allEntities = this.$store.state.profile.keys.filter(en => en.type === 'addressBlock')

      // Filter out entities that already have parties created
      return allEntities.filter(entity => !this.existingPartyNames.includes(entity.keyValue))
    },
    currentPartyColumns() {
      if (!this.currentManageColumnsTable) return []
      const party = this.tableTemplate.find(t => t.name === this.currentManageColumnsTable)
      return party ? party.columns.filter(col => col.key !== 'action') : []
    },
    // COMMENTED OUT: Using projectKeyItems filtering instead
    // availableEntities() {
    //   // Get all addressBlock entities for column selection
    //   return this.$store.state.profile.keys.filter(en => en.type === 'addressBlock')
    // },
    editableColumns() {
      const excludeKeys = ['action', 'id', 'process_name', 'PROCESS_NAME', 'ID']
      return columns => columns.filter(
        column => !excludeKeys.includes(column.key) && !this.isDateColumn(column.key),
      )
    },
    isFormEmpty() {
      if (!this.formData) return true

      // Count how many fields have valid values
      const filledFieldsCount = Object.values(this.formData).filter(value => {
        if (value === '' || value === null || value === undefined) return false
        if (typeof value === 'string' && value.trim() === '') return false
        return true
      }).length

      // Require at least 1 field to be filled
      return filledFieldsCount < 1
    },
    processUid() {
      return this.$store.getters['profile/processUid']
    },
    existingPartyNames() {
      // Extract table names from tableTemplate to pass to CreateNewParty
      return this.tableTemplate.map(table => table.name)
    },
    processKeyItems() {
      // Combine and deduplicate the key options
      return this.$store.state.profile.keys
    },
  },

  mounted() {
    this.isComponentMounted = true
  },

  beforeDestroy() {
    this.isComponentMounted = false
    Object.values(this.abortControllers).forEach(controller => controller.abort())
    this.abortControllers = {}
  },

  async created() {
    // Ensure parties process exists before fetching tables
    try {
      await this.$store.dispatch('profile/ensurePartiesProcessExists')
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error ensuring parties process exists:', error)
    }
    this.fetchTableNames()
  },
  methods: {
    visibleColumns(columns) {
    // Hide 'id', 'ID' but keep all others
      const hiddenKeys = ['id', 'ID']
      return columns.filter(col => !hiddenKeys.includes(col.key))
    },
    createAbortController(key) {
      if (this.abortControllers[key]) {
        this.abortControllers[key].abort()
      }

      const controller = new AbortController()
      this.abortControllers[key] = controller
      return controller
    },

    showToast(title, variant = 'success', icon = 'CheckIcon') {
      this.$toast({
        component: ToastificationContent,
        props: { title, icon, variant },
      })
    },

    async apiRequest(key, method, url, payload = null) {
      const controller = this.createAbortController(key)
      try {
        const response = await axios({
          method,
          url,
          data: payload,
          signal: controller.signal,
        })
        return response.data
      } catch (error) {
        if (error.name === 'CanceledError') return null
        throw error
      } finally {
        delete this.abortControllers[key]
      }
    },

    async handleDelete(tableName, ids) {
      if (!this.isComponentMounted) return
      try {
        // Use store action for deleting party records
        await this.$store.dispatch('profile/deletePartyRecords', {
          tableName,
          ids,
        })

        this.showToast(`${ids.length > 1 ? 'Records' : 'Record'} deleted successfully`)
        await this.fetchTableData(tableName, true)
        this.tableStates[tableName].selectedRecords = []
        this.tableStates[tableName].selectAll = false
      } catch (error) {
        this.showToast(
          error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to delete records',
          'danger',
          'AlertTriangleIcon',
        )
      } finally {
        this.currentTableName = null
        this.currentDeleteRecord = null
      }
    },

    openBulkDeleteDialog(tableName) {
      this.currentTableName = tableName
      this.$bvModal.show(`bulk-delete-modal-${tableName}`)
    },

    openCreatePartyDialog() {
      this.showCreatePartyDialog = true
    },

    handlePartyCreated() {
      // Refresh the table templates to include the new party
      this.fetchTableNames()
    },

    handleImportAllSuccess() {
      // Refresh all tables after importing all parties
      this.fetchTableNames()
    },

    openDeletePartyDialog(tableName) {
      this.partyToDelete = tableName
      this.showDeletePartyDialog = true
    },

    handlePartyDeleted() {
      // Refresh the table templates to remove the deleted party
      this.fetchTableNames()
      this.partyToDelete = ''
    },

    handleBulkDeleteSubmit(tableName) {
      this.handleDelete(tableName, this.tableStates[tableName].selectedRecords)
    },

    async handleDeleteSubmit(tableName) {
      this.handleDelete(tableName, [this.currentDeleteRecord?.ID || this.currentDeleteRecord?.id])
    },

    async fetchTableNames() {
      this.loading = true
      this.error = null
      try {
        // Fetch all party tables to get list of available table names
        const tablesData = await this.$store.dispatch('profile/fetchAllPartyTables')

        if (Array.isArray(tablesData)) {
          // Extract only table names - columns will come from formatted API
          this.tableTemplate = tablesData.map(table => ({
            name: table.table_name,
            columns: [], // Will be populated from formatted API per table
            description: table.description || null,
            rowCount: table.row_count || 0,
          }))

          this.initializeTableStates()
          // Load table data - columns will be extracted from each table's formatted response
          await this.loadTableData()
        } else {
          throw new Error('Invalid response structure from parties tables API')
        }
      } catch (error) {
        if (error.name === 'CanceledError') return
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to load tables'
        this.tableTemplate = []
        this.showToast(this.error, 'danger', 'AlertTriangleIcon')
      } finally {
        this.loading = false
      }
    },

    async loadTableData() {
      await this.tableTemplate.reduce(
        (promise, template) => promise.then(() => {
          if (!this.isComponentMounted) return Promise.resolve()
          return this.fetchTableData(template.name, false)
        }),
        Promise.resolve(),
      )
    },

    async fetchTableData(tableName, silent = false, lookupData = null) {
      if (!this.isComponentMounted) return
      const state = this.getTableState(tableName)
      if (!state) return

      const cleanedQueries = Object.fromEntries(
        Object.entries(state.searchBy || {}).filter(([, value]) => value !== '' && value != null),
      )

      if (!silent) state.isLoading = true
      const controller = this.createAbortController(tableName)

      try {
        // Build query parameters for pagination and sorting
        const queryParams = new URLSearchParams({
          page: String(state.currentPage),
          page_size: String(state.perPage),
          sort_desc: String(state.sortDesc),
        })

        // Add sort_by only if it exists
        if (state.sortBy) {
          queryParams.append('sort_by', String(state.sortBy))
        }

        // Add search queries as 'filters' query parameter (like curl command)
        if (Object.keys(cleanedQueries).length > 0) {
          queryParams.append('filters', JSON.stringify(cleanedQueries))
        }

        // Build request body for lookup data only
        const requestBody = {}

        // Add lookup data if provided
        if (lookupData && Object.keys(lookupData).length > 0) {
          requestBody.lookup_queries = lookupData
        }

        // Build endpoint with query parameters
        const endpoint = `parties/tables/${this.processUid}/${tableName}/formatted?${queryParams.toString()}`

        const response = await axios.post('/pipeline/qdrant_vector_db/', requestBody, {
          signal: controller.signal,
          params: {
            endpoint,
            request_type: 'GET',
          },
        })

        // Extract data from response
        this.$set(this.tableData, tableName, response.data.data || response.data.results || [])
        state.totalRecords = response.data.total_records
          || response.data.count
          || response.data.data?.length
          || 0

        // Extract and update columns from formatted response
        if (response.data.columns && Array.isArray(response.data.columns)) {
          const templateIndex = this.tableTemplate.findIndex(t => t.name === tableName)
          if (templateIndex !== -1) {
            // Add action column to the columns array
            const columnsWithAction = [
              ...response.data.columns,
              {
                key: 'action',
                label: 'Actions',
                sortable: false,
                customSearch: false,
              },
            ]

            // Update columns in template
            this.$set(this.tableTemplate[templateIndex], 'columns', columnsWithAction)

            // Preserve existing search values before updating searchBy
            const existingSearchValues = { ...(state.searchBy || {}) }

            // Build new searchBy object with all valid columns
            const newSearchObj = {}
            response.data.columns.forEach(col => {
              if (col.customSearch !== false && col.key !== 'action') {
                // Preserve existing value if it exists, otherwise initialize to empty string
                newSearchObj[col.key] = existingSearchValues[col.key] !== undefined
                  ? existingSearchValues[col.key]
                  : ''
              }
            })

            // Only update if we have valid columns
            if (Object.keys(newSearchObj).length > 0) {
              // Use Vue.set to update each key individually to maintain reactivity
              Object.keys(newSearchObj).forEach(key => {
                this.$set(state.searchBy, key, newSearchObj[key])
              })

              // Remove keys that no longer exist in the column list
              Object.keys(state.searchBy).forEach(key => {
                if (!(key in newSearchObj)) {
                  this.$delete(state.searchBy, key)
                }
              })
            }
          }
        }
      } catch (error) {
        if (error.name === 'CanceledError') return
        this.$set(this.tableData, tableName, [])
        state.totalRecords = 0
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message || `Failed to load data for ${tableName}`
        this.showToast(this.error, 'danger', 'AlertTriangleIcon')
      } finally {
        delete this.abortControllers[tableName]
        if (!silent) state.isLoading = false
      }
    },

    handleLookupRefresh(payload) {
      // Refresh the table with lookup data
      const { tableName, lookupData } = payload

      // Store or clear the applied lookup data
      if (lookupData && Object.keys(lookupData).length > 0) {
        this.$set(this.appliedLookupData, tableName, lookupData)
      } else {
        this.$set(this.appliedLookupData, tableName, null)
      }

      this.fetchTableData(tableName, false, lookupData)
    },

    initializeTableStates() {
      this.tableTemplate.forEach(template => {
        // Preserve existing search values if table state already exists
        const existingState = this.tableStates[template.name]
        const existingSearchBy = existingState?.searchBy || {}

        this.$set(this.tableStates, template.name, {
          currentPage: existingState?.currentPage || 1,
          perPage: existingState?.perPage || 5,
          perPageOptions: [5, 10, 25, 50, 100],
          totalRecords: existingState?.totalRecords || 0,
          sortBy: existingState?.sortBy || '',
          sortDesc: existingState?.sortDesc || false,
          searchBy: existingSearchBy, // Preserve existing search values
          selectedRecords: existingState?.selectedRecords || [],
          selectAll: existingState?.selectAll || false,
          isLoading: existingState?.isLoading || false,
        })

        this.$set(this.importPartiesState, template.name, false)

        // Initialize searchBy for new columns only (preserve existing values)
        const searchObj = { ...existingSearchBy }
        template.columns.forEach(col => {
          if (col.customSearch !== false && col.key !== 'action') {
            // Only initialize if key doesn't exist
            if (!(col.key in searchObj)) {
              searchObj[col.key] = ''
            }
          }
        })
        this.tableStates[template.name].searchBy = searchObj

        // Initialize table data if it doesn't exist
        if (!this.tableData[template.name]) {
          this.$set(this.tableData, template.name, [])
        }
      })
    },

    handlePerPageChange(tableName, newPerPage) {
      if (this.isComponentMounted && this.tableStates[tableName]) {
        this.$set(this.tableStates[tableName], 'perPage', newPerPage)
        this.$set(this.tableStates[tableName], 'currentPage', 1)
        // Preserve applied lookup data when changing per page
        const lookupData = this.appliedLookupData[tableName] || null
        this.fetchTableData(tableName, false, lookupData)
      }
    },

    getTableState(tableName) {
      return this.tableStates[tableName] || {}
    },

    isTableLoading(tableName) {
      return this.getTableState(tableName).isLoading || false
    },

    getCurrentTableData(tableName) {
      return this.tableData[tableName] || []
    },

    hasSearchableColumns(columns) {
      return columns.some(col => col.key !== 'action')
    },

    getColumnValue(record, key) {
      return record[key] || '-'
    },

    isDateColumn(key) {
      const dateKeys = ['created_at', 'updated_at', 'date_created', 'date_updated']
      return dateKeys.includes(key)
    },

    formatDate(dateString) {
      if (!dateString) return '-'
      try {
        const date = new Date(dateString)
        return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`
      } catch {
        return dateString
      }
    },

    getSearchValue(tableName, key) {
      return this.tableStates[tableName]?.searchBy[key] || ''
    },

    updateSearchValue(tableName, key, value) {
      if (this.tableStates[tableName]) {
        this.$set(this.tableStates[tableName].searchBy, key, value)
      }
    },

    async searchTable(tableName) {
      if (this.tableStates[tableName]) {
        this.tableStates[tableName].currentPage = 1
        // Preserve applied lookup data when searching
        const lookupData = this.appliedLookupData[tableName] || null
        await this.fetchTableData(tableName, false, lookupData)
      }
    },

    isAllSelected(tableName) {
      const state = this.tableStates[tableName]
      const data = this.getCurrentTableData(tableName)
      return state?.selectAll && data.length > 0
    },

    isRecordSelected(tableName, recordId) {
      const state = this.tableStates[tableName]
      return state?.selectedRecords.includes(recordId) || false
    },

    toggleSelectAll(tableName, isSelected) {
      if (this.tableStates[tableName]) {
        this.tableStates[tableName].selectAll = isSelected
        if (isSelected) {
          this.tableStates[tableName].selectedRecords = this.getCurrentTableData(tableName).map(
            record => record.ID || record.id || 0,
          )
        } else {
          this.tableStates[tableName].selectedRecords = []
        }
      }
    },

    toggleRecordSelection(tableName, recordId, isSelected) {
      if (!this.tableStates[tableName]) return
      const { selectedRecords } = this.tableStates[tableName]
      if (isSelected) {
        if (!selectedRecords.includes(recordId)) {
          selectedRecords.push(recordId)
        }
      } else {
        const index = selectedRecords.indexOf(recordId)
        if (index > -1) {
          selectedRecords.splice(index, 1)
        }
        this.tableStates[tableName].selectAll = false
      }
    },

    getSortState(tableName, key) {
      const state = this.tableStates[tableName]
      if (state?.sortBy === key) {
        return state.sortDesc ? 'descending' : 'ascending'
      }
      return 'none'
    },

    async customSort(tableName, key) {
      const state = this.tableStates[tableName]
      if (!state) return
      if (state.sortBy === key) {
        state.sortDesc = !state.sortDesc
      } else {
        state.sortBy = key
        state.sortDesc = false
      }
      // Preserve applied lookup data when sorting
      const lookupData = this.appliedLookupData[tableName] || null
      await this.fetchTableData(tableName, false, lookupData)
    },

    async pageChanged(tableName, page) {
      if (this.tableStates[tableName]) {
        this.tableStates[tableName].currentPage = page
        // Preserve applied lookup data when changing pages
        const lookupData = this.appliedLookupData[tableName] || null
        await this.fetchTableData(tableName, false, lookupData)
      }
    },

    openImportDialog(tableName) {
      this.$set(this.importPartiesState, tableName, true)
    },

    closeImportDialog(tableName) {
      this.$set(this.importPartiesState, tableName, false)
    },

    importExcel(tableName) {
      this.closeImportDialog(tableName)
      this.fetchTableData(tableName, true)
    },

    openColumnsDialog(tableName) {
      this.currentTableName = tableName
      // COMMENTED OUT: Using projectKeyItems filtering instead of dynamic columns
      // Get dynamic columns from store for this table
      // const dynamicColumns = this.$store.getters['profile/partiesDynamicColumn']
      // const tableColumns = dynamicColumns[tableName] || []

      // Convert column names to objects with key and label
      // this.currentTableColumns = tableColumns.map(col => ({
      //   key: col,
      //   label: col.charAt(0).toUpperCase() + col.slice(1).replace(/([A-Z])/g, ' $1').trim(),
      // }))

      this.showColumnsDialog = true
    },

    getSelectedColumnsForTable(tableName) {
      const partiesConfigTable = this.$store.state.profile.partiesConfigTable || []
      const table = partiesConfigTable.find(t => t.table === tableName)
      return table ? table.columns : []
    },

    async saveTableColumns({ tableName, columns }) {
      try {
        // Update Vuex store first
        this.$store.commit('profile/UPDATE_PARTIES_TABLE_COLUMNS', {
          tableName,
          columns,
        })

        // Get the profile ID from the route
        const profileId = this.$route.params.id

        // Only make API call if we're in edit mode (profile exists)
        if (profileId) {
          // Build the payload with latest data from store
          const state = this.$store.state.profile
          const payload = {
            ...state.generalInfo,
            manual_validation: state.manualValidation,
            multi_shipment: state.multiShipment,
            send_time_stamp: state.sendTimeStamp,
            automatic_splitting: state.automaticSplitting,
            ignore_dense_pages: state.ignoreDensePages,
            exceptional_excel: state.exceptionalExcel,
            email_domains: state.emailDomains,
            email_from: state.emailFrom,
            email_subject_match_option: state.emailSubjectMatchOption,
            email_subject_match_text: state.emailSubjectMatchText,
            customers: state.customers,
            documents: state.documents,
            translated_documents: state.translated_documents,
            free_name: state.generalInfo.freeName,
            country: state.generalInfo.countryCode,
            keys: state.keys,
            process_id: state.processId,
            lookup_items: state.lookupItems,
            parties_config: state.partiesConfigTable, // Include updated parties_config
          }

          // Make API call to update the profile
          await axios.put(`/dashboard/profiles/${profileId}/`, payload)
          this.showToast(`Columns configuration saved for ${tableName}`, 'success')

          // COMMENTED OUT: Using projectKeyItems filtering instead of dynamic columns
          // Refresh the dynamic column templates to get any newly added columns
          // await this.$store.dispatch('profile/fetchPartiesDynamicColumn')

          // Refresh the specific table data to reflect column changes
          await this.fetchTableNames()

          // Emit event to refresh lookup table columns
          bus.$emit('profile/columnsUpdated')
        } else {
          // In create mode, just update the store (will be saved on final submit)
          this.showToast(`Columns configuration updated for ${tableName}`, 'success')
        }
      } catch (error) {
        this.showToast(
          error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to save columns configuration',
          'danger',
          'AlertTriangleIcon',
        )
      }
    },

    openRecordDialog(tableName, mode, record = null) {
      this.currentTableName = tableName
      this.modalMode = mode
      this.currentRecord = record
      this.formData = mode === 'edit' && record ? { ...record } : {}
      this.$bvModal.show(`record-modal-${tableName}`)
    },

    openDeleteDialog(tableName, record) {
      this.currentTableName = tableName
      this.currentDeleteRecord = record
      this.$bvModal.show(`delete-modal-${tableName}`)
    },

    resetRecordForm() {
      this.formData = {}
      this.currentRecord = null
      this.currentTableName = null
      this.modalMode = 'add'
    },

    async handleRecordSubmit(tableName, bvModalEvt) {
      if (!this.isComponentMounted) return

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
      const refName = `formObserver_${tableName}`
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

      const isEdit = this.modalMode === 'edit'
      const successMsg = isEdit ? 'Record updated successfully' : 'Record created successfully'

      try {
        if (isEdit) {
          await this.$store.dispatch('profile/updatePartyRecord', {
            tableName,
            recordId: this.currentRecord?.id || this.currentRecord?.ID,
            record: this.formData,
          })
        } else {
          await this.$store.dispatch('profile/addPartyRecord', {
            tableName,
            record: this.formData,
          })
        }

        this.showToast(successMsg, 'success', 'CheckIcon')
        await this.fetchTableData(tableName, true)
        this.$bvModal.hide(`record-modal-${tableName}`)
        this.resetRecordForm()
      } catch (error) {
        let errMsg = 'An error occurred'
        if (error.response) {
          errMsg = error.response.data?.detail
            || error.response.data?.message
            || error.response.data?.error
            || `Failed to ${isEdit ? 'update' : 'create'} record`

          if (error.response.data?.errors) {
            errMsg = Object.values(error.response.data.errors).flat().join('; ')
          }
        } else if (error.message) {
          errMsg = error.message
        } else {
          errMsg = `Failed to ${isEdit ? 'update' : 'create'} record`
        }

        this.showToast(errMsg, 'danger', 'AlertTriangleIcon')
      }
    },

    // Open manage columns dialog for adding/removing table schema columns
    openManageColumnsDialog(tableName) {
      this.currentManageColumnsTable = tableName
      this.showManageColumnsDialog = true
    },

    // Close manage columns dialog
    closeManageColumnsDialog() {
      this.showManageColumnsDialog = false
      this.currentManageColumnsTable = null
    },

    // Save column schema changes
    async handleSaveColumns(columnsData) {
      if (!this.currentManageColumnsTable) return

      const tableName = this.currentManageColumnsTable

      try {
        // Call API to update column schema
        await this.$store.dispatch('profile/updatePartyColumns', {
          tableName,
          columns: columnsData,
        })

        // Show success toast
        this.$bvToast.toast('Columns updated successfully', {
          title: 'Success',
          variant: 'success',
          solid: true,
        })

        // Refresh table data to get updated columns
        await this.fetchTableData(tableName, true)

        // Notify dialog of success - this will close it
        if (this.$refs.partyColumnsDialog) {
          this.$refs.partyColumnsDialog.onSaveSuccess()
        }
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to update columns'
        // Show toast notification
        this.$bvToast.toast(
          errorMessage,
          {
            title: 'Error',
            variant: 'danger',
            solid: true,
          },
        )
        // Notify dialog of error - keep it open and show error inside
        if (this.$refs.partyColumnsDialog) {
          this.$refs.partyColumnsDialog.onSaveError(errorMessage)
        }
      }
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';
.max-table-col-w {
  max-width: 500px;
  overflow-wrap: break-word;
  white-space: normal;
}
.per-page-selector {
  width: 7rem;
  // height: 2.5rem;
}
.mt-delete-icon {
  margin-top: 6px;
}
</style>
