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
            md="6"
            class="d-flex align-items-center justify-content-start mb-1 mb-md-0"
          >
            <b-dropdown
              v-if="false"
              text="Actions"
              variant="primary"
            >
              <b-dropdown-item
                :disabled="selectedRecords.length === 0"
                @click="deleteMultipleHandler"
              >
                <feather-icon icon="TrashIcon" />
                <span class="align-middle ml-50">Multiple Delete</span>
              </b-dropdown-item>
              <b-dropdown-item
                :disabled="selectedRecords.length === 0"
                @click="exportTemplates('templates')"
              >
                <feather-icon icon="RefreshCwIcon" />
                <span class="align-middle ml-50">Export Templates</span>
              </b-dropdown-item>
              <b-dropdown-item
                @click="uploadEmailBatch = true"
              >
                <feather-icon icon="RefreshCwIcon" />
                <span class="align-middle ml-50">Import Templates</span>
              </b-dropdown-item>
            </b-dropdown>
            <b-button
              variant="primary"
              class="ml-1"
              @click="createTemplate"
            >
              Create Template
            </b-button>
            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="uploadEmailBatch = true"
            >
              Import Templates
            </b-button>
            <b-button
              variant="outline-primary"
              :disabled="selectedRecords.length === 0"
              class="ml-1"
              @click="exportTemplates('Templates')"
            >
              Export Templates
            </b-button>
            <b-button
              :disabled="exportingAllTemplates || !templates.length"
              variant="outline-primary"
              class="ml-1"
              @click="exportsAllModal"
            >
              Export All
              <b-spinner
                v-if="exportingAllTemplates"
                small
                label="Small Spinner"
              />
            </b-button>
          </b-col>

          <b-col
            cols="12"
            md="6"
            class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
          >
            <div class="mr-1">
              <label>Refresh Rate</label>
              <v-select
                v-model="refreshInterval"
                :options="refreshIntervalOptions"
                :reduce="option => option.value"
                :clearable="false"
                class="refresh-rate-selector d-inline-block mx-50"
              />
            </div>
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
                  :disabled="templates.length === 0"
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
          <template v-for="(item) of templates">
            <b-tr
              :key="`main-row-${item.id}`"
              :class="{
                'has-row-details': expandedRowIds.includes(item.id)
              }"
            >
              <b-td>
                <b-form-checkbox
                  v-model="selectedRecords"
                  :value="item"
                />
              </b-td>
              <b-td>
                {{ item.template_name }}
              </b-td>
              <b-td>
                {{ item.project }}
              </b-td>
              <b-td>
                {{ item.doc_type }}
              </b-td>
              <b-td class="text-center">
                {{ item.created_by }}
              </b-td>
              <b-td class="text-center">
                {{ item.linked_profiles || 0 }}
              </b-td>
              <b-td class="text-center">
                {{ item.file_type }}
              </b-td>
              <b-td class="text-center">
                {{ item.ocr_engine }}
              </b-td>
              <b-td>
                <chip
                  :variant="item.barcode? 'success': 'secondary'"
                >
                  {{ item.barcode }}
                </chip>
              </b-td>
              <b-td>
                <chip
                  :variant="item.page_rotate? 'success': 'secondary'"
                >
                  {{ item.page_rotate }}
                </chip>
              </b-td>
              <b-td>
                {{ formatedDate(item.created_at) }}
              </b-td>
              <b-td>
                <div class="text-nowrap">
                  <feather-icon
                    v-b-tooltip.hover
                    :icon="expandedRowIds.includes(item.id) ? 'ChevronDownIcon' : 'ChevronUpIcon'"
                    class="cursor-pointer"
                    size="18"
                    title="View Template Details"
                    @click="toggleRowDetails(item.id)"
                  />
                  <div
                    class="d-inline"
                    @click="setTimelineId(item.template_name)"
                  >
                    <TimelineTemplate
                      :batch-id="item.template_name"
                      :icon-size="'18'"
                      class="ml-1"
                      @show-details-change="handleShowDetailsChange"
                    />
                  </div>
                  <feather-icon
                    v-b-tooltip.hover
                    title="Upload Document"
                    icon="UploadIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    @click="handleActions(item, 'upload')"
                  />
                  <feather-icon
                    v-if="exportSystemName"
                    v-b-tooltip.hover
                    icon="SendIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    title="Send Template"
                    @click="handleActions(item, 'send')"
                  />
                  <feather-icon
                    v-if="!exportingTemplateIds.includes(item.id)"
                    v-b-tooltip.hover
                    title="Export Template"
                    icon="DownloadIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    @click="exportSingleTemplate(item, item.template_name)"
                  />
                  <b-spinner
                    v-if="exportingTemplateIds.includes(item.id)"
                    class="ml-1"
                    small
                    label="Small Spinner"
                  />
                  <b-spinner
                    v-if="downloadingZips.includes(item.id)"
                    small
                    label="Small Spinner"
                    class="ml-1"
                  />
                  <feather-icon
                    v-b-tooltip.hover
                    title="Edit Template"
                    icon="EditIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    @click="editTemplate(item.id)"
                  />
                  <feather-icon
                    v-b-tooltip.hover
                    title="Clone Template"
                    icon="CopyIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    @click="handleActions(item, 'clone')"
                  />
                  <feather-icon
                    v-b-tooltip.hover
                    icon="TrashIcon"
                    class="cursor-pointer ml-1"
                    size="18"
                    title="Delete Template"
                    @click="deleteHandler(item)"
                  />
                </div>
              </b-td>
            </b-tr>

            <b-tr
              v-if="expandedRowIds.includes(item.id)"
              :key="`detail-row-${item.id}`"
              class="p-0 m-0"
            >
              <b-td
                colspan="12"
                class="p-0 m-0"
              >
                <TemplateBatchDetails :template="item" />
              </b-td>
            </b-tr>
          </template>

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

      <div
        v-if="!loading && templates.length === 0"
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
          :local-records="templates.length"
          @page-changed="pageChanged"
        />
      </div>
    </b-card>
    <DeleteTemplateBatch
      v-if="deleteTempleteIds.length"
      :list="deleteTempleteIds"
      @modal-closed="deleteTempleteIds = []"
      @deleted="fetchTemplates"
    />
    <clone-template
      v-if="cloneTemplate"
      :template="cloneTemplate"
      @modal-closed="cloneTemplate = false"
      @cloned="fetchTemplates"
    />
    <train-template
      v-if="trainTemplate"
      :template="trainTemplate"
      @modal-closed="trainTemplate = null"
    />
    <UploadTemplates
      v-if="uploadEmailBatch"
      @modal-closed="uploadEmailBatch = false"
      @uploaded="fetchTemplates"
    />
    <send-template
      v-if="sendTemplate"
      :template="sendTemplate"
      :export-system-name="exportSystemName"
      @modal-closed="sendTemplate = null"
    />
    <b-modal
      v-model="showExportsAllModal"
      centered
      title="Export All Templates"
      @ok="exportAllTemplates"
    >
      <b-card-text>
        <div>
          Are you sure you want to export <span class="text-primary">{{ totalRecords }}</span> templates?
        </div>
      </b-card-text>

      <template #modal-footer="{ ok, cancel }">
        <b-button
          variant="secondary"
          @click="cancel()"
        >
          Cancel
        </b-button>
        <b-button
          variant="primary"
          :disabled="exportingAllTemplates"
          @click="ok()"
        >
          Export
          <b-spinner
            v-if="exportingAllTemplates"
            small
            label="Small Spinner"
          />
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>

import axios from 'axios'
import {
  BCardText, BCard, BRow, BCol, BSpinner, BAlert, BFormCheckbox, BForm, BFormInput,
  BTableSimple, BThead, BTr, BTbody, BTh, BTd, VBTooltip, BButton, BDropdown, BDropdownItem, BModal,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import WS from '@/utils/ws'
import bus from '@/bus'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import DeleteTemplateBatch from '@/components/Template/DeleteTemplateBatch.vue'
import TimelineTemplate from '@/components/Template/TimelineTemplate.vue'
import TemplateBatchDetails from '@/components/Template/TemplateBatchDetails.vue'
import UploadTemplates from '@/components/Template/UploadTemplates.vue'
import CloneTemplate from '@/components/Template/CloneTemplate.vue'
import TrainTemplate from '@/components/Template/TrainTemplate.vue'
import Chip from '@/components/UI/Chip.vue'
import exportFromJSON from 'export-from-json'
import SendTemplate from './SendTemplate.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BCardText,
    BCard,
    BRow,
    BCol,
    BSpinner,
    BAlert,
    BFormCheckbox,
    BForm,
    BFormInput,
    vSelect,
    DeleteTemplateBatch,
    TimelineTemplate,
    BTableSimple,
    BThead,
    BTr,
    BTbody,
    BTh,
    BTd,
    DetailedPagination,
    TemplateBatchDetails,
    UploadTemplates,
    CloneTemplate,
    BButton,
    TrainTemplate,
    Chip,
    BDropdown,
    BDropdownItem,
    SendTemplate,
    BModal,
  },
  data() {
    return {
      loading: true,
      error: null,
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      templates: [],
      tableColumns: [
        { key: 'select', label: '', width: 1 },
        {
          key: 'template_name', label: 'Name', sortable: true, customSearch: true, width: 21,
        },
        {
          key: 'project', label: 'Project', sortable: true, customSearch: true, width: 12,
        },
        {
          key: 'doc_type', label: 'Document Type', sortable: true, customSearch: true, width: 10,
        },
        {
          key: 'created_by', label: 'Created By', width: 5,
        },
        {
          key: 'linked_profiles', label: 'Profile Count', sortable: true, width: 5,
        },
        {
          key: 'file_type', label: 'File Type', width: 5,
        },
        {
          key: 'ocr_engine', label: 'OCR Engine', width: 5,
        },
        {
          key: 'barcode', label: 'Barcode', width: 5,
        },
        {
          key: 'page_rotate', label: 'Page Rotate', width: 6,
        },
        {
          key: 'created_at', label: 'Created At', sortable: true, width: 8,
        },
        { key: 'actions', label: 'Actions', width: 8 },
      ],
      deleteTempleteIds: [],
      selectedRecords: [],
      exportingTemplateIds: [],
      allRecordsSeleted: false,
      sortBy: 'created_at',
      sortDesc: true,
      initialized: false,
      searchBy: {
        id: null,
        email_from: null,
        email_subject: null,
        matched_profile_name: null,
        status: null,
      },
      downloadingZips: [],
      expandedRowIds: [],
      uploadEmailBatch: false,
      refreshIntervalOptions: [
        { label: '---', value: 0 },
        { label: '10 sec', value: 10 },
        { label: '20 sec', value: 20 },
        { label: '30 sec', value: 30 },
        { label: '1 min', value: 60 },
      ],
      refreshInterval: 0,
      clearInterval: null,
      trainTemplate: null,
      cloneTemplate: false,
      exportSystemName: null,
      sendTemplate: null,
      exportingAllTemplates: false,
      showExportsAllModal: false,
      showModal: false,
    }
  },
  computed: {
    templateNames() {
      return this.templates.map(template => template.template_name)
    },
    stickyFilters() {
      return {
        searchBy: this.searchBy,
        perPage: this.perPage,
      }
    },
  },
  watch: {
    perPage() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchTemplates()
      }
    },
    selectedRecords(newValue) {
      if (this.templates.length > 0 && newValue.length === this.templates.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    templates() {
      this.selectedRecords = this.selectedRecords.filter(item => {
        const index = this.templates.findIndex(template => template.id === item.id)
        return index !== -1
      })

      this.expandedRowIds = this.expandedRowIds.filter(id => {
        const index = this.templates.findIndex(template => template.id === id)
        return index !== -1
      })
    },
    stickyFilters: {
      handler() {
        localStorage.setItem('email-batches-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true,
    },
    templateNames(newValue, oldValue) {
      const addedBatches = newValue.filter(item => !oldValue.includes(item))
      const removedBatches = oldValue.filter(item => !newValue.includes(item))
      addedBatches.forEach(templatename => {
        const modifiedName = this.convertGroupName(templatename)
        WS.joinRoom(`template_batch_status_tag_${modifiedName}`)
      })
      removedBatches.forEach(templatename => {
        const modifiedName = this.convertGroupName(templatename)
        WS.leaveRoom(`template_batch_status_tag_${modifiedName}`)
      })
    },
    refreshInterval(newVal, oldVal) {
      if (newVal === oldVal) {
        return
      }

      this.autoDataRefresh()
    },
  },
  created() {
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

    this.fetchTemplates()
    this.fetchDataExportConfig()
    this.initialize()
    this.autoDataRefresh()
  },
  destroyed() {
    localStorage.setItem('email-batches-last-active-page', this.currentPage)
    this.cleanup()
  },
  methods: {
    initialize() {
      bus.$on('wsData/templateBatchStatusTag', this.onTemplateBatchStatusTag)
    },
    cleanup() {
      this.templateNames.forEach(batchId => {
        WS.leaveRoom(`template_batch_status_tag_${batchId}`)
      })
      bus.$off('wsData/templateBatchStatusTag', this.onTemplateBatchStatusTag)

      clearInterval(this.clearInterval)
    },
    pageChanged(page) {
      this.currentPage = page
      this.fetchTemplates()
    },
    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchTemplates()
    },
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchTemplates()
    },
    fetchTemplates() {
      this.loading = true
      const params = {
        page_size: this.perPage,
        page: this.currentPage,
        sort_by: this.sortBy,
        sort_desc: this.sortDesc,
        ...this.searchBy,
      }
      axios.get('/dashboard/template/', {
        params,
      })
        .then(res => {
          this.templates = res.data.results
          this.totalRecords = res.data.count
          this.loading = false
        })
        .catch(error => {
          this.loading = false
          const errorResponse = error?.response
          if (errorResponse && errorResponse.status === 404 && this.currentPage > 1) {
            this.currentPage -= 1
            this.fetchTemplates()
          } else {
            this.error = error?.response?.data?.detail || ' Error fetching Template'
          }
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
    deleteHandler(item) {
      this.onHideTimelineModal(true)
      this.deleteTempleteIds.push(item)
    },
    deleteMultipleHandler() {
      this.deleteTempleteIds = [...this.selectedRecords]
    },
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? [...this.templates] : []
    },
    downloadZip(batchId) {
      this.downloadingZips.push(batchId)

      axios.get('/pipeline/download_email_batch/', {
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
      })
    },
    toggleRowDetails(id) {
      if (this.expandedRowIds.includes(id)) {
        this.expandedRowIds = this.expandedRowIds.filter(itemId => itemId !== id)
      } else {
        this.expandedRowIds.push(id)
      }
    },
    onTemplateBatchStatusTag(data) {
      this.templates.forEach((item, index) => {
        if (item.id === data.batch_id) {
          this.templates[index].status = data.status
        }
      })
    },
    autoDataRefresh() {
      clearInterval(this.clearInterval)

      if (!this.refreshInterval) {
        return
      }

      this.clearInterval = setInterval(() => {
        this.fetchTemplates()
      }, this.refreshInterval * 1000)
    },
    handleShowDetailsChange(showDetails) {
      if (showDetails) {
        this.showModal = true
        clearInterval(this.clearInterval)

        return
      }
      this.showModal = false
      this.autoDataRefresh()
    },
    setTimelineId(templateName) {
      bus.$emit('setTimelineID', templateName)
    },
    onHideTimelineModal(hide) {
      bus.$emit('onHideTimelineModal', hide)
    },
    editTemplate(templateId) {
      this.$router.push({ name: 'edit-template', params: { id: templateId } })
    },
    createTemplate() {
      this.$router.push({ name: 'create-template' })
    },
    exportsAllModal() {
      this.showExportsAllModal = true
    },
    exportAllTemplates() {
      this.exportingAllTemplates = true
      this.showExportsAllModal = false
      const payload = {
        ids: [],
        export_all: true,
      }
      const fileName = 'All Templates'
      axios.post('/dashboard/export_templates/', payload)
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
          this.exportingAllTemplates = false
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting templates(s)',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
    },
    exportTemplates(fileName = 'Templates') {
      if (this.selectedRecords.length === 0) {
        return
      }
      const ids = this.selectedRecords.map(item => item.id)
      this.exportingTemplateIds = ids
      axios.post('/dashboard/export_templates/', { ids })
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
          this.selectedRecords = []
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting templates(s)',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        }).finally(() => {
          this.exportingTemplateIds = []
        })
    },
    exportSingleTemplate(item, templateName) {
      this.onHideTimelineModal(true)
      this.selectedRecords = [item]
      this.exportTemplates(`Template-${templateName}`)
    },
    convertGroupName(groupName) {
      const cleanedName = groupName.replace(/[^\w.-]/g, '-')
      return cleanedName
    },
    async fetchDataExportConfig() {
      try {
        const res = await axios.get('/settings/data_export_config/')
        this.exportSystemName = res.data?.export_system_name || null
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching data export config'
        this.loading = false
      }
    },
    handleActions(item, action) {
      if (this.showModal) {
        this.onHideTimelineModal(true)
      }

      if (action === 'upload') {
        this.trainTemplate = item
      } else if (action === 'send') {
        this.sendTemplate = item
      } else if (action === 'clone') {
        this.cloneTemplate = item
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
      padding: 0.6rem 0.8rem;
      vertical-align: baseline;
    }
    th {
      padding: 0.6rem 0.5rem;
    }
    tr.has-row-details {
      border-bottom: hidden;
    }
  }

</style>

<style lang="scss">
  @import '@core/scss/vue/libs/vue-select.scss';
</style>
