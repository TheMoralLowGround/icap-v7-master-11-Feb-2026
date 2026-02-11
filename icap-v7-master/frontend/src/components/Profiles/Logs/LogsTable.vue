<template>
  <div>
    <b-card
      no-body
      class="mb-0"
    >
      <!-- <b-col
        cols="12"
        md="6"
        class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
      >
        <label>Show</label>
        <v-select
          v-model="perPage"
          :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
          :options="perPageOptions"
          :clearable="false"
          class="per-page-selector d-inline-block mx-50"
        />
        <label>entries</label>
      </b-col> -->
      <b-table-simple
        :class="{
          'table-busy': loading
        }"
        class="process-logs-table"
        responsive
      >
        <b-thead>
          <!-- Header Row with Column Names and Sorting -->
          <b-tr>
            <template v-for="tableColumn of tableColumns">
              <b-th
                v-if="tableColumn.sortable"
                :key="tableColumn.key"
                :aria-sort="sortBy === tableColumn.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                @click="sortColumn(tableColumn.key)"
              >
                {{ tableColumn.label }}
              </b-th>

              <b-th
                v-if="!tableColumn.sortable"
                :key="tableColumn.key"
              >
                {{ tableColumn.label }}
              </b-th>
            </template>
          </b-tr>

          <!-- Search Row -->
          <b-tr>
            <template v-for="tableColumn of tableColumns">
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

        <b-tbody v-if="!loading">
          <b-tr
            v-for="(log, logIndex) of processLogs"
            :key="logIndex"
          >
            <!-- ID Column -->
            <!-- <b-td>
              <span class="font-weight-bold">{{ log.id }}</span>
            </b-td> -->

            <!-- Updated By Column -->
            <b-td>
              <div class="d-flex align-items-center">
                <b-avatar
                  :text="log.user && log.user.username ? log.user.username.charAt(0).toUpperCase() : 'U'"
                  size="sm"
                  variant="light-primary"
                  class="mr-1"
                />
                {{ log.user.username || '-' }}
              </div>
            </b-td>

            <!-- Change Type Column -->
            <b-td>
              {{ log.change_category }}
            </b-td>

            <!-- Status Column -->
            <b-td>
              <b-badge
                v-if="log.action"
                :variant="getStatusVariant(log.action)"
                class="text-capitalize"
              >
                {{ log.action }}
              </b-badge>
            </b-td>

            <!-- Updated At Column -->
            <b-td>
              {{ formatedDate(log.updated_at) }}
            </b-td>

            <!-- Actions Column -->
            <b-td>
              <div class="text-nowrap">
                <!-- Download Icon -->
                <feather-icon
                  v-b-tooltip.hover
                  icon="DownloadIcon"
                  size="18"
                  class="cursor-pointer mr-2"
                  title="Download Process Log"
                  @click.stop="showDownloadConfirm(log)"
                />

                <!-- Revert Icon -->
                <feather-icon
                  v-if="!log.revert"
                  v-b-tooltip.hover
                  icon="RotateCcwIcon"
                  size="18"
                  class="cursor-pointer"
                  title="Revert Process"
                  @click.stop="showRevertConfirm(log)"
                />
                <feather-icon
                  v-else
                  v-b-tooltip.hover
                  icon="CheckIcon"
                  size="18"
                  class="text-muted"
                  title="Already Reverted"
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
        <b-spinner variant="primary" />
      </div>

      <div
        v-if="!loading && processLogs.length === 0"
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
          :local-records="processLogs.length"
          @page-changed="pageChanged"
        />
      </div>
    </b-card>

    <!-- Revert Confirm Dialog -->
    <RevertConfirmDialog
      v-if="showRevertDialog && changeLogId"
      :id="changeLogId"
      :visible="showRevertDialog"
      title="Confirm Revert"
      ok-title="Revert"
      ok-variant="primary"
      icon="AlertTriangleIcon"
      icon-class="text-primary"
      :change-type="changeType"
      @confirm="handleRevertConfirm"
      @close="closeRevertDialog"
    />

    <!-- Download Confirm Dialog -->
    <DownloadConfirmDialog
      v-if="showDownloadDialog && changeLogId"
      :id="changeLogId"
      :visible="showDownloadDialog"
      title="Download Logs"
      ok-title="Download"
      ok-variant="primary"
      icon="DownloadIcon"
      icon-class="text-primary"
      :change-type="changeType"
      @confirm="handleDownloadConfirm"
      @close="closeDownloadDialog"
    />
  </div>
</template>

<script>
import {
  BAvatar,
  BBadge,
  BCard,
  BForm,
  BFormInput,
  BSpinner,
  BTableSimple,
  BTbody,
  BTd,
  BTh,
  BThead,
  BTr,
  VBTooltip,
  // BAlert,
} from 'bootstrap-vue'

import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
// import vSelect from 'vue-select'
import RevertConfirmDialog from './RevertConfirmDialog.vue'
import DownloadConfirmDialog from './DownloadConfirmDialog.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BAvatar,
    BBadge,
    BCard,
    BForm,
    BFormInput,
    BSpinner,
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTbody,
    BTd,
    // BAlert,
    RevertConfirmDialog,
    DownloadConfirmDialog,
    DetailedPagination,
    // vSelect,
  },
  data() {
    return {
      changeLogId: null,
      processLogs: [],
      loading: true,
      loadingError: null,
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      sortBy: 'updated_at',
      sortDesc: true,
      searchBy: {
        // id: null,
        user: null,
        change_category: null,
        action: null,
      },
      showRevertDialog: false,
      showDownloadDialog: false,
      selectedLog: null,
      changeType: '',
      tableColumns: [
        // {
        //   key: 'id',
        //   label: 'ID',
        //   sortable: true,
        //   customSearch: true,
        // },
        {
          key: 'user',
          label: 'Updated By',
          sortable: true,
          customSearch: true,
        },
        {
          key: 'change_category',
          label: 'Change Type',
          sortable: true,
          customSearch: true,
        },
        {
          key: 'action',
          label: 'Status',
          sortable: true,
          customSearch: true,
        },
        {
          key: 'updated_at',
          label: 'Updated At',
          sortable: true,
        },
        {
          key: 'actions',
          label: 'Actions',
        },
      ],
    }
  },
  computed: {
    profileId() {
      return this.$route.params.id
    },
  },
  watch: {
    perPage() {
      this.currentPage = 1
      this.fetchProcessLogs()
    },
  },
  created() {
    this.fetchProcessLogs()
  },
  methods: {
    async fetchProcessLogs() {
      if (!this.profileId) {
        this.processLogs = []
        this.totalRecords = 0
        this.loading = false
        this.loadingError = 'No logs available'
        return
      }
      this.loading = true
      this.loadingError = null
      try {
        const params = {
          module: 'PROFILE',
          module_id: this.profileId,
          page_size: this.perPage,
          page: this.currentPage,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
          username: this.searchBy.user,
          change_category: this.searchBy.change_category,
          action: this.searchBy.action,
          // ...this.searchBy,
        }
        // Remove undefined or null values from params
        // Object.keys(params).forEach(key => params[key] == null && delete params[key])

        const res = await axios.get('/changelogs/', { params })

        this.processLogs = res.data.results || []
        this.totalRecords = res.data.count || 0
        this.loading = false
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching logs'
        this.loading = false

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error',
            text: this.loadingError,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    },

    sortColumn(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchProcessLogs()
    },

    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchProcessLogs()
    },

    pageChanged(page) {
      this.currentPage = page
      this.fetchProcessLogs()
    },

    formatedDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      const datePart = date.toLocaleDateString('en-GB')
      const timePart = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      })
      return `${datePart} ${timePart}`
    },

    getStatusVariant(action) {
      const variants = {
        created: 'success',
        updated: 'info',
        update: 'info',
        deleted: 'danger',
        pending: 'warning',
      }
      return variants[String(action).toLowerCase()] || 'secondary'
    },

    showRevertConfirm(log) {
      this.selectedLog = log
      this.showRevertDialog = true
      this.changeLogId = log.id
      this.changeType = log.change_category
    },

    showDownloadConfirm(log) {
      this.selectedLog = log
      this.showDownloadDialog = true
      this.changeLogId = log.id
      this.changeType = log.change_category
    },

    handleRevertConfirm() {
      // Implement revert logic here
      this.closeRevertDialog()
      this.changeLogId = null
      this.changeType = ''
      window.location.reload()
    },

    handleDownloadConfirm() {
      // Implement download logic here
      this.closeDownloadDialog()
      this.changeLogId = null
    },

    closeRevertDialog() {
      this.showRevertDialog = false
      this.selectedLog = null
      this.changeLogId = null
      this.changeType = ''
    },

    closeDownloadDialog() {
      this.showDownloadDialog = false
      this.selectedLog = null
      this.changeLogId = null
      this.changeType = ''
    },
  },
}
</script>
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
