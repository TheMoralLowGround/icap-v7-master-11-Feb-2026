<template>
  <b-card
    no-body
  >
    <div class="m-2">
      <b-row>
        <b-col
          cols="12"
          class="d-flex align-items-center"
          style="column-gap: 1.5rem"
        >
          <!-- Action buttons -->
          <div class="mr-auto">
            <b-button
              variant="primary"
              @click="uploadZip = true"
            >
              Upload Zip
            </b-button>
          </div>
          <!-- Searchbox -->
          <div>
            <b-form
              style="width: 13vw"
              @submit.prevent="searchSubmitHandler"
            >
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
                  v-model="search"
                  placeholder="Search"
                />
              </b-input-group>
            </b-form>
          </div>
          <!-- Entries -->
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
        <b-col
          cols="12"
          class="mt-1"
        >
          <b-breadcrumb
            :items="breadcrumbItems"
          />
        </b-col>
      </b-row>
    </div>

    <b-table-simple
      v-if="!loadingError"
      :class="{
        'table-busy': loading
      }"
    >
      <b-thead>
        <b-tr>
          <template
            v-for="tableColumn of tableColumns"
          >
            <b-th
              v-if="tableColumn.sortable"
              :key="tableColumn.key"
              :aria-sort="sortBy === tableColumn.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
              :style="{
                width: tableColumn.width + '%'
              }"
              @click="customSort(tableColumn.key)"
            >
              {{ tableColumn.label }}
            </b-th>

            <b-th
              v-if="!tableColumn.sortable"
              :key="tableColumn.key"
              :style="{
                width: tableColumn.width + '%'
              }"
            >
              {{ tableColumn.label }}
            </b-th>
          </template>
        </b-tr>
      </b-thead>
      <b-tbody v-if="!loading">
        <b-tr
          v-for="(batch) of batches"
          :key="batch.id"
        >
          <b-td>
            <feather-icon
              :icon="batch.is_folder ? 'FolderIcon' : 'FileIcon'"
              size="16"
              class="d-inline-block mr-1"
            />

            <b-link
              v-if="batch.is_folder"
              :to="{ name: 'batches', query: { path: nextPath(currentPath, batch.name) } }"
              class="font-weight-bold d-inline-block text-nowrap batch-link"
            >
              {{ batch.name }}
            </b-link>
            <span v-else>{{ batch.name }}</span>

            <b-badge
              v-if="batch.is_uploaded"
              v-b-tooltip.hover.right
              :title="`Batch uploaded in ${batch.mode} mode`"
              variant="info"
              class="mx-1"
            >
              {{ batch.mode }}
            </b-badge>
          </b-td>
          <b-td>
            {{ formatedDate(batch.date_modified) }}
          </b-td>
          <b-td>
            <template v-if="batch.is_folder">
              <feather-icon
                v-b-tooltip.hover
                title="Upload Batch"
                icon="UploadCloudIcon"
                :class="allowUploadBatch ? 'cursor-pointer mx-50' : 'mx-50 text-muted'"
                size="20"
                @click.stop="allowUploadBatch && (uploadBatchId = batch.name)"
              />

              <b-spinner
                v-if="downloadingZips.includes(batch.name)"
                small
                label="Small Spinner"
                class="mx-50"
              />
              <feather-icon
                v-else
                v-b-tooltip.hover
                title="Download Batch (Zip)"
                icon="DownloadCloudIcon"
                class="cursor-pointer mx-50"
                size="20"
                @click.stop="downloadZip(batch.name)"
              />

            </template>
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

    <div
      v-if="!loading && batches.length === 0"
      class="text-center m-3"
    >
      {{ tableEmptyMessage }}
    </div>

    <b-alert
      variant="danger"
      class="mx-1"
      :show="!loading && loadingError ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <div
      v-if="!loading && !loadingError"
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

    <upload-batch
      v-if="uploadBatchId !== null"
      :batch-id="uploadBatchId"
      :sub-path="currentPath"
      @modal-closed="uploadBatchId = null"
      @uploaded="fetchBatches"
    />

    <upload-zip
      v-if="uploadZip === true"
      :sub-path="currentPath"
      @modal-closed="uploadZip = false"
      @uploaded="fetchBatches"
    />
  </b-card>
</template>

<script>
import axios from 'axios'
import {
  BLink, BBreadcrumb, BCard, BButton, BSpinner, BAlert, VBTooltip, BBadge, BInputGroup, BInputGroupText,
  BForm, BFormInput, BRow, BCol,
  BTableSimple, BThead, BTr, BTbody, BTh, BTd,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import UploadZip from '@/components/UI/UploadZip.vue'
import UploadBatch from './UploadBatch.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BLink,
    BBreadcrumb,
    BCard,
    BButton,
    BSpinner,
    BAlert,
    UploadZip,
    UploadBatch,
    BForm,
    BFormInput,
    BRow,
    BCol,
    vSelect,
    BBadge,
    DetailedPagination,
    BInputGroup,
    BInputGroupText,
    BTableSimple,
    BThead,
    BTr,
    BTbody,
    BTh,
    BTd,
  },
  data() {
    return {
      batches: [],
      tableColumns: [
        {
          key: 'name', label: 'Name', sortable: true, width: 50,
        },
        {
          key: 'date_modified', label: 'Modified At', sortable: true, width: 30,
        },
        {
          key: 'actions', label: 'Actions', width: 20,
        },
      ],
      loading: true,
      loadingError: null,
      uploadBatchId: null,
      uploadZip: false,
      downloadingZips: [],
      search: null,
      currentPage: 1,
      perPage: 10,
      sortBy: 'date_modified',
      sortDesc: true,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      initialized: false,
      developerSettingsLoaded: false,
    }
  },
  computed: {
    currentPath() {
      return this.$route.query?.path || null
    },
    submitedSearch() {
      return this.$route.query?.search || null
    },
    breadcrumbItems() {
      let breadcrumbCurrentPath = null
      const items = [
        {
          text: 'Home',
          to: { name: 'batches' },
        },
      ]

      if (this.currentPath) {
        this.currentPath.split('/').forEach(path => {
          const breadcrumbPath = this.nextPath(breadcrumbCurrentPath, path)
          items.push({
            text: path,
            to: { name: 'batches', query: { path: breadcrumbPath } },
          })
          breadcrumbCurrentPath = breadcrumbPath
        })
      }

      return items
    },
    tableEmptyMessage() {
      if (this.submitedSearch) {
        return 'No matching files found!'
      }
      return 'No files found!'
    },
    stickyFilters() {
      return {
        perPage: this.perPage,
      }
    },
    allowUploadBatch() {
      return this.developerSettingsLoaded && this.$store.getters['developerSettings/allowUploadBatch']
    },
  },
  watch: {
    perPage() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchBatches()
      }
    },
    currentPath() {
      this.currentPage = 1
      this.fetchBatches()
    },
    submitedSearch() {
      this.currentPage = 1
      this.search = this.submitedSearch
      this.fetchBatches()
    },
    stickyFilters: {
      handler() {
        localStorage.setItem('disk-batches-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true,
    },
  },
  created() {
    const batchesFilterData = localStorage.getItem('disk-batches-filter')
    if (batchesFilterData) {
      const batchesFilter = JSON.parse(batchesFilterData)
      if (batchesFilter.perPage) {
        this.perPage = batchesFilter.perPage
      }
    }
    this.search = this.submitedSearch

    this.$nextTick(() => {
      this.initialized = true
    })

    this.fetchBatches()
  },
  async mounted() {
    // Load developer settings to check if batch upload is allowed
    try {
      await this.$store.dispatch('developerSettings/fetchData')
      this.developerSettingsLoaded = true
    } catch (error) {
      // console.error('Error loading developer settings:', error)
      this.developerSettingsLoaded = false
    }
  },
  destroyed() {
    this.developerSettingsLoaded = false
  },
  methods: {
    nextPath(currentPath, path) {
      return currentPath ? `${currentPath}/${path}` : `${path}`
    },
    fetchBatches() {
      this.loading = true
      axios.get('/pipeline/batch_path_content/', {
        params: {
          sub_path: this.currentPath,
          page_size: this.perPage,
          page: this.currentPage,
          search: this.submitedSearch,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
        },
      })
        .then(res => {
          this.batches = res.data.items
          this.totalRecords = res.data.count
          this.loadingError = null
          this.loading = false
        })
        .catch(error => {
          this.loadingError = error?.response?.data?.detail || 'Error fetching batches'
          this.loading = false
        })
    },
    downloadZip(folderName) {
      this.downloadingZips.push(folderName)
      const batchPath = this.currentPath ? `${this.currentPath}/${folderName}` : `${folderName}`

      axios.get('/pipeline/download_batch_zip/', {
        params: {
          batch_path: batchPath,
        },
        responseType: 'blob',
      }).then(response => {
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${folderName}.zip`)
        document.body.appendChild(link)
        link.click()

        this.downloadingZips = this.downloadingZips.filter(folder => folder !== folderName)
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
        this.downloadingZips = this.downloadingZips.filter(folder => folder !== folderName)
      })
    },
    searchSubmitHandler() {
      this.$router.push({ name: 'batches', query: { path: this.currentPath, search: this.search.trim() } })
    },
    pageChanged(page) {
      this.currentPage = page
      this.fetchBatches()
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
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false

      this.sortBy = sortBy
      this.sortDesc = sortDesc

      this.fetchBatches()
    },
  },
}
</script>

<style scoped>
.per-page-selector {
  width: 90px;
}
.table-busy {
  opacity: 0.55;
  pointer-events: none;
}
.table-busy-spinner {
 opacity: 0.55;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
