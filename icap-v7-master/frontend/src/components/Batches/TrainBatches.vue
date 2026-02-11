<!--
 Organization: AIDocbuilder Inc.
 File: TrainBatches.vue
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
    <!-- Alert to display errors when loading fails -->
    <b-alert
      variant="danger"
      :show="!loading && error ? true : false"
    >
      <div class="alert-body">
        <p>{{ error }}</p>
      </div>
    </b-alert>

    <!-- Main card container -->
    <b-card
      v-if="!error"
      no-body
      class="mb-0"
    >

      <!-- Top actions and search filters -->
      <div class="m-2">
        <b-row>
          <!-- Action buttons for bulk operations -->
          <b-col
            cols="4"
            md="4"
            class="d-flex align-items-center justify-content-start mb-1 mb-md-0"
          >
            <b-dropdown
              text="Actions"
              variant="primary"
            >
              <b-dropdown-item
                v-if="isAdmin"
                :disabled="selectedRecords.length === 0"
                @click="deleteMultipleHandler"
              >
                <feather-icon icon="TrashIcon" />
                <span class="align-middle ml-50">Delete</span>
              </b-dropdown-item>
              <b-dropdown-item
                :disabled="selectedRecords.length === 0"
                @click="reProcessMultipleHandler"
              >
                <feather-icon icon="RefreshCwIcon" />
                <span class="align-middle ml-50">Re-Process</span>
              </b-dropdown-item>
            </b-dropdown>
            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="uploadTrainBatch = true"
            >
              Upload Train Batch
            </b-button>
            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="isTraining = true"
            >
              Search Training Batch
            </b-button>
          </b-col>

          <!-- Search and filter options -->
          <b-col
            cols="8"
            md="8"
            class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
          >
            <b-button
              v-if="!noSearches"
              variant="outline-danger"
              size="sm"
              class="mr-1"
              @click="clearSearch"
            >
              Clear Search
            </b-button>
            <!-- Search by linked batch ID -->
            <div class="mr-1">
              <b-form @submit.prevent="searchSubmitHandler">
                <b-input-group
                  class="input-group-merge"
                >
                  <template #append>
                    <b-input-group-text class="py-0 my-0">
                      <span>
                        <feather-icon
                          icon="SearchIcon"
                          size="15"
                          class="cursor-pointer"
                          @click="searchSubmitHandler"
                        />
                      </span>
                    </b-input-group-text>
                  </template>
                  <b-form-input
                    v-model="searchBy.linked_batch_id"
                    placeholder="Search by Linked Batch"
                  />
                </b-input-group>
              </b-form>
            </div>
            <!-- Filter options for extension type -->
            <v-select
              v-model="searchBy.extension_type"
              :options="extentionOptions"
              :reduce="option => option.value"
              :clearable="false"
              class="refresh-rate-selector d-inline-block mx-50"
            />
            <!-- Refresh interval selection -->
            <div class="mr-1">
              <feather-icon
                v-b-tooltip.hover
                icon="FilterIcon"
                class="cursor-pointer mr-1"
                size="20"
                title="Filter Train Batches"
                @click.stop="filterTrainBatches = true"
              />
              <label>Refresh Rate</label>
              <v-select
                v-model="refreshInterval"
                :options="refreshIntervalOptions"
                :reduce="option => option.value"
                :clearable="false"
                class="refresh-rate-selector d-inline-block mx-50"
              />
            </div>
            <!-- Entries per page selector -->
            <div>
              <label>Show</label>
              <v-select
                v-model="perPage"
                :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
                :options="perPageOptions"
                :clearable="false"
                class="per-page-selector d-inline-block mx-50"
              />
              <label>entries</label>
            </div>
          </b-col>
        </b-row>
      </div>

      <!-- Table displaying batch data -->
      <b-table-simple
        :class="{
          'table-busy': loading
        }"
        class="batches-table"
      >
        <colgroup>
          <col
            v-for="(tableColumn) of tableColumns"
            :key="tableColumn.key"
            :style="{ width: tableColumn.width + '%' }"
          >
        </colgroup>

        <!-- Table headers -->
        <b-thead>
          <b-tr>
            <template
              v-for="tableColumn of tableColumns"
            >
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
          <!-- Custom search inputs for table columns -->
          <b-tr>
            <template
              v-for="tableColumn of tableColumns"
            >
              <b-th
                v-if="tableColumn.customSearch"
                :key="tableColumn.key"
              >
                <b-form
                  @submit.prevent="searchSubmitHandler"
                >
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

        <!-- Table body displaying batch rows -->
        <b-tbody
          v-if="!loading"
          :key="isStatus"
        >
          <template v-for="(batch) of batches">
            <!-- Main row for batch data -->
            <b-tr
              :key="`main-row-${batch.id}`"
              :class="{
                'has-row-details': expandedRowIds.includes(batch.id)
              }"
            >
              <b-td>
                <b-form-checkbox
                  v-model="selectedRecords"
                  :value="batch.id"
                />
              </b-td>
              <b-td>

                {{ batch.id }}
              </b-td>
              <b-td>
                {{ batch.matched_profile_name }}
              </b-td>
              <b-td>
                {{ batch.customer || batch.custom_data || '-' }}
              </b-td>
              <!-- <b-td>
                {{ batch.manual_classification_status }}
              </b-td> -->
              <b-td
                :class="{ 'cursor-pointer': batch.status === 'classification review' || batch.status === 'classification error' }"
                @click="handleBatchClick(batch)"
              >
                <status-tag :status="batch.status" />
              </b-td>
              <b-td>
                {{ formatedDate(batch.created_at) }}
              </b-td>
              <b-td>
                <div class="text-nowrap">
                  <div class="d-inline">
                    <feather-icon
                      v-b-tooltip.hover
                      :icon="expandedRowIds.includes(batch.id) ? 'ChevronDownIcon' : 'ChevronUpIcon'"
                      class="cursor-pointer"
                      size="18"
                      title="View Train Batch Details"
                      @click="toggleRowDetails(batch.id)"
                    />
                  </div>
                  <div
                    class="d-inline"
                    @click="setTimelineId(batch.id)"
                  >
                    <timeline
                      :batch-id="`${batch.id}`"
                      :icon-size="'18'"
                      class="ml-1"
                      @show-details-change="handleShowDetailsChange"
                    />
                  </div>
                  <feather-icon
                    v-b-tooltip.hover
                    title="Classification Interface"
                    icon="FileTextIcon"
                    class="cursor-pointer ml-1"
                    :class="{ 'disabled': true }"
                    size="18"
                    @click.stop="renderClassificationBatch(batch.id)"
                  />

                  <b-spinner
                    v-if="!downloadTransaction && downloadingZips.includes(batch.id)"
                    small
                    label="Small Spinner"
                    class="ml-1"
                  />
                  <feather-icon
                    v-else
                    v-b-tooltip.hover
                    title="Download Train Batch (Zip)"
                    icon="DownloadCloudIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    @click.stop="downloadZip(batch.id)"
                  />
                  <feather-icon
                    v-if="isAdmin"
                    v-b-tooltip.hover
                    icon="TrashIcon"
                    class="ml-1 cursor-pointer"
                    size="18"
                    title="Delete Train Batch"
                    @click="deleteHandler(batch.id)"
                  />
                </div>
              </b-td>
            </b-tr>

            <!-- Detail row for expanded batch information -->
            <b-tr
              v-if="expandedRowIds.includes(batch.id)"
              :key="`detail-row-${batch.id}`"
              class="p-0 m-0"
            >
              <b-td
                colspan="12"
                class="p-0 m-0"
              >
                <train-batch-details
                  :train-batch="batch"
                  :extension-type="searchExtensionType"
                />
              </b-td>
            </b-tr>
          </template>
        </b-tbody>
      </b-table-simple>

      <!-- Spinner while loading data -->
      <div
        v-if="loading"
        class="text-center m-3 table-busy-spinner"
      >
        <b-spinner
          variant="primary"
        />
      </div>

      <!-- No data available message -->
      <div
        v-if="!loading && batches.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>

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

    <upload-zip
      v-if="uploadTrainBatch"
      title="Upload Train Batch"
      label="Zip File (.zip):"
      api-endpoint="/pipeline/upload_training_batch/"
      replace
      @uploaded="fetchBatches"
      @modal-closed="uploadTrainBatch = false"
    />
    <upload-datasets
      v-if="isTraining"
      title=""
      api-endpoint="/pipeline/get_annotation_batches/"
      @modal-closed="isTraining = false"
      @submitted="fetchBatches"
    />

    <delete-train-batch
      v-if="deleteBatches.length > 0"
      :ids="deleteBatches"
      @modal-closed="deleteBatches = []"
      @deleted="fetchBatches"
    />

    <ReProcessBatch
      v-if="reProcessBatches.length > 0"
      title="Re-Process Train Batch"
      :ids="reProcessBatches"
      api-url="/pipeline/re_process_training_batches/"
      @modal-closed="reProcessBatches = []"
      @completed="fetchBatches"
    />

    <filter-options
      v-if="filterTrainBatches"
      @modal-closed="filterTrainBatches = false"
    />
    <confirm-clear-searches
      v-if="clearSearches"
      v-model="searchBy"
      @submited="fetchBatches"
      @modal-closed="clearSearches = false"
    />
    <b-modal
      v-model="showClassificationReviewModal"
      centered
      title="Classification Review"
      @ok="clickClassificationSubmit"
    >
      <b-card-text>
        <div>
          You can review or submit this classification.
        </div>
      </b-card-text>

      <template #modal-footer="{ ok }">
        <b-button
          variant="warning"
          @click="clickClassificationReview()"
        >
          Review
        </b-button>
        <b-button
          variant="primary"
          :disabled="false"
          @click="ok()"
        >
          Submit
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>

import axios from 'axios'
import {
  BCard, BCardText, BRow, BCol, BSpinner, BAlert, BFormCheckbox, BDropdown, BDropdownItem, BForm, BFormInput,
  BTableSimple, BThead, BTr, BTbody, BTh, BTd, VBTooltip, BInputGroup, BInputGroupText, BButton, BModal,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import WS from '@/utils/ws'
import bus from '@/bus'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import FilterOptions from '@/components/UI/FilterOptions.vue'
import ConfirmClearSearches from '@/components/UI/ConfirmClearSearches.vue'
import DeleteTrainBatch from '@/components/Batches/DeleteTrainBatch.vue'
import UploadZip from '@/components/UI/UploadZip.vue'
import ReProcessBatch from '@/components/Batches/ReProcessBatch.vue'
import Timeline from '@/components/UI/Timeline/Timeline.vue'
import TrainBatchDetails from '@/components/Batches/TrainBatchDetails.vue'
import StatusTag from '@/components/Batches/StatusTag.vue'
import UploadDatasets from '../Training/UploadDatasets.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BModal,
    BCardText,
    BCard,
    BRow,
    BCol,
    BSpinner,
    BAlert,
    BDropdown,
    BDropdownItem,
    BFormCheckbox,
    BForm,
    BFormInput,
    vSelect,
    DeleteTrainBatch,
    ReProcessBatch,
    Timeline,
    UploadZip,
    BTableSimple,
    BThead,
    BTr,
    BTbody,
    BTh,
    BTd,
    DetailedPagination,
    FilterOptions,
    ConfirmClearSearches,
    TrainBatchDetails,
    StatusTag,
    BInputGroup,
    BInputGroupText,
    BButton,
    UploadDatasets,
  },
  data() {
    return {
      loading: true,
      error: null,
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      batches: [],
      // Generates table columns dynamically
      tableColumns: [
        { key: 'select', label: '', width: 1 },
        {
          key: 'id', label: 'ID', sortable: true, customSearch: true, width: 15,
        },
        // {
        //   key: 'train_from', label: 'Train From', sortable: true, customSearch: true, width: 20,
        // },
        {
          key: 'matched_profile_name', label: 'Matched Process', sortable: true, customSearch: true, width: 20,
        },
        {
          key: 'customer', label: 'Customer', sortable: true, customSearch: true, width: 15,
        },
        // {
        //   key: 'manual_classification_status', label: 'Manual Classification Status', sortable: true, customSearch: true, width: 25,
        // },
        {
          key: 'status', label: 'Status', sortable: true, customSearch: true, width: 10,
        },
        {
          key: 'created_at', label: 'Created At', sortable: true, width: 10,
        },
        { key: 'actions', label: 'Actions', width: 10 },
      ],
      deleteBatches: [],
      reProcessBatches: [],
      selectedRecords: [],
      allRecordsSeleted: false,
      sortBy: 'created_at',
      sortDesc: true,
      initialized: false,
      searchBy: {
        id: null,
        train_from: null,
        train_subject: null,
        matched_profile_name: null,
        customer: null,
        status: null,
        linked_batch_id: null,
        extension_type: 'all',
      },
      downloadingZips: [],
      expandedRowIds: [],
      uploadTrainBatch: false,
      isTraining: false,
      uploadTransaction: false,
      refreshIntervalOptions: [
        { label: '---', value: 0 },
        { label: '10 sec', value: 10 },
        { label: '20 sec', value: 20 },
        { label: '30 sec', value: 30 },
        { label: '1 min', value: 60 },
      ],
      extentionOptions: [
        { label: 'All', value: 'all' },
        { label: 'PDF', value: '.pdf' },
        { label: 'Excel', value: '.xlsx' },
      ],
      refreshInterval: 0,
      clearInterval: null,
      filterTrainBatches: false,
      reFetchTrainBatches: false,
      downloadTransaction: false,
      isDisabled: true,
      isStatus: 0,
      clearSearches: false,
      showClassificationReviewModal: false,
      modalBatchId: null,
    }
  },
  computed: {
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    // Returns an array of batch IDs from the `batches` array.
    batchIds() {
      return this.batches.map(batch => batch.id)
    },
    // Stores filter settings like `searchBy` and `perPage` for persistence or reuse.
    stickyFilters() {
      return {
        searchBy: this.searchBy,
        perPage: this.perPage,
      }
    },
    // Retrieves selected project countries from the Vuex store.
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    // Builds a structured object categorizing projects by country.
    filterBy() {
      const result = {}

      this.selectedProjectCountries.forEach(e => {
        const { countryCode, project } = e

        // Initialize the array for the country code if not already present.
        if (!result[countryCode]) {
          result[countryCode] = []
        }

        // Add the project to the country code's list if not already included.
        if (!result[countryCode].includes(project)) {
          result[countryCode].push(project)
        }
      })

      return {
        project_countries: result,
      }
    },
    // Checks if all `searchBy` filters are unset or set to 'all'.
    noSearches() {
      return Object.values(this.searchBy).every(value => value === null || value === 'all' || value === '')
    },
    // Gets the newly created train ID from the Vuex store.
    getNewCreatedTrainID() {
      return this.$store.getters['classifications/getNewCreatedTrainID']
    },
    // Retrieves the `extension_type` value from `searchBy` filters.
    searchExtensionType() {
      return this.searchBy.extension_type
    },
  },
  watch: {
    // When `perPage` changes, reset the current page and fetch new batch data.
    perPage() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchBatches()
      }
    },
    // When `searchExtensionType` changes, reset the current page and fetch new batch data.
    searchExtensionType() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchBatches()
      }
    },
    // Watches for changes in selected records checks if all records are selected.
    selectedRecords(newValue) {
      if (this.batches.length > 0 && newValue.length === this.batches.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    // Updates selected and expanded records when `batches` change, ensuring they still exist.
    batches() {
      this.selectedRecords = this.selectedRecords.filter(id => {
        const index = this.batches.findIndex(batch => batch.id === id)
        return index !== -1
      })

      this.expandedRowIds = this.expandedRowIds.filter(id => {
        const index = this.batches.findIndex(batch => batch.id === id)
        return index !== -1
      })
    },
    // Persists sticky filters to localStorage whenever they change.
    stickyFilters: {
      handler() {
        localStorage.setItem('train-batches-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true, // Ensures the handler is triggered for nested property changes.
    },
    // Monitors batch IDs to join/leave WebSocket rooms based on additions/removals.
    batchIds(newValue, oldValue) {
      const addedBatches = newValue.filter(item => !oldValue.includes(item))
      const removedBatches = oldValue.filter(item => !newValue.includes(item))
      addedBatches.forEach(batchId => {
        WS.joinRoom(`train_batch_status_tag_${batchId}`)
      })
      removedBatches.forEach(batchId => {
        WS.leaveRoom(`train_batch_status_tag_${batchId}`)
      })
    },
    // Triggers auto-refresh when the refresh interval changes.
    refreshInterval(newVal, oldVal) {
      if (newVal === oldVal) {
        return
      }

      this.autoDataRefresh()
    },
    // Refetches batch data when filters change and the component is not loading.
    filterBy() {
      if (!this.loading) {
        this.fetchBatches()
      } else {
        this.reFetchTrainBatches = true
      }
    },
    // Refetches batch data after loading finishes if re-fetching is flagged.
    loading(newVal) {
      if (!newVal && this.reFetchTrainBatches) {
        this.reFetchTrainBatches = false
        this.fetchBatches()
      }
    },
  },
  created() {
    localStorage.setItem('batch-type', '')
    // Retrieve the last active page from localStorage and set it as the current page.
    const currentPage = localStorage.getItem('train-batches-last-active-page')
    if (currentPage) {
      this.currentPage = parseInt(currentPage, 10)
    }

    // Retrieve filter data from localStorage and apply it to `searchBy` and `perPage`.
    const batchesFilterData = localStorage.getItem('train-batches-filter')
    if (batchesFilterData) {
      const batchesFilter = JSON.parse(batchesFilterData)
      if (batchesFilter.searchBy) {
        // Merge with default searchBy to ensure new fields are included
        this.searchBy = { ...this.searchBy, ...batchesFilter.searchBy }
      }
      if (batchesFilter.perPage) {
        this.perPage = batchesFilter.perPage
      }
    }

    // Ensure the component is fully initialized before proceeding.
    this.$nextTick(() => {
      this.initialized = true
    })

    // If a new train ID exists, set it as a filter criterion.
    if (this.getNewCreatedTrainID) {
      this.searchBy.id = this.getNewCreatedTrainID
    }

    // Initialize component-specific settings and start automatic data refresh.
    this.initialize()
    this.autoDataRefresh()
  },
  mounted() {
    // Fetch the initial batch data when the component is mounted.
    this.fetchBatches()

    // Clear the new train ID in the Vuex store.
    this.$store.commit('classifications/SET_NEW_CREATED_TRAIN_ID', '')
  },
  destroyed() {
    // Save the current page to localStorage before the component is destroyed.
    localStorage.setItem('train-batches-last-active-page', this.currentPage)

    // Perform cleanup tasks like unsubscribing from events and WebSocket rooms.
    this.cleanup()
  },
  methods: {
    // Initializes event listeners for WebSocket data.
    initialize() {
      bus.$on('wsData/trainBatchStatusTag', this.onTrainBatchStatusTag)
    },
    // Cleans up WebSocket connections and event listeners.
    cleanup() {
      this.batchIds.forEach(batchId => {
        WS.leaveRoom(`train_batch_status_tag_${batchId}`)
      })
      bus.$off('wsData/trainBatchStatusTag', this.onTrainBatchStatusTag)

      // Clear any running intervals.
      clearInterval(this.clearInterval)
    },
    // Handles page changes by updating the current page and fetching new data.
    pageChanged(page) {
      this.currentPage = page
      this.fetchBatches()
    },
    // Submits the search form, resets to the first page, and fetches data.
    async searchSubmitHandler() {
      this.currentPage = 1
      await this.fetchBatches()
    },
    // Toggles sorting by the specified column and fetches updated data.
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchBatches()
    },
    // Clears all search filters and resets the results.
    clearSearch() {
      this.searchBy = Object.fromEntries(
        Object.keys(this.searchBy).map(key => [key, key === 'extension_type' ? 'all' : null]),
      )
      this.expandedRowIds = []
      this.fetchBatches()
    },
    // Fetches the batch data based on current filters, pagination, and sorting.
    fetchBatches() {
      this.loading = true

      // Prepare data and parameters for the API request.
      const data = {
        ...this.filterBy,
      }

      // Trim the linked batch ID filter if it exists.
      this.searchBy.linked_batch_id = this.searchBy.linked_batch_id ? this.searchBy.linked_batch_id.trim() : null

      const params = {
        page_size: this.perPage,
        page: this.currentPage,
        sort_by: this.sortBy,
        sort_desc: this.sortDesc,
        ...this.searchBy,
      }

      // Send an API request to fetch the filtered and paginated batches.
      axios.post('/train-batches/filter_list/', data, {
        params,
      })
        .then(res => {
          // Update batch data and total record count.
          this.batches = res.data.results
          this.totalRecords = res.data.count
          this.loading = false

          // Automatically expand the row if only one result is returned.
          if (res.data.results.length === 1 && this.searchBy.linked_batch_id) {
            if (!this.expandedRowIds.includes(res.data.results[0].id)) {
              this.toggleRowDetails(res.data.results[0].id)
            }
          } else {
            this.expandedRowIds = []
          }
        })
        .catch(error => {
          // Handle errors during the data fetch process.
          this.loading = false
          const errorResponse = error?.response
          if (errorResponse && errorResponse.status === 404 && this.currentPage > 1) {
            // If a 404 error occurs, decrement the page and try fetching again.
            this.currentPage -= 1
            this.fetchBatches()
          } else {
            this.error = error?.response?.data?.detail || ' Error fetching train batches'
          }
        })
    },
    formatedDate(dateString) {
      // return moment.utc(dateString).tz('America/New_York').format('DD/MM/YYYY HH:mm')
      const date = new Date(dateString)
      // Format the date as "30/10/2024"
      const datePart = date.toLocaleDateString('en-GB') // 'en-GB' gives DD/MM/YYYY format
      // Format the time as "10:41 AM"
      const timePart = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      })
      return `${datePart} ${timePart}`
    },
    // Handles deletion of a single batch by setting it to the `deleteBatches` array.
    deleteHandler(id) {
      this.deleteBatches = [id]
    },
    // Handles deletion of multiple batches by adding all selected records to `deleteBatches`.
    deleteMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.deleteBatches = [...this.selectedRecords]
    },
    // Prepares multiple selected batches for reprocessing.
    reProcessMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.reProcessBatches = [...this.selectedRecords]
    },
    // Toggles the selection of all records based on the `checked` state.
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.batches.map(doc => doc.id) : []
    },
    // Downloads a batch as a ZIP file, supporting both train batch and transaction types.
    downloadZip(batchId, type = 'trainBatch') {
      let apiEndpoint = '/pipeline/download_training_batch/'
      if (type === 'Transaction') {
        this.downloadTransaction = true
        apiEndpoint = '/pipeline/download_transaction/'
      }

      this.downloadingZips.push(batchId)

      axios.get(apiEndpoint, {
        params: {
          train_batch_id: batchId,
        },
        responseType: 'blob',
      }).then(response => {
        // Create a temporary link to trigger the file download.
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${batchId}.zip`)
        document.body.appendChild(link)
        link.click()

        // Remove the batch from the downloading queue.
        this.downloadingZips = this.downloadingZips.filter(itemId => itemId !== batchId)

        if (type === 'Transaction') {
          this.downloadTransaction = false
        }
      }).catch(async error => {
        // convert blob response to json
        // Handle errors and parse the response to extract a message.
        let responseDataJSON = null
        if (error?.response?.data) {
          const responseData = await error?.response?.data.text()
          responseDataJSON = JSON.parse(responseData)
        }

        const message = responseDataJSON?.detail || 'Error downloading batch'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        this.downloadingZips = this.downloadingZips.filter(itemId => itemId !== batchId)

        if (type === 'Transaction') {
          this.downloadTransaction = false
        }
      })
    },
    // Expands or collapses the details of a row based on its ID.
    toggleRowDetails(id) {
      const index = this.expandedRowIds.indexOf(id)
      if (index > -1) {
        this.expandedRowIds.splice(index, 1)
      } else {
        this.expandedRowIds.push(id)
      }
    },
    // Handles WebSocket updates for batch status, updating the corresponding batch in the list.
    onTrainBatchStatusTag(data) {
      this.isStatus += 1
      this.batches.forEach((item, index) => {
        if (item.id === data.batch_id) {
          this.batches[index].status = data.status
        }
      })
    },
    // Sets up automatic data refresh at the specified interval.
    autoDataRefresh() {
      clearInterval(this.clearInterval)

      if (!this.refreshInterval) {
        return
      }

      this.clearInterval = setInterval(() => {
        this.fetchBatches()
      }, this.refreshInterval * 1000)
    },
    // Adjusts data refresh behavior based on whether details are being shown.
    handleShowDetailsChange(showDetails) {
      if (showDetails) {
        clearInterval(this.clearInterval)
        return
      }
      this.autoDataRefresh()
    },
    // Emits an event to set the timeline ID for another component.
    setTimelineId(batchID) {
      bus.$emit('setTimelineID', batchID)
    },
    // Determines if manual classification is enabled based on the batch's status.
    isManualClassificationEnabled(batch) {
      if (['ready', 'submitted'].includes(batch.manual_classification_status) || ['classification error', 'classification review'].includes(batch.status)) {
        return true
      }

      return false
    },
    // Displays a modal for classification review for a specific batch.
    showModal(batchId) {
      this.showClassificationReviewModal = true
      this.modalBatchId = batchId
    },
    // Submits the classification review for a batch and closes the modal on success.
    async clickClassificationSubmit() {
      const isSuccess = await this.$store.dispatch('classifications/verifyClassification', {
        train_batch_id: this.modalBatchId,
        forceSubmit: true,
      })
      if (isSuccess) {
        this.showClassificationReviewModal = false
      }
    },
    // Redirects to the classification review page for the current modal batch.
    clickClassificationReview() {
      this.$router.push({ name: 'classification', params: { id: this.modalBatchId } })
    },
    // Redirects to the classification page for the specified batch.
    renderClassificationBatch(batchId) {
      this.$router.push({ name: 'classification', params: { id: batchId } })
    },
    // Handles clicks on a batch row, triggering modals or redirects based on its status.
    handleBatchClick(batch) {
      if (batch.status === 'classification review') {
        this.showModal(batch.id)
      } else if (batch.status === 'classification error') {
        this.$router.push({ name: 'classification', params: { id: batch.id } })
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.per-page-selector {
  width: 90px;
}
.refresh-rate-selector {
  width: 120px;
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
  tr.has-row-details {
    border-bottom: hidden;
  }
}
.disabled {
  pointer-events: none;
  opacity: 0.5;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
