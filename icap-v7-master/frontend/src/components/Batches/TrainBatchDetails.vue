<!--
 Organization: AIDocbuilder Inc.
 File: trainBatchDetails.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   The `trainBatchDetails.vue` component displays detailed information about a specific train batch.
   It includes features for displaying a list of batches with various properties, bulk actions (delete, re-process),
   and real-time status updates via WebSocket.

 Features:
   - Shows a loading spinner and error alerts during data fetch operations.
   - Displays a list of batches in a table with options for bulk actions like delete and re-process.
   - Provides a batch detail view linked by the batch ID with clickable batch links.
   - Includes individual action buttons (e.g., Timeline, Delete) for each batch.
   - Dynamically adapts its theme (dark/light mode) based on user settings.
   - Uses WebSocket to update batch status in real-time.

 Dependencies:
   - `bootstrap-vue`: For UI components like spinner, alerts, tooltips, checkboxes, dropdowns, and tables.
   - `vue-router`: For navigation and linking to batch detail pages.
   - `feather-icons`: For icons used in UI components.
   - Custom components: Includes components for deleting and re-processing batches, status tags, and timeline.
   - `@vue/composition-api`: For handling reactive data and computed properties.

 Key Data Properties:
   - `loading`: A boolean that indicates if the batch data is still being fetched.
   - `loadingError`: Stores the error message if batch fetching fails.
   - `batches`: An array of batch records to be displayed in the table.
   - `tableColumns`: Defines the columns to display in the table.
   - `selectedRecords`: Tracks the IDs of selected batches for bulk actions.
   - `deleteBatches`: Stores the batch IDs to be deleted.
   - `reProcessBatches`: Stores the batch IDs to be re-processed.

 Notes:
   - Uses `v-if` for conditional rendering of loading, error, and content sections.
   - Ensures bulk actions are only enabled when one or more records are selected.
   - Provides tooltips for delete actions to enhance user experience.
   - The `Timeline` component is used for displaying batch-specific timelines when clicked.
   - Includes modals for batch deletion and re-processing, with event handlers to refresh the batch data after actions are completed.
-->

<template>
  <!-- Main wrapper for the component, styled conditionally based on the theme (dark or light) -->
  <div
    class="train-batch-details-wrapper mb-1 mx-1 mt-50 p-1 bg"
    :class="isDark ? 'dark-bg': 'light-bg'"
  >
    <!-- Spinner displayed when data is loading -->
    <div
      v-if="loading"
      class="text-center m-1"
    >
      <b-spinner
        variant="primary"
      />
    </div>

    <!-- Alert message displayed if there's an error during loading -->
    <b-alert
      variant="danger"
      :show="!loading && loadingError ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <!-- Main content rendered when data is loaded successfully -->
    <div v-if="!loading && !loadingError">
      <!-- Header section with title and action dropdown -->
      <div
        class="d-flex align-items-center justify-content-start mb-50"
      >
        <h5 class="mb-0">
          Batches
        </h5>
        <!-- Dropdown for batch actions: Delete and Re-Process -->
        <b-dropdown
          text="Actions"
          variant="primary"
          size="sm"
          class="ml-1"
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
      </div>

      <!-- Table for displaying batch data -->
      <b-table-simple class="custom-table">
        <b-tbody>
          <!-- Table header row -->
          <b-tr>
            <template
              v-for="tableColumn of tableColumns"
            >
              <!-- Checkbox for selecting all rows -->
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

              <!-- Display table column labels -->
              <b-th
                v-if="tableColumn.key !== 'select'"
                :key="tableColumn.key"
              >
                {{ tableColumn.label }}
              </b-th>
            </template>
          </b-tr>

          <!-- Rows displaying batch data -->
          <b-tr
            v-for="(batch) of batches"
            :key="batch.id"
          >
            <!-- Checkbox for selecting individual rows -->
            <b-td>
              <b-form-checkbox
                v-model="selectedRecords"
                :value="batch.id"
              />
            </b-td>
            <!-- Batch ID linked to a detail view -->
            <b-td>
              <router-link
                v-if="!['uploading', 'supporting'].includes(batch.mode)"
                :to="{ name: 'batch', params: {transactionType: 'training', id: trainBatch.id}, query: {'transaction-type': 'training',
                                                                                                        ...(trainBatch.id && trainBatch.id.startsWith('multi_') && { 'link-batch-id': batch.id }),
                                                                                                        'batch-id': batch.id
                } }"
                class="font-weight-bold d-block text-nowrap batch-link"
              >
                {{ batch.id }}
              </router-link>
              <span
                v-else
                class="font-weight-bold d-block text-nowrap text-secondary"
              >
                {{ batch.id }}
              </span>
            </b-td>
            <!-- Displaying other batch details -->
            <b-td>{{ batch.type }}</b-td>
            <b-td>{{ batch.extension }}</b-td>
            <b-td>{{ batch.mode }}</b-td>
            <b-td><status-tag :status="batch.status" /></b-td>
            <b-td>{{ batch.confirmation_number }}</b-td>
            <b-td>
              {{ formatedDate(batch.created_at) }}
            </b-td>
            <!-- Actions for individual rows: Timeline and Delete -->
            <b-td>
              <div class="text-nowrap">
                <!-- Timeline action -->
                <div
                  class="d-inline"
                  @click="setTimelineId(batch.id)"
                >
                  <timeline
                    :batch-id="batch.id"
                    :icon-size="'18'"
                  />
                </div>
                <!-- Delete action with tooltip -->
                <feather-icon
                  v-if="isAdmin"
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

      <!-- Message displayed if no batch records are found -->
      <div
        v-if="!loading && batches.length === 0"
        class="text-center m-1"
      >
        No records found!
      </div>
      <div
        v-if="!loading && isProfileTraining"
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
    </div>

    <!-- Modal for deleting batches -->
    <delete-batch
      v-if="deleteBatches.length > 0"
      :ids="deleteBatches"
      :is-profile-training="isProfileTraining"
      @modal-closed="deleteBatches = []"
      @deleted="fetchBatches"
    />

    <!-- Modal for re-processing batches -->
    <re-process-batch
      v-if="reProcessBatches.length > 0"
      title="Re-Process Batch"
      :ids="reProcessBatches"
      api-url="/pipeline/re_process_extraction/"
      @modal-closed="reProcessBatches = []"
      @completed="fetchBatches"
    />
  </div>
</template>

<script>

import axios from 'axios'
import {
  BSpinner, BTooltip, BAlert, BFormCheckbox, BDropdown, BDropdownItem,
  BTableSimple, BTr, BTbody, BTd, BTh,
} from 'bootstrap-vue'
import WS from '@/utils/ws'
import bus from '@/bus'

import DeleteBatch from '@/components/Batches/DeleteBatch.vue'
import ReProcessBatch from '@/components/Batches/ReProcessBatch.vue'
import Timeline from '@/components/UI/Timeline/Timeline.vue'
import StatusTag from '@/components/Batches/StatusTag.vue'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import useAppConfig from '@core/app-config/useAppConfig'
import { computed } from '@vue/composition-api'

export default {
  setup() {
    const { skin } = useAppConfig()

    const isDark = computed(() => skin.value === 'dark')

    return { skin, isDark }
  },
  components: {
    BSpinner,
    BTooltip,
    BAlert,
    BDropdown,
    BDropdownItem,
    BFormCheckbox,
    DeleteBatch,
    Timeline,
    ReProcessBatch,
    BTableSimple,
    BTr,
    BTbody,
    BTh,
    BTd,
    StatusTag,
    DetailedPagination,
  },
  props: {
    trainBatch: {
      type: Object,
      required: true,
    },
    isProfileTraining: {
      type: Boolean,
      required: false,
    },
    extensionType: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loading: true, // Indicates if the data is still being fetched
      loadingError: null, // Stores error message if batch fetching fails
      batches: [], // List of batches displayed in the table
      tableColumns: [ // Table column configurations
        { key: 'select', label: '' }, // Column for selecting rows
        { key: 'id', label: 'ID' }, // Batch ID column
        { key: 'type', label: 'Type' }, // Batch type column
        { key: 'extension', label: 'File Extension' }, // File extension column
        { key: 'mode', label: 'Mode' }, // Processing mode column
        { key: 'status', label: 'Status' }, // Batch status column
        { key: 'confirmation_number', label: 'Confirmation No.' }, // Confirmation number column
        { key: 'created_at', label: 'Created At' }, // Batch creation date column
        { key: 'actions', label: 'Actions' }, // Action buttons column
      ],
      deleteBatches: [], // Stores batch IDs to be deleted
      reProcessBatches: [], // Stores batch IDs to be reprocessed
      selectedRecords: [], // Stores IDs of currently selected batches
      allRecordsSeleted: false, // Indicates if all records are selected
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
    }
  },
  computed: {
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    // Computes a list of batch IDs from the current `batches` array
    batchIds() {
      return this.batches.map(batch => batch.id)
    },
    // Retrieves the selected project countries from the Vuex store
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    // Constructs a filter object based on selected project countries
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
      return { project_countries: result }
    },
  },
  watch: {
    // Monitors `selectedRecords` to update `allRecordsSeleted` state
    selectedRecords(newValue) {
      if (this.batches.length > 0 && newValue.length === this.batches.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    // Updates `selectedRecords` to remove IDs that no longer exist in `batches`
    batches() {
      this.selectedRecords = this.selectedRecords.filter(id => {
        const index = this.batches.findIndex(doc => doc.id === id)
        return index !== -1
      })
    },
    // Watches `batchIds` for additions/removals and manages WebSocket room subscriptions
    batchIds(newValue, oldValue) {
      const addedBatches = newValue.filter(item => !oldValue.includes(item))
      const removedBatches = oldValue.filter(item => !newValue.includes(item))
      addedBatches.forEach(batchId => {
        WS.joinRoom(`batch_status_tag_${batchId}`)
      })
      removedBatches.forEach(batchId => {
        WS.leaveRoom(`batch_status_tag_${batchId}`)
      })
    },
  },
  created() {
    // Retrieve the last active page from localStorage and set it as the current page.
    const currentPage = localStorage.getItem('nptv-last-active-page')
    if (currentPage) {
      this.currentPage = parseInt(currentPage, 10)
    }
    this.fetchBatches() // Fetches the initial batch data
    this.initialize() // Sets up WebSocket event listeners
  },
  destroyed() {
    // Save the current page to localStorage before the component is destroyed.
    localStorage.setItem('nptv-last-active-page', this.currentPage)
    this.cleanup() // Cleans up WebSocket subscriptions and event listeners
  },
  methods: {
    // Sets up event listeners for WebSocket data updates
    initialize() {
      bus.$on('wsData/batchStatusTag', this.onBatchStatusTag)
    },
    // Removes WebSocket subscriptions and event listeners
    cleanup() {
      this.batchIds.forEach(batchId => {
        WS.leaveRoom(`batch_status_tag_${batchId}`)
      })
      bus.$off('wsData/batchStatusTag', this.onBatchStatusTag)
    },
    pageChanged(page) {
      this.currentPage = page
      this.fetchBatches()
    },
    // Fetches batch data from the API
    fetchBatches() {
      this.loading = true
      const data = {
        ...this.filterBy,
      }
      const params = {
        train_batch_id: this.trainBatch?.id,
        definition_id: this.trainBatch?.profile,
        profile_training: this.isProfileTraining,
        page_size: 100,
        page: this.currentPage,
        extension: this.extensionType === 'all' ? null : this.extensionType,
      }
      axios.post('/batches/filter_list/', data, {
        params,
      })
        .then(res => {
          this.batches = res.data.results // Sets fetched batches
          this.totalRecords = res.data.count
          this.loading = false
        })
        .catch(loadingError => {
          this.loading = false
          this.loadingError = loadingError?.response?.data?.detail || 'Error fetching batches'
        })
    },
    // Formats a date string into "DD/MM/YYYY HH:MM AM/PM" format
    formatedDate(dateString) {
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
    // Sets a single batch ID for deletion
    deleteHandler(id) {
      this.deleteBatches = [id]
    },
    // Sets multiple selected batch IDs for deletion
    deleteMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.deleteBatches = [...this.selectedRecords]
    },
    // Sets multiple selected batch IDs for reprocessing
    reProcessMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.reProcessBatches = [...this.selectedRecords]
    },
    // Toggles selection of all batch records
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.batches.map(doc => doc.id) : []
    },
    // Updates batch status based on WebSocket data
    onBatchStatusTag(data) {
      this.batches.forEach((item, index) => {
        if (item.id === data.batch_id) {
          this.batches[index].status = data.status
        }
      })
    },
    // Emits a timeline ID event for a specific batch
    setTimelineId(batchID) {
      bus.$emit('setTimelineID', batchID)
    },
  },
}
</script>

<style lang="scss" scoped>
.train-batch-details-wrapper {
  border-radius: 5px;
}
.batch-link.disabled {
  pointer-events: none !important;
}
</style>
