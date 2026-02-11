<template>
  <div
    class="email-batch-details-wrapper mb-1 mx-1 mt-50 p-1"
    :class="isDark ? 'dark-bg': 'light-bg'"
  >
    <div
      v-if="loading"
      class="text-center m-1"
    >
      <b-spinner
        variant="primary"
      />
    </div>

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

    <div v-if="!loading && !loadingError">
      <div
        class="d-flex align-items-center justify-content-start mb-50"
      >
        <h5 class="mb-0">
          Batches
        </h5>
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

      <b-table-simple class="custom-table">
        <b-tbody>
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
                v-if="tableColumn.key !== 'select'"
                :key="tableColumn.key"
              >
                {{ tableColumn.label }}
              </b-th>
            </template>
          </b-tr>
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
            <b-td>
              <router-link
                v-if="!['uploading', 'supporting'].includes(batch.mode)"
                :to="{ name: 'batch', params: {transactionType: 'batch', id: emailBatch.id }, query: { 'batch-id': batch.id } }"
                class="font-weight-bold d-block text-nowrap batch-link"
              >
                {{ batch.id }}
              </router-link>
              <!-- emailBatch -->
              <span
                v-else
                class="font-weight-bold d-block text-nowrap text-secondary"
              >
                {{ batch.id }}
              </span>
            </b-td>
            <b-td>{{ batch.type }}</b-td>
            <b-td>{{ batch.extension }}</b-td>
            <b-td>{{ batch.mode }}</b-td>
            <b-td><status-tag :status="batch.status" /></b-td>
            <b-td>{{ batch.confirmation_number }}</b-td>
            <b-td>
              {{ formatedDate(batch.created_at) }}
            </b-td>
            <b-td>
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

      <div
        v-if="!loading && batches.length === 0"
        class="text-center m-1"
      >
        No records found!
      </div>

    </div>

    <delete-batch
      v-if="deleteBatches.length > 0"
      :ids="deleteBatches"
      @modal-closed="deleteBatches = []"
      @deleted="fetchBatches"
    />

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
import StatusTag from '@/components/EmailBatches/StatusTag.vue'
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
  },
  props: {
    emailBatch: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: true,
      loadingError: null,
      batches: [],
      tableColumns: [
        { key: 'select', label: '' },
        { key: 'id', label: 'ID' },
        { key: 'type', label: 'Type' },
        { key: 'extension', label: 'File Extention' },
        { key: 'mode', label: 'Mode' },
        { key: 'status', label: 'Status' },
        { key: 'confirmation_number', label: 'Confirmation No.' },
        { key: 'created_at', label: 'Created At' },
        { key: 'actions', label: 'Actions' },
      ],
      deleteBatches: [],
      reProcessBatches: [],
      selectedRecords: [],
      allRecordsSeleted: false,
      pageLimit: 100,
    }
  },
  computed: {
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    batchIds() {
      return this.batches.map(batch => batch.id)
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
  },
  watch: {
    emailBatch: {
      handler(newBatch) {
        if (newBatch && ['completed', 'failed'].includes(newBatch.status)) {
          this.fetchBatches()
        }
      },
      deep: true,
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
        const index = this.batches.findIndex(doc => doc.id === id)
        return index !== -1
      })
    },
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
    this.fetchBatches()
    this.initialize()
  },
  destroyed() {
    this.cleanup()
  },
  methods: {
    initialize() {
      bus.$on('wsData/batchStatusTag', this.onBatchStatusTag)
    },
    cleanup() {
      this.batchIds.forEach(batchId => {
        WS.leaveRoom(`batch_status_tag_${batchId}`)
      })
      bus.$off('wsData/batchStatusTag', this.onBatchStatusTag)
    },
    fetchBatches() {
      this.loading = true
      const data = {
        ...this.filterBy,
      }
      const params = {
        page_size: this.pageLimit,
        email_batch_id: this.emailBatch.id,
      }
      axios.post('/batches/filter_list/', data, {
        params,
      })
        .then(res => {
          this.batches = res.data.results
          this.loading = false
        })
        .catch(loadingError => {
          this.loading = false
          this.loadingError = loadingError?.response?.data?.detail || 'Error fetching batches'
        })
    },
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
    deleteHandler(id) {
      this.deleteBatches = [id]
    },
    deleteMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.deleteBatches = [...this.selectedRecords]
    },
    reProcessMultipleHandler() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.reProcessBatches = [...this.selectedRecords]
    },
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.batches.map(doc => doc.id) : []
    },
    onBatchStatusTag(data) {
      this.batches.forEach((item, index) => {
        if (item.id === data.batch_id) {
          this.batches[index].status = data.status
        }
      })
    },
    setTimelineId(batchID) {
      bus.$emit('setTimelineID', batchID)
    },
  },
}
</script>

<style lang="scss" scoped>
.email-batch-details-wrapper {
  border-radius: 5px;
}
.batch-link.disabled {
  pointer-events: none !important;
}
</style>
