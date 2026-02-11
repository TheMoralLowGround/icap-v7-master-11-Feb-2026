<template>
  <div>
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

    <b-card
      v-if="!error"
      no-body
      class="mb-0"
    >

      <div class="m-2">

        <b-row>

          <b-col
            cols="12"
            md="5"
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
              <b-dropdown-item
                @click="exportExcelHandler"
              >
                <feather-icon icon="DownloadIcon" />
                <span class="align-middle ml-50">Export to Excel</span>
              </b-dropdown-item>
            </b-dropdown>

            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="uploadEmailBatch = true"
            >
              Upload File
            </b-button>

            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="uploadTransaction = true"
            >
              Upload Transaction
            </b-button>
          </b-col>

          <b-col
            cols="12"
            md="7"
            class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
          >
            <!-- Clear Search button and Search by Linked Batch input, side by side -->
            <div class="d-flex align-items-center mr-2">
              <b-button
                v-if="!noSearches"
                variant="outline-danger"
                size="sm"
                class="mr-1"
                @click="clearSearch"
              >
                Clear Search
              </b-button>
              <b-form
                class="d-flex"
                @submit.prevent="searchSubmitHandler"
              >
                <b-input-group class="input-group-merge">
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

            <!-- Filter, Refresh Rate, and Entries Selection, side by side -->
            <div class="d-flex align-items-center mr-2">
              <feather-icon
                v-b-tooltip.hover
                icon="FilterIcon"
                class="cursor-pointer mr-1"
                size="20"
                title="Filter Email Batches"
                @click.stop="filterEmailBatches = true"
              />

              <label class="mb-0 mr-1">Refresh Rate</label>
              <v-select
                v-model="refreshInterval"
                :options="refreshIntervalOptions"
                :reduce="option => option.value"
                :clearable="false"
                class="refresh-rate-selector d-inline-block mx-50"
              />
            </div>

            <div class="d-flex align-items-center">
              <label class="mb-0 mr-1">Show</label>
              <v-select
                v-model="perPage"
                :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
                :options="perPageOptions"
                :clearable="false"
                class="per-page-selector d-inline-block mx-50"
              />
              <label class="mb-0">entries</label>
            </div>
          </b-col>
        </b-row>
      </div>

      <div class="table-responsive">
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
          <b-thead>
            <b-tr>
              <template
                v-for="tableColumn of tableColumns"
              >
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
          <b-tbody v-if="!loading">
            <template v-for="(batch) of batches">
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
                  <router-link
                    v-if="isVerificationLinkEnabled(batch)"
                    :to="{ name: 'verification', params: { id: batch.id } }"
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
                <b-td class="max-table-col-w">
                  {{ batch.email_from }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ batch.email_subject }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ batch.matched_profile_name }}
                </b-td>
                <b-td class="max-table-col-w">
                  <template v-if="batch.confirmation_numbers.length">
                    <!-- If there's only one confirmation number, display it -->
                    <template v-if="batch.confirmation_numbers.length === 1">
                      {{ batch.confirmation_numbers[0] }}
                    </template>

                    <!-- If there are multiple confirmation numbers -->
                    <template v-else>
                      {{ batch.confirmation_numbers.slice(0, 1).join(', ') }} <!-- Show the first value -->
                      <button
                        class="btn btn-link p-0 m-0 text-decoration-none"
                        @click="showMoreConfirmationNumbers(batch.confirmation_numbers)"
                      >
                        Show More
                      </button>
                    </template>
                  </template>
                  <template v-else>
                    <!-- Show empty text if confirmation_numbers is not defined -->
                  </template>
                </b-td>
                <b-td>
                  <status-tag :status="batch.status" />
                </b-td>
                <b-td>
                  {{ formattedCreatedAt(batch.created_at) }}
                </b-td>
                <b-td>
                  <div class="text-nowrap">
                    <div class="d-inline">
                      <feather-icon
                        v-b-tooltip.hover
                        :icon="expandedRowIds.includes(batch.id) ? 'ChevronDownIcon' : 'ChevronUpIcon'"
                        class="cursor-pointer"
                        size="18"
                        title="View Email Batch Details"
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

                    <b-spinner
                      v-if="!downloadTransaction && downloadingZips.includes(batch.id)"
                      small
                      label="Small Spinner"
                      class="ml-1"
                    />
                    <!-- <feather-icon
                      v-else
                      v-b-tooltip.hover
                      title="Download Email Batch (Zip)"
                      icon="DownloadCloudIcon"
                      class="cursor-pointer ml-1"
                      size="18"
                      @click.stop="downloadZip(batch.id)"
                    /> -->

                    <b-spinner
                      v-if="downloadTransaction && downloadingZips.includes(batch.id)"
                      small
                      label="Small Spinner"
                      class="ml-1"
                    />
                    <feather-icon
                      v-else
                      v-b-tooltip.hover
                      title="Download Transaction (Zip)"
                      icon="DownloadIcon"
                      class="cursor-pointer ml-1"
                      size="18"
                      @click.stop="downloadZip(batch.id, 'Transaction')"
                    />

                    <feather-icon
                      v-if="isAdmin || (!isAdmin && batch.matched_profile_name === '')"
                      v-b-tooltip.hover
                      icon="TrashIcon"
                      class="ml-1 cursor-pointer"
                      size="18"
                      title="Delete Email Batch"
                      @click="deleteHandler(batch.id)"
                    />
                  </div>
                </b-td>
              </b-tr>

              <b-tr
                v-if="expandedRowIds.includes(batch.id)"
                :key="`detail-row-${batch.id}`"
                class="p-0 m-0"
              >
                <b-td
                  colspan="12"
                  class="p-0 m-0"
                >
                  <email-batch-details
                    :email-batch="batch"
                  />
                </b-td>
              </b-tr>
            </template>

          </b-tbody>
        </b-table-simple>
      </div>

      <div
        v-if="loading"
        class="text-center m-3 table-busy-spinner"
      >
        <b-spinner
          variant="primary"
        />
      </div>

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

    <delete-email-batch
      v-if="deleteBatches.length > 0"
      :ids="deleteBatches"
      @modal-closed="deleteBatches = []"
      @deleted="fetchBatches"
    />

    <re-process-email-batch
      v-if="reProcessBatches.length > 0"
      :ids="reProcessBatches"
      @modal-closed="reProcessBatches = []"
      @completed="fetchBatches"
    />

    <export-to-excel-email-batch
      v-if="exportToExcelEmailBatch"
      :ids="exportExcelBatches"
      :total-records="totalRecords"
      :page="currentPage"
      :sort-by="sortBy"
      :sort-desc="sortDesc"
      :search-by="searchBy"
      :filter-by="filterBy"
      @modal-closed="resetExportValues"
      @completed="fetchBatches"
    />

    <!-- <upload-email-batch
      v-if="uploadEmailBatch"
      @modal-closed="uploadEmailBatch = false"
      @uploaded="fetchBatches"
    /> -->

    <upload-file
      v-if="uploadEmailBatch"
      @modal-closed="uploadEmailBatch = false"
      @uploaded="fetchBatches"
    />

    <upload-zip
      v-if="uploadTransaction === true"
      title="Upload Transaction"
      label="Zip File (.zip):"
      api-endpoint="/pipeline/upload_transaction/"
      replace
      @uploaded="fetchBatches"
      @modal-closed="uploadTransaction = false"
    />

    <filter-options
      v-if="filterEmailBatches"
      @modal-closed="filterEmailBatches = false"
    />

    <confirm-clear-searches
      v-if="clearSearches"
      v-model="searchBy"
      @submited="fetchBatches"
      @modal-closed="clearSearches = false"
    />
    <b-modal
      v-model="showConfirmationNumbersModal"
      centered
      title="Confirmation Numbers"
    >
      <b-card-text>
        <div style="max-height: 200px; overflow-y: auto; white-space: pre-wrap;">
          <ul>
            <li
              v-for="(number, index) in confirmationNumbers"
              :key="index"
            >
              {{ number }}
            </li>
          </ul>
        </div>
      </b-card-text>

      <template #modal-footer="{ cancel }">
        <b-button
          variant="secondary"
          @click="cancel"
        >
          Close
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>

import axios from 'axios'
import {
  BCard, BRow, BCol, BSpinner, BAlert, BFormCheckbox, BDropdown, BDropdownItem, BForm, BFormInput,
  BTableSimple, BThead, BTr, BTbody, BTh, BTd, VBTooltip, BButton, BInputGroup, BInputGroupText, BModal, BCardText,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import WS from '@/utils/ws'
import bus from '@/bus'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import UploadZip from '@/components/UI/UploadZip.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import FilterOptions from '@/components/UI/FilterOptions.vue'
import ConfirmClearSearches from '@/components/UI/ConfirmClearSearches.vue'
import DeleteEmailBatch from '@/components/EmailBatches/DeleteEmailBatch.vue'
import ReProcessEmailBatch from '@/components/EmailBatches/ReProcessEmailBatch.vue'
import ExportToExcelEmailBatch from '@/components/EmailBatches/ExportToExcelEmailBatch.vue'
import Timeline from '@/components/UI/Timeline/Timeline.vue'
import EmailBatchDetails from '@/components/EmailBatches/EmailBatchDetails.vue'
// import UploadEmailBatch from '@/components/EmailBatches/UploadEmailBatch.vue'
import StatusTag from '@/components/EmailBatches/StatusTag.vue'
import UploadFile from './UploadFile.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
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
    DeleteEmailBatch,
    ReProcessEmailBatch,
    Timeline,
    BTableSimple,
    BThead,
    BTr,
    BTbody,
    BTh,
    BTd,
    DetailedPagination,
    UploadZip,
    FilterOptions,
    ConfirmClearSearches,
    EmailBatchDetails,
    BButton,
    // UploadEmailBatch,
    UploadFile,
    StatusTag,
    ExportToExcelEmailBatch,
    BInputGroup,
    BInputGroupText,
    BModal,
    BCardText,
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
      tableColumns: [
        { key: 'select', label: '', width: 1 },
        {
          key: 'id', label: 'ID', sortable: true, customSearch: true, width: 8,
        },
        {
          key: 'email_from', label: 'Source', sortable: true, customSearch: true, width: 17,
        },
        {
          key: 'email_subject', label: 'Description', sortable: true, customSearch: true, width: 20,
        },
        {
          key: 'matched_profile_name', label: 'Matched Process', sortable: true, customSearch: true, width: 25,
        },
        {
          key: 'confirmation_number', label: 'Confirmation Numbers', customSearch: true, width: 15,
        },
        {
          key: 'status', label: 'Status', sortable: true, customSearch: true, width: 7,
        },
        {
          key: 'created_at', label: 'Created At', sortable: true, width: 8,
        },
        { key: 'actions', label: 'Actions', width: 6 },
      ],
      deleteBatches: [],
      reProcessBatches: [],
      exportExcelBatches: [],
      selectedRecords: [],
      allRecordsSeleted: false,
      sortBy: 'created_at',
      sortDesc: true,
      initialized: false,
      searchBy: {
        id: null,
        email_from: null,
        email_subject: null,
        matched_profile_name: null,
        confirmation_number: null,
        status: null,
        linked_batch_id: null,
      },
      downloadingZips: [],
      expandedRowIds: [],
      uploadEmailBatch: false,
      exportToExcelEmailBatch: false,
      uploadTransaction: false,
      refreshIntervalOptions: [
        { label: '---', value: 0 },
        { label: '10 sec', value: 10 },
        { label: '20 sec', value: 20 },
        { label: '30 sec', value: 30 },
        { label: '1 min', value: 60 },
      ],
      refreshInterval: 0,
      clearInterval: null,
      filterEmailBatches: false,
      reFetchEmailBatches: false,
      downloadTransaction: false,
      clearSearches: false,
      showConfirmationNumbersModal: false,
      confirmationNumbers: null,
    }
  },
  computed: {
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    batchIds() {
      return this.batches.map(batch => batch.id)
    },
    stickyFilters() {
      return {
        searchBy: this.searchBy,
        perPage: this.perPage,
      }
    },
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
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
    noSearches() {
      return Object.values(this.searchBy).every(value => value === null || value === '')
    },
    isVerificationLinkEnabled() {
      return batch => {
        if (batch.status === 'waiting' || ['ready', 'submitted'].includes(batch.verification_status)) {
          return true
        }

        if (batch.verification_status === 'disabled') {
          return false
        }

        return !!batch.assembly_triggered
      }
    },
  },
  watch: {
    perPage() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchBatches()
      }
    },
    selectedRecords(newValue) {
      if (this.batches.length > 0 && newValue.length === this.batches.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
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
    stickyFilters: {
      handler() {
        localStorage.setItem('email-batches-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true,
    },
    batchIds(newValue, oldValue) {
      const addedBatches = newValue.filter(item => !oldValue.includes(item))
      const removedBatches = oldValue.filter(item => !newValue.includes(item))
      addedBatches.forEach(batchId => {
        WS.joinRoom(`email_batch_status_tag_${batchId}`)
      })
      removedBatches.forEach(batchId => {
        WS.leaveRoom(`email_batch_status_tag_${batchId}`)
      })
    },
    refreshInterval(newVal, oldVal) {
      if (newVal === oldVal) {
        return
      }

      this.autoDataRefresh()
    },
    filterBy() {
      if (!this.loading) {
        this.fetchBatches()
      } else {
        this.reFetchEmailBatches = true
      }
    },
    loading(newVal) {
      if (!newVal && this.reFetchEmailBatches) {
        this.reFetchEmailBatches = false
        this.fetchBatches()
      }
    },

  },
  created() {
    localStorage.setItem('batch-type', 'email')
    const currentPage = localStorage.getItem('email-batches-last-active-page')

    if (currentPage) {
      this.currentPage = parseInt(currentPage, 10)
    }

    const batchesFilterData = localStorage.getItem('email-batches-filter')
    if (batchesFilterData) {
      const batchesFilter = JSON.parse(batchesFilterData)
      if (batchesFilter.searchBy) {
        this.searchBy = batchesFilter.searchBy
      }
      if (batchesFilter.perPage) {
        this.perPage = batchesFilter.perPage
      }
    }
    this.$nextTick(() => {
      this.initialized = true
    })

    this.fetchBatches()
    this.initialize()
    this.autoDataRefresh()
  },
  destroyed() {
    localStorage.setItem('email-batches-last-active-page', this.currentPage)
    this.cleanup()
  },
  methods: {
    initialize() {
      bus.$on('wsData/emailBatchStatusTag', this.onEmailBatchStatusTag)
    },

    cleanup() {
      this.batchIds.forEach(batchId => {
        WS.leaveRoom(`email_batch_status_tag_${batchId}`)
      })
      bus.$off('wsData/emailBatchStatusTag', this.onEmailBatchStatusTag)

      clearInterval(this.clearInterval)
    },
    pageChanged(page) {
      this.currentPage = page
      this.fetchBatches()
    },
    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchBatches()
    },
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchBatches()
    },
    clearSearch() {
      this.searchBy = Object.fromEntries(
        Object.keys(this.searchBy).map(key => [key, null]),
      )
      this.expandedRowIds = []
      this.fetchBatches()
    },
    fetchBatches() {
      this.loading = true
      const data = {
        ...this.filterBy,
      }

      this.searchBy.linked_batch_id = this.searchBy.linked_batch_id ? this.searchBy.linked_batch_id.trim() : null

      const params = {
        page_size: this.perPage,
        page: this.currentPage,
        sort_by: this.sortBy,
        sort_desc: this.sortDesc,
        ...this.searchBy,
      }
      axios.post('/email-batches/filter_list/', data, {
        params,
      })
        .then(res => {
          this.batches = res.data.results
          this.totalRecords = res.data.count
          this.loading = false
          if (res.data.results.length === 1 && this.searchBy.linked_batch_id) {
            if (!this.expandedRowIds.includes(res.data.results[0].id)) {
              this.toggleRowDetails(res.data.results[0].id)
            }
          } else {
            this.expandedRowIds = []
          }
        })
        .catch(error => {
          this.loading = false
          const errorResponse = error?.response
          if (errorResponse && errorResponse.status === 404 && this.currentPage > 1) {
            this.currentPage -= 1
            this.fetchBatches()
          } else {
            this.error = error?.response?.data?.detail || ' Error fetching email batches'
          }
        })
    },
    formattedCreatedAt(dateString) {
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
    deleteHandler(id) {
      this.deleteBatches = [id]
    },
    deleteMultipleHandler() {
      this.deleteBatches = [...this.selectedRecords]
    },
    reProcessMultipleHandler() {
      this.reProcessBatches = [...this.selectedRecords]
    },
    exportExcelHandler() {
      this.exportToExcelEmailBatch = true
      this.exportExcelBatches = [...this.selectedRecords]
    },
    resetExportValues() {
      this.exportExcelBatches = []
      this.exportToExcelEmailBatch = false
    },
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.batches.map(doc => doc.id) : []
    },
    downloadZip(batchId, type = 'emailBatch') {
      let apiEndpoint = '/pipeline/download_email_batch/'

      if (type === 'Transaction') {
        this.downloadTransaction = true

        apiEndpoint = '/pipeline/download_transaction/'
      }

      this.downloadingZips.push(batchId)

      axios.get(apiEndpoint, {
        params: {
          email_batch_id: batchId,
        },
        responseType: 'blob',
      }).then(response => {
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${batchId}.zip`)
        document.body.appendChild(link)
        link.click()

        this.downloadingZips = this.downloadingZips.filter(itemId => itemId !== batchId)

        if (type === 'Transaction') {
          this.downloadTransaction = false
        }
      }).catch(async error => {
        // convert blob response to json
        let responseDataJSON = null
        if (error?.response?.data) {
          const responseData = await error?.response?.data.text()
          responseDataJSON = JSON.parse(responseData)
        }

        const message = responseDataJSON?.detail || 'Error downlaoding batch'
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
    toggleRowDetails(id) {
      const index = this.expandedRowIds.indexOf(id)
      if (index > -1) {
        this.expandedRowIds.splice(index, 1)
      } else {
        this.expandedRowIds.push(id)
      }
    },
    onEmailBatchStatusTag(data) {
      this.batches.forEach((item, index) => {
        if (item.id === data.batch_id) {
          this.batches[index].status = data.status
        }
      })
    },
    autoDataRefresh() {
      clearInterval(this.clearInterval)

      if (!this.refreshInterval) {
        return
      }

      this.clearInterval = setInterval(() => {
        this.fetchBatches()
      }, this.refreshInterval * 1000)
    },
    handleShowDetailsChange(showDetails) {
      if (showDetails) {
        clearInterval(this.clearInterval)

        return
      }

      this.autoDataRefresh()
    },
    setTimelineId(batchID) {
      bus.$emit('setTimelineID', batchID)
    },
    showMoreConfirmationNumbers(confirmationNumbers) {
      // Show the rest of the values in a modal, alert, or console for now
      this.showConfirmationNumbersModal = true
      this.confirmationNumbers = confirmationNumbers
    },
  },
}
</script>

<style lang="scss" scoped>
.hover {
  transition: opacity 0.5s ease;
  opacity: 1;
  cursor: pointer;
}
.hover:hover {
  opacity: 0.5;
}
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

.table-responsive {
  overflow-x: auto;
  white-space: normal;
}

</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
