<template>
  <div>
    <b-alert
      variant="danger"
      :show="!loading && loadingError !== null ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <b-card
      v-if="!loadingError"
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
            <b-button
              :to="{ name: 'create-process' }"
              variant="primary"
            >
              Create Process
            </b-button>

            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="importProfile = true"
            >
              Import Processes
            </b-button>

            <b-button
              :disabled="selectedRecords.length === 0 || exportingProfiles"
              variant="outline-primary"
              class="ml-1"
              @click="exportMultipleProfiles"
            >
              Export Processes
              <b-spinner
                v-if="exportingProfiles"
                small
                label="Small Spinner"
              />
            </b-button>
            <b-button
              :disabled="exportingAllProfiles || !profiles.length"
              variant="outline-primary"
              class="ml-1"
              @click="exportsAllModal"
            >
              Export All
              <b-spinner
                v-if="exportingAllProfiles"
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
            <b-button
              v-if="!noSearches"
              variant="outline-danger"
              size="sm"
              class="mr-1"
              @click="clearSearch"
            >
              Clear Search
            </b-button>
            <feather-icon
              v-b-tooltip.hover
              icon="FilterIcon"
              class="cursor-pointer mr-1"
              size="20"
              title="Filter Processes"
              @click.stop="filterProfiles = true"
            />

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
      <div class="table-responsive">
        <b-table-simple
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
                  v-if="tableColumn.key === 'select'"
                  :key="tableColumn.key"
                >
                  <b-form-checkbox
                    v-model="allRecordsSeleted"
                    :disabled="profiles.length === 0"
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
                    <v-select
                      v-if="tableColumn.key === 'cw1'"
                      v-model="searchBy[tableColumn.key]"
                      :dir="$store.state.appConfig.isRTL ? 'rtl' : 'ltr'"
                      :options="cw1FilterOptions"
                      :reduce="option => option.value"
                      :disabled="loading"
                      class="cw1-selection"
                      @input="searchSubmitHandler"
                    />

                    <b-form-input
                      v-if="tableColumn.key !== 'cw1'"
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
              v-for="(profile, profileIndex) of profiles"
              :key="profileIndex"
            >
              <b-td>
                <b-form-checkbox
                  v-model="selectedRecords"
                  :value="profile.id"
                />
              </b-td>
              <b-td>
                {{ profile.process_id }}
              </b-td>
              <b-td class="max-w">
                {{ profile.name }}
              </b-td>
              <b-td class="max-w">
                {{ profile.email_subject_match_text }}
              </b-td>
              <b-td class="max-w">
                {{ profile.project }}
              </b-td>
              <b-td>
                {{ profile.country }}
              </b-td>
              <!-- <b-td>{{ profile.mode_of_transport }}</b-td> -->
              <b-td>
                {{ formattedUpdatedAt(profile.updated_at) }}
              </b-td>
              <b-td>
                <div class="text-nowrap">
                  <feather-icon
                    v-if="isAdmin || defaultDefinitionVersion !== 'prod'"
                    v-b-tooltip.hover
                    icon="UploadCloudIcon"
                    size="18"
                    class="mr-1 cursor-pointer"
                    title="Train Documents"
                    @click.stop="trainDocumentProfileId = profile.id"
                  />

                  <feather-icon
                    v-b-tooltip.hover
                    icon="EditIcon"
                    size="18"
                    class="mr-1 cursor-pointer"
                    title="Process Configuration"
                    @click.stop="editProfile(profile)"
                  />

                  <feather-icon
                    v-b-tooltip.hover
                    icon="CopyIcon"
                    size="18"
                    class="mr-1 cursor-pointer"
                    title="Clone Process"
                    @click.stop="cloneProfile = profile"
                  />
                  <!-- <feather-icon
                    v-b-tooltip.hover
                    icon="RepeatIcon"
                    size="18"
                    class="mr-1 cursor-pointer"
                    title="Document Vendors Import / Export"
                    @click.stop="ExportImportProfile = profile"
                  /> -->

                  <feather-icon
                    v-if="exportSystemName"
                    v-b-tooltip.hover
                    icon="SendIcon"
                    class="mr-1 cursor-pointer"
                    size="18"
                    title="Send Process"
                    @click.stop="sendProfile = profile"
                  />

                  <feather-icon
                    v-if="!exportingProfileIds.includes(profile.id)"
                    v-b-tooltip.hover
                    icon="DownloadIcon"
                    class="mr-1 cursor-pointer"
                    size="18"
                    title="Export Process"
                    @click.stop="exportProfile(profile)"
                  />
                  <b-spinner
                    v-if="exportingProfileIds.includes(profile.id)"
                    class="mr-1"
                    small
                    label="Small Spinner"
                  />

                  <feather-icon
                    v-b-tooltip.hover
                    icon="TrashIcon"
                    class="cursor-pointer"
                    size="18"
                    title="Delete Process"
                    @click.stop="deleteProfile = profile"
                  />
                </div>
              </b-td>
            </b-tr>
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
        v-if="!loading && profiles.length === 0"
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
          :local-records="profiles.length"
          @page-changed="pageChanged"
        />
      </div>

    </b-card>

    <delete-profile
      v-if="deleteProfile"
      :profile="deleteProfile"
      @modal-closed="deleteProfile = null"
      @deleted="fetchProfiles"
    />

    <import-json
      v-if="importProfile"
      title="Processes"
      url="/dashboard/profiles/import/"
      field="profiles"
      @modal-closed="importProfile = false"
      @imported="fetchProfiles"
    />

    <train-documents
      v-if="trainDocumentProfileId"
      :profile-id="trainDocumentProfileId"
      @modal-closed="trainDocumentProfileId = null"
    />

    <clone-profile
      v-if="cloneProfile"
      :profile="cloneProfile"
      @modal-closed="cloneProfile = null"
      @cloned="handleCloneSuccess"
    />
    <!-- <export-import-profile
      v-if="ExportImportProfile"
      :profile="ExportImportProfile"
      @modal-closed="ExportImportProfile = false"
    /> -->

    <send-profile
      v-if="sendProfile"
      :definition="sendProfile"
      :export-system-name="exportSystemName"
      @modal-closed="sendProfile = null"
    />
    <filter-options
      v-if="filterProfiles"
      @modal-closed="filterProfiles = false"
    />
    <confirm-clear-searches
      v-if="clearSearches"
      v-model="searchBy"
      @submited="fetchProfiles"
      @modal-closed="clearSearches = false"
    />
    <b-modal
      v-model="showExportsAllModal"
      centered
      title="Export All Processes"
      @ok="exportAllProfiles"
    >
      <b-card-text>
        <div>
          Are you sure you want to export <span class="text-primary">{{ totalRecords }}</span> processes?
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
          :disabled="exportingAllProfiles"
          @click="ok()"
        >
          Export
          <b-spinner
            v-if="exportingAllProfiles"
            small
            label="Small Spinner"
          />
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>
import {
  BCardText, VBTooltip, BSpinner, BAlert, BCard, BRow, BCol, BButton, BTableSimple, BThead, BTr, BTh, BTbody, BForm, BFormInput, BTd, BFormCheckbox,
} from 'bootstrap-vue'
import axios from 'axios'
import vSelect from 'vue-select'
import exportFromJSON from 'export-from-json'
import getEnv from '@/utils/env'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ImportJson from '@/components/UI/ImportJson.vue'
import FilterOptions from '@/components/UI/FilterOptions.vue'
import ConfirmClearSearches from '@/components/UI/ConfirmClearSearches.vue'
import CloneProfile from './CloneProfile.vue'
// import ExportImportProfile from './ExportImportProfile.vue'
import DeleteProfile from './DeleteProfile.vue'
import TrainDocuments from './TrainDocuments.vue'
import SendProfile from './SendProfile.vue'

const definitionVersion = getEnv('VUE_APP_DEFAULT_DEFINITION_VERSION')

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BCardText,
    DeleteProfile,
    BSpinner,
    BAlert,
    BCard,
    BButton,
    BRow,
    BCol,
    DetailedPagination,
    FilterOptions,
    ConfirmClearSearches,
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTbody,
    BForm,
    BFormInput,
    BTd,
    vSelect,
    BFormCheckbox,
    ImportJson,
    TrainDocuments,
    SendProfile,
    CloneProfile,
    // ExportImportProfile,
  },
  data() {
    return {
      defaultDefinitionVersion: definitionVersion,
      profiles: [],
      tableColumns: [
        {
          key: 'select', width: 1,
        },
        {
          key: 'process_id', label: 'Process Id', sortable: true, customSearch: true, width: 10,
        },
        {
          key: 'name', label: 'Name', sortable: true, customSearch: true, width: 20,
        },
        {
          key: 'email_subject_match_text', label: 'Email Subject', sortable: true, customSearch: true, width: 10,
        },
        {
          key: 'project', label: 'Project', sortable: true, customSearch: true, width: 10,
        },
        {
          key: 'country', label: 'Country', sortable: true, customSearch: true, width: 5,
        },
        // {
        //   key: 'mode_of_transport', label: 'Mode Of Transport', sortable: true, customSearch: true, width: 5,
        // },
        {
          key: 'updated_at', label: 'Updated Date', sortable: true, width: 8,
        },
        {
          key: 'actions', label: 'Actions', width: 10,
        },
      ],
      deleteProfile: null,
      loading: true,
      loadingError: null,
      expanded: false,
      exportSystemName: null,
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      sortBy: 'updated_at',
      sortDesc: true,
      searchBy: {
        name: null,
        country_name: null,
        // mode_of_transport: null,
        project: null,
      },
      initialized: false,
      cw1FilterOptions: [
        {
          label: 'True',
          value: true,
        },
        {
          label: 'False',
          value: false,
        },
      ],
      selectedRecords: [],
      allRecordsSeleted: false,
      exportingProfileIds: [],
      exportingProfiles: false,
      importProfile: false,
      trainDocumentProfileId: null,
      sendProfile: null,
      cloneProfile: null,
      filterProfiles: false,
      reFetchProfiles: false,
      ExportImportProfile: null,
      exportingAllProfiles: false,
      showExportsAllModal: false,
      clearSearches: false,
    }
  },
  computed: {
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    stickySortAndFilters() {
      return {
        searchBy: this.searchBy,
        perPage: this.perPage,
        sortBy: this.sortBy,
        sortDesc: this.sortDesc,
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
  },
  watch: {
    perPage() {
      if (this.initialized) {
        this.currentPage = 1
        this.fetchProfiles()
      }
    },
    stickySortAndFilters: {
      handler() {
        localStorage.setItem('profiles-filter', JSON.stringify(this.stickySortAndFilters))
      },
      deep: true,
    },
    selectedRecords(newValue) {
      if (this.profiles.length > 0 && newValue.length === this.profiles.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    profiles() {
      this.selectedRecords = this.selectedRecords.filter(id => {
        const index = this.profiles.findIndex(profile => profile.id === id)
        return index !== -1
      })
    },
    filterBy() {
      if (!this.loading) {
        this.fetchProfiles()
      } else {
        this.reFetchProfiles = true
      }
    },
    loading(newVal) {
      if (!newVal && this.reFetchProfiles) {
        this.reFetchProfiles = false
        this.fetchProfiles()
      }
    },
  },
  created() {
    this.initProfiles()
  },
  methods: {
    async initProfiles() {
      this.loading = true

      const profilesFilterData = localStorage.getItem('profiles-filter')
      if (profilesFilterData) {
        const profilesFilter = JSON.parse(profilesFilterData)
        if (profilesFilter.searchBy) {
          this.searchBy = profilesFilter.searchBy
        }
        if (profilesFilter.perPage) {
          this.perPage = profilesFilter.perPage
        }
        if (profilesFilter.sortBy) {
          this.sortBy = profilesFilter.sortBy
        }
        this.sortDesc = profilesFilter.sortDesc
      }
      this.$nextTick(() => {
        this.initialized = true
      })

      await this.fetchDataExportConfig()

      this.fetchProfiles()
    },
    clearSearch() {
      this.searchBy = Object.fromEntries(
        Object.keys(this.searchBy).map(key => [key, null]),
      )
      this.fetchProfiles()
    },
    fetchProfiles() {
      this.loading = true

      const data = {
        ...this.filterBy,
      }

      axios.post('/dashboard/profiles/filter_list/', data, {
        params: {
          page_size: this.perPage,
          page: this.currentPage,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
          ...this.searchBy,
        },
      })
        .then(res => {
          this.profiles = res.data.results
          this.totalRecords = res.data.count
          this.loading = false
        })
        .catch(error => {
          this.loadingError = error?.response?.data?.detail || 'Error fetching processes'
          this.loading = false
        })
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
    formattedUpdatedAt(updatedAt) {
      const date = new Date(updatedAt)
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
    pageChanged(page) {
      this.currentPage = page
      this.fetchProfiles()
    },
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchProfiles()
    },
    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchProfiles()
    },
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.profiles.map(profile => profile.id) : []
    },
    editProfile(profile) {
      this.$router.push({ name: 'edit-process', params: { id: profile.id } })
    },
    handleCloneSuccess() {
      // Close the modal and refresh the listing
      // The modal closing is handled by the modal-closed event
      // Reset to first page to ensure new process is visible (since it's sorted by updated_at desc)
      this.currentPage = 1
      this.fetchProfiles()
    },
    exportProfile(profile) {
      this.exportingProfileIds.push(profile.id)
      const payload = {
        ids: [profile.id],
        export_all: false,
      }
      const fileName = `Process-${profile.name}`
      this.exportProfiles(payload, fileName)
        .then(() => {
          this.exportingProfileIds = this.exportingProfileIds.filter(profileId => profileId !== profile.id)
        })
    },
    exportMultipleProfiles() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.exportingProfiles = true
      const payload = {
        ids: this.selectedRecords,
        export_all: false,
      }
      this.exportProfiles(payload, 'Processes')
        .then(() => {
          this.exportingProfiles = false
          this.selectedRecords = []
        })
    },
    exportsAllModal() {
      this.showExportsAllModal = true
    },
    exportAllProfiles() {
      this.exportingAllProfiles = true
      this.showExportsAllModal = false
      const payload = {
        ids: [],
        export_all: true,
      }
      this.exportProfiles(payload, 'All Processes')
        .then(() => {
          this.exportingAllProfiles = false
        })
    },
    exportProfiles(data, fileName) {
      return axios.post('/dashboard/profiles/export/', data)
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting process(s)',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
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
.cw1-selection {
  width:130px;
}
.cw1-selection:not(.vs--disabled) {
  background:white;
  border-radius: 0.357rem;
}

[dir] .table th, [dir] .table td {
    padding: 0.72rem !important;
}
.table-responsive {
  overflow-x: auto;
  white-space: normal;
}
.max-w {
  max-width: 500px;
  overflow-wrap: break-word;
  white-space: normal;
}
/* .table-responsive td, .table-responsive th {
  word-break: break-word;
  white-space: normal;
} */
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
