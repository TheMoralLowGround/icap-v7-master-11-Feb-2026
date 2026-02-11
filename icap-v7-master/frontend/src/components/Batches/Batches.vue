<!--
 Organization: AIDocbuilder Inc.
 File: Batches.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   The `trainBatches.vue` component is designed to facilitate the management and monitoring of train batch data.
   It includes features like search, filtering, sorting, bulk operations, and refresh intervals to optimize user interactions.

 Features:
   - Displays train batch records in a tabular format with options for pagination, sorting, and filtering.
   - Provides bulk actions, including delete and reprocess operations, for selected records.
   - Includes search functionality by linked batch ID and filtering by file extension.
   - Allows users to upload new train batches or filter existing batches with ease.
   - Dynamically adjusts display settings, including refresh intervals and entries per page.

 Dependencies:
   - `bootstrap-vue`: For UI components like alerts, buttons, cards, and tables.
   - `vue-select`: For dropdown selectors.
   - Custom components: Includes components for pagination, filtering, batch details, status tags, and more.

 Key Data Properties:
   - `batches`: Array of batch records fetched from the backend.
   - `selectedRecords`: Tracks user-selected records for bulk operations.
   - `searchBy`: Stores filter and search parameters.
   - `refreshInterval`: Interval for automatic data refresh.

 Notes:
   - Ensures error handling and user feedback via alert messages.
   - Utilizes Vuex for state management, enabling cross-component communication.
   - Provides a scalable structure for future enhancements, like advanced filtering or additional bulk actions.
-->

<template>
  <div>
    <!-- Error alert section -->
    <b-alert
      variant="danger"
      :show="!loading && error ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ error }}
        </p>
      </div>
    </b-alert>

    <!-- Card to contain batch actions and table -->
    <b-card
      v-if="!error"
      no-body
      class="mb-0"
    >
      <div class="m-2">
        <b-row>
          <!-- Left section for dropdown actions -->
          <b-col
            cols="12"
            md="6"
            class="d-flex align-items-center justify-content-start mb-1 mb-md-0"
          >
            <b-dropdown
              text="Actions"
              variant="primary"
            >
              <!-- Delete selected records action -->
              <b-dropdown-item
                :disabled="selectedRecords.length === 0"
                @click="deleteMultipleHandler"
              >
                <feather-icon icon="TrashIcon" />
                <span class="align-middle ml-50">Delete</span>
              </b-dropdown-item>
              <!-- Re-process actions -->
              <b-dropdown-item
                :disabled="selectedRecords.length === 0"
                @click="reProcessMultipleHandler('extraction')"
              >
                <feather-icon icon="RefreshCcwIcon" />
                <span class="align-middle ml-50">Re-Process Extraction</span>
              </b-dropdown-item>
              <b-dropdown-item
                :disabled="selectedRecords.length === 0"
                @click="reProcessMultipleHandler('email')"
              >
                <feather-icon icon="RefreshCwIcon" />
                <span class="align-middle ml-50">Re-Process Email</span>
              </b-dropdown-item>
            </b-dropdown>
          </b-col>

          <!-- Right section for filters and entries selection -->
          <b-col
            cols="12"
            md="6"
            class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
          >
            <!-- Filter icon for admin users -->
            <feather-icon
              v-b-tooltip.hover
              icon="FilterIcon"
              class="cursor-pointer mr-1"
              size="20"
              title="Filter Batches"
              @click.stop="filterBatches = true"
            />
            <!-- Entries per page selection -->
            <label>Show</label>
            <v-select
              v-model="perPage"
              :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
              :options="perPageOptions"
              :clearable="false"
              class="per-page-selector d-inline-block mx-50"
            />
            <label>entries</label>
          </b-col>
        </b-row>
      </div>
      <!-- Table section -->
      <b-table-simple
        :class="{ 'table-busy': loading }"
        class="batches-table"
      >
        <!-- Table column widths -->
        <colgroup>
          <col
            v-for="(tableColumn) of tableColumns"
            :key="tableColumn.key"
            :style="{ width: tableColumn.width + '%' }"
          >
        </colgroup>

        <!-- Table headers with sorting and search -->
        <b-thead>
          <b-tr>
            <template v-for="tableColumn of tableColumns">
              <!-- Checkbox for selecting all records -->
              <b-th
                v-if="tableColumn.key === 'select'"
                :key="tableColumn.key"
              >
                <b-form-checkbox
                  v-model="allRecordsSeleted"
                  :disabled="batches.length === 0"
                  @change="toggleRecordsSelection"
                />
              </b-th>
              <!-- Sortable and non-sortable columns -->
              <b-th
                v-if="tableColumn.key !== 'select' && tableColumn.sortable"
                :key="tableColumn.key"
                :aria-sort="sortBy === tableColumn.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                @click="customSort(tableColumn.key)"
              >
                {{ tableColumn.label }}
              </b-th>

              <b-th
                v-if="tableColumn.key !== 'select' && !tableColumn.sortable"
                :key="tableColumn.key"
              >
                {{ tableColumn.label }}
              </b-th>
            </template>
          </b-tr>
          <b-tr>
            <template v-for="tableColumn of tableColumns">
              <!-- Search inputs for searchable columns -->
              <b-th
                v-if="tableColumn.customSearch"
                :key="tableColumn.key"
              >
                <b-form @submit.prevent="searchSubmitHandler">
                  <b-form-input
                    v-model="searchBy[tableColumn.key]"
                    trim
                    :disabled="loading"
                    placeholder="Search"
                  />
                </b-form>
              </b-th>
              <b-th
                v-else
                :key="tableColumn.key"
              />
            </template>
          </b-tr>
        </b-thead>

        <!-- Table body -->
        <b-tbody v-if="!loading">
          <b-tr
            v-for="(batch) of batches"
            :key="batch.id"
          >
            <b-td>
              <b-form-checkbox
                v-model="selectedRecords"
                :value="batch.id"
              />
            </b-td>
            <!-- Table row data -->
            <b-td>
              <b-button
                variant="link"
                class="font-weight-bold d-block text-nowrap batch-link"
                :class="{ 'text-secondary': batch.mode === 'uploading' }"
                :disabled="batch.mode === 'uploading'"
                @click="handleNavigation(batch.id)"
              >
                {{ batch.id }}
              </b-button>
            </b-td>
            <b-td>{{ batch.vendor }}</b-td>
            <b-td>{{ batch.type }}</b-td>
            <b-td>{{ batch.definition_id }}</b-td>
            <b-td>{{ batch.project }}</b-td>
            <b-td>{{ batch.extension }}</b-td>
            <b-td v-if="!trainingMode">
              {{ batch.mode }}
            </b-td>
            <b-td>
              {{ formatedDate(batch.created_at) }}
            </b-td>
            <b-td>
              <!-- Action icons for each batch -->
              <div class="text-nowrap">
                <div
                  class="d-inline"
                  @click="setTimelineId(batch.id)"
                >
                  <timeline
                    :batch-id="batch.id"
                    :icon-size="'18'"
                  />
                </div>
                <feather-icon
                  :id="`batch-row-${batch.id}-delete-icon`"
                  icon="TrashIcon"
                  class="mx-1 cursor-pointer"
                  size="18"
                  @click="deleteHandler(batch.id)"
                />
                <b-tooltip
                  title="Delete Batch"
                  class="cursor-pointer"
                  :target="`batch-row-${batch.id}-delete-icon`"
                  boundary="window"
                />
              </div>
            </b-td>
          </b-tr>
        </b-tbody>
      </b-table-simple>

      <div
        v-if="loading"
        class="text-center m-3 table-busy-spinner"
      >
        <b-spinner
          variant="primary"
        />
      </div>

      <!-- No records message -->
      <div
        v-if="!loading && batches.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>

      <!-- Pagination -->
      <div
        v-if="!loading"
        class="mx-2 mt-1 mb-2"
      >
        <detailed-pagination
          :per-page="perPage"
          :current-page="currentPage"
          :total-records="totalRecords"
          :local-records="batches.length"
          @page-changed="pageChanged"
        />
      </div>
    </b-card>

    <!-- Delete batch modal -->
    <delete-batch
      v-if="deleteBatches.length > 0"
      :ids="deleteBatches"
      @modal-closed="deleteBatches = []"
      @deleted="fetchBatches"
    />

    <!-- Re-process batch modal -->
    <re-process-batch
      v-if="reProcessBatches.length > 0"
      :title="reProcessTitle"
      :message="reProcessMessage"
      :api-url="reProcessUrl"
      :ids="reProcessBatches"
      @modal-closed="reProcessBatches = []"
      @completed="fetchBatches"
    />

    <!-- Filter options modal -->
    <filter-options
      v-if="filterBatches"
      @modal-closed="filterBatches = false"
    />
  </div>
</template>

<script>

import axios from 'axios'
import moment from 'moment-timezone'
import {
  VBTooltip, BCard, BRow, BCol, BSpinner, BTooltip, BAlert, BFormCheckbox, BDropdown, BDropdownItem, BForm, BFormInput,
  BTableSimple, BThead, BTr, BTbody, BTh, BTd,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import bus from '@/bus'
import FilterOptions from '@/components/UI/FilterOptions.vue'
import DeleteBatch from './DeleteBatch.vue'
import ReProcessBatch from './ReProcessBatch.vue'
import Timeline from '../UI/Timeline/Timeline.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BCard,
    BRow,
    BCol,
    BSpinner,
    BTooltip,
    BAlert,
    BDropdown,
    BDropdownItem,
    BFormCheckbox,
    BForm,
    BFormInput,
    vSelect,
    DeleteBatch,
    Timeline,
    ReProcessBatch,
    BTableSimple,
    BThead,
    BTr,
    BTbody,
    BTh,
    BTd,
    DetailedPagination,
    FilterOptions,
  },
  props: {
    // Prop to determine if the component is in training mode. Defaults to false.
    trainingMode: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
  },
  data() {
    // Component's reactive state
    return {
      loading: true, // Indicates if data is being fetched
      error: null, // Stores error messages
      currentPage: 1, // Tracks the current pagination page
      perPage: 10, // Number of records per page
      totalRecords: 0, // Total number of records
      perPageOptions: [10, 25, 50, 100], // Options for records per page
      batches: [], // Holds batch data
      deleteBatches: [], // Tracks batches to delete
      reProcessBatches: [], // Tracks batches to reprocess
      selectedRecords: [], // Tracks selected records
      allRecordsSeleted: false, // Indicates if all records are selected
      sortBy: 'created_at', // Default column to sort by
      sortDesc: true, // Sort direction
      initialized: false, // Indicates if the component is initialized
      searchBy: { // Search filters
        id: null,
        vendor: null,
        type: null,
        definition_id: null,
        mode: null,
      },
      filterBatches: false, // Tracks if batches should be filtered
      reFetchBatches: false, // Flags if batches need to be refetched
      reProcessUrl: '', // URL for reprocessing batches
      reProcessTitle: '', // Title for reprocessing modal
      reProcessMessage: '', // Message for reprocessing modal
    }
  },
  computed: {
    // Checks if the current user has admin privileges
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    // Generates table columns dynamically
    tableColumns() {
      let items = [
        { key: 'select', label: '', width: 2 }, // Checkbox column for selection
        {
          key: 'id', label: 'ID', sortable: true, customSearch: true, width: 11,
        },
        {
          key: 'vendor', label: 'Customer', sortable: true, customSearch: true, width: 17,
        },
        {
          key: 'type', label: 'type', sortable: true, customSearch: true, width: 17,
        },
        {
          key: 'definition_id', label: 'Definition Process ID', sortable: true, customSearch: true, width: 17,
        },
        {
          key: 'project', label: 'Project', sortable: true, customSearch: true, width: 9,
        },
        {
          key: 'extension', label: 'File Extention', sortable: true, customSearch: true, width: 6,
        },
      ]

      // Adds 'Mode' column only if trainingMode is false
      if (!this.trainingMode) {
        items.push({
          key: 'mode', label: 'Mode', sortable: true, customSearch: true, width: 6,
        })
      }

      // Adds additional columns
      items = items.concat([
        {
          key: 'created_at', label: 'Created At', sortable: true, width: 9,
        },
        { key: 'actions', label: 'Actions', width: 6 },
      ])

      return items
    },
    // Extracts batch IDs from batch data
    batchIds() {
      return this.batches.map(batch => batch.id)
    },
    // Persists filters in local storage
    stickyFilters() {
      return {
        searchBy: this.searchBy,
        perPage: this.perPage,
      }
    },
    // Returns selected project countries and their associated projects
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    // Constructs filterBy object for API requests
    filterBy() {
      const result = {}

      this.selectedProjectCountries.forEach(e => {
        const { countryCode, project } = e

        if (!result[countryCode]) {
          result[countryCode] = []
        }

        if (!result[countryCode].includes(project)) {
          result[countryCode].push(project)
        }
      })

      return {
        project_countries: result,
      }
    },
  },
  watch: {
    // Refetches batches when perPage changes
    perPage() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchBatches()
      }
    },
    // Tracks if all records are selected
    selectedRecords(newValue) {
      if (this.batches.length > 0 && newValue.length === this.batches.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    // Removes deselected records from selectedRecords
    batches() {
      this.selectedRecords = this.selectedRecords.filter(id => {
        const index = this.batches.findIndex(doc => doc.id === id)
        return index !== -1
      })
    },
    // Updates local storage when filters change
    stickyFilters: {
      handler() {
        localStorage.setItem('batches-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true, // Ensures deep watch on nested objects
    },
    // Refetches batches when filterBy changes
    filterBy() {
      if (!this.loading) {
        this.fetchBatches()
      } else {
        this.reFetchBatches = true
      }
    },
    // Triggers data fetch after loading completes
    loading(newVal) {
      if (!newVal && this.reFetchBatches) {
        this.reFetchBatches = false
        this.fetchBatches()
      }
    },
  },
  created() {
    // Retrieve the last active page from localStorage, if available, and set it as the current page.
    const currentPage = localStorage.getItem('home-last-active-page')

    if (currentPage) {
      this.currentPage = parseInt(currentPage, 10)
    }

    // Retrieve saved filter data for batches from localStorage, if available, and apply it.
    const batchesFilterData = localStorage.getItem('batches-filter')
    if (batchesFilterData) {
      const batchesFilter = JSON.parse(batchesFilterData)
      if (batchesFilter.searchBy) {
        this.searchBy = batchesFilter.searchBy
      }
      if (batchesFilter.perPage) {
        this.perPage = batchesFilter.perPage
      }
    }

    // Ensure the component is fully initialized before marking it as initialized.
    this.$nextTick(() => {
      this.initialized = true
    })

    // Fetch the batch data on component creation.
    this.fetchBatches()
  },
  destroyed() {
    // Save the current page to localStorage before the component is destroyed.
    localStorage.setItem('home-last-active-page', this.currentPage)
  },
  methods: {
    // Handles page change events and fetches the corresponding data for the new page.
    pageChanged(page) {
      this.currentPage = page
      this.fetchBatches()
    },

    // Resets the current page to 1 and fetches batch data based on the current search criteria.
    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchBatches()
    },

    // Toggles sorting based on the specified column. Reverses sorting direction if already sorted by the same column.
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchBatches()
    },

    // Fetches batch data from the server based on filters, pagination, and sorting.
    fetchBatches() {
      this.loading = true
      const data = {
        ...this.filterBy,
      }
      const params = {
        page_size: this.perPage,
        page: this.currentPage,
        sort_by: this.sortBy,
        sort_desc: this.sortDesc,
        ...this.searchBy,
      }
      if (this.trainingMode) {
        params.mode = 'training'
      }
      axios.post('/batches/filter_list/', data, {
        params,
      })
        .then(res => {
          // Updates batches and total records count based on the response.
          this.batches = res.data.results
          this.totalRecords = res.data.count
          this.loading = false
        })
        .catch(error => {
          this.loading = false
          const errorResponse = error?.response
          if (errorResponse && errorResponse.status === 404 && this.currentPage > 1) {
            // If a page is not found, navigate to the previous page and retry fetching.
            this.currentPage -= 1
            this.fetchBatches()
          } else {
            // Handle errors and display an appropriate message.
            this.error = error?.response?.data?.detail || ' Error fetching batches'
          }
        })
    },

    // Formats a date string to a specific timezone and format using Moment.js.
    formatedDate(dateString) {
      return moment.utc(dateString).tz('America/New_York').format('DD/MM/YYYY HH:mm')
    },

    // Prepares a single batch for deletion by setting its ID.
    deleteHandler(id) {
      this.deleteBatches = [id]
    },

    // Prepares multiple selected batches for deletion.
    deleteMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.deleteBatches = [...this.selectedRecords]
    },

    // Prepares multiple selected batches for re-processing, with a different message based on the type.
    reProcessMultipleHandler(type) {
      if (this.selectedRecords.length === 0) {
        return
      }
      if (type === 'extraction') {
        this.reProcessUrl = '/pipeline/re_process_extraction/'
        this.reProcessTitle = 'Re-Process Extraction Batch'
        this.reProcessMessage = `Are you sure you want to re-process the following ${this.selectedRecords.length > 1 ? 'batches' : 'batch'} ?`
      } else if (type === 'email') {
        this.reProcessUrl = '/pipeline/re_process_training_batches/'
        this.reProcessTitle = 'Re-Process Email Batch'
        this.reProcessMessage = `The following ${this.selectedRecords.length > 1 ? 'batches' : 'batch'} will be deleted and regenerated. Are you sure? `
      }
      this.reProcessBatches = [...this.selectedRecords]
    },

    // Toggles selection of all records based on the checked state.
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.batches.map(doc => doc.id) : []
    },

    // Emits an event to set the timeline ID in another component via a shared event bus.
    setTimelineId(batchID) {
      bus.$emit('setTimelineID', batchID)
    },

    // Navigates to the detailed view of a specific batch using Vue Router.
    handleNavigation(batchId) {
      this.$router.push({ name: 'batch', params: { id: batchId } })
    },
  },
}
</script>

<style lang="scss" scoped>
.per-page-selector {
  width: 90px;
}
.batch-link.disabled {
  pointer-events: none;
}
.table-busy {
  opacity: 0.55;
  pointer-events: none;
}
.table-busy-spinner {
 opacity: 0.55;
}
.batches-table {
  td {
    padding: 0.4rem 0.5rem;
    vertical-align: baseline;
  }
  th {
    padding: 0.8rem 0.5rem;
  }
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
