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
              variant="primary"
              @click.stop="createProject = true"
            >
              Create Project
            </b-button>

            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="importProject = true"
            >
              Import Projects
            </b-button>

            <b-button
              :disabled="selectedRecords.length === 0 || exportingProjects"
              variant="outline-primary"
              class="ml-1"
              @click="exportMultipleProjects"
            >
              Export Projects
              <b-spinner
                v-if="exportingProjects"
                small
                label="Small Spinner"
              />
            </b-button>
            <b-button
              :disabled="!projects.length"
              variant="outline-primary"
              class="ml-1"
              @click="exportsAllModal"
            >
              Export All
            </b-button>
          </b-col>

          <b-col
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
          </b-col>
        </b-row>
      </div>

      <b-table-simple
        :class="{
          'table-busy': loading
        }"
      >
        <b-thead>
          <b-tr>
            <template v-for="tableColumn of tableColumns">
              <b-th
                v-if="tableColumn.key === 'select'"
                :key="tableColumn.key"
              >
                <b-form-checkbox
                  v-model="allRecordsSeleted"
                  :disabled="projects.length === 0"
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
            v-for="(project, projectIndex) of projects"
            :key="projectIndex"
          >
            <b-td>
              <b-form-checkbox
                v-model="selectedRecords"
                :value="project.id"
              />
            </b-td>
            <b-td>
              {{ project.project_id }}
            </b-td>
            <b-td class="max-table-col-w">
              {{ project.name }}
            </b-td>
            <b-td>
              {{ formatedDate(project.updated_at) }}
            </b-td>
            <b-td>
              <div class="text-nowrap">
                <feather-icon
                  v-b-tooltip.hover
                  icon="EditIcon"
                  size="18"
                  class="mr-1 cursor-pointer"
                  title="Edit Project"
                  @click.stop="editProject(project)"
                />

                <feather-icon
                  v-if="!exportingProjectIds.includes(project.id)"
                  v-b-tooltip.hover
                  icon="DownloadIcon"
                  class="mr-1 cursor-pointer"
                  size="18"
                  title="Export Project"
                  @click.stop="exportProject(project)"
                />
                <b-spinner
                  v-if="exportingProjectIds.includes(project.id)"
                  class="mr-1"
                  small
                  label="Small Spinner"
                />

                <feather-icon
                  v-b-tooltip.hover
                  icon="TrashIcon"
                  class="cursor-pointer"
                  size="18"
                  title="Delete Project"
                  @click.stop="deleteProject = project"
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
        v-if="!loading && projects.length === 0"
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
          :local-records="projects.length"
          @page-changed="pageChanged"
        />
      </div>

    </b-card>

    <project-form
      v-if="createProject"
      :project="createProject"
      @modal-closed="createProject = null"
    />

    <delete-project
      v-if="deleteProject"
      :project="deleteProject"
      @modal-closed="deleteProject = null"
      @deleted="submitDelete"
    />

    <import-json
      v-if="importProject"
      title="Projects"
      url="/dashboard/admin/projects/import/"
      field="projects"
      @modal-closed="importProject = false"
      @imported="fetchProjects"
    />
    <export-all-projects
      v-if="showExportAllModal"
      :total-records="totalRecords"
      @modal-closed="showExportAllModal = false"
      @exported="fetchProjects"
    />
  </div>
</template>

<script>
import axios from 'axios'
import {
  BAlert,
  BButton,
  BCard,
  BCol,
  BForm,
  BFormCheckbox,
  BFormInput,
  BRow,
  BSpinner,
  BTableSimple,
  BTbody,
  BTd,
  BTh,
  BThead, BTr,
  VBTooltip,
} from 'bootstrap-vue'
import exportFromJSON from 'export-from-json'
import vSelect from 'vue-select'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ImportJson from '@/components/UI/ImportJson.vue'
import DeleteProject from './DeleteProject.vue'
import ProjectForm from './ProjectForm.vue'
import ExportAllProjects from './ExportAllProjects.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    ProjectForm,
    ImportJson,
    DeleteProject,
    BSpinner,
    BAlert,
    BCard,
    BButton,
    BRow,
    BCol,
    DetailedPagination,
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
    ExportAllProjects,
  },
  data() {
    return {
      projects: [],
      tableColumns: [
        {
          key: 'select',
        },
        {
          key: 'project_id', label: 'Project Id', sortable: true, customSearch: true,
        },
        {
          key: 'name', label: 'Name', sortable: true, customSearch: true,
        },
        { key: 'updated_at', label: 'Updated Date', sortable: true },
        { key: 'actions', label: 'Actions' },
      ],
      deleteProject: null,
      loading: true,
      loadingError: null,
      expanded: false,
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      sortBy: 'name',
      sortDesc: false,
      searchBy: {
        name: null,
      },
      initialized: false,
      selectedRecords: [],
      allRecordsSeleted: false,
      exportingProjectIds: [],
      exportingProjects: false,
      createProject: null,
      importProject: false,
      showExportAllModal: false,
    }
  },
  computed: {
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

        this.fetchProjects()
      }
    },
    stickyFilters: {
      handler() {
        localStorage.setItem('projects-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true,
    },
    selectedRecords(newValue) {
      if (this.projects.length > 0 && newValue.length === this.projects.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    projects() {
      this.selectedRecords = this.selectedRecords.filter(id => {
        const index = this.projects.findIndex(project => project.id === id)

        return index !== -1
      })
    },
  },
  created() {
    this.initProjects()
  },
  methods: {
    async initProjects() {
      this.loading = true

      const projectsFilterData = localStorage.getItem('projects-filter')

      if (projectsFilterData) {
        const projectsFilter = JSON.parse(projectsFilterData)

        if (projectsFilter.searchBy) {
          this.searchBy = projectsFilter.searchBy
        }

        if (projectsFilter.perPage) {
          this.perPage = projectsFilter.perPage
        }
      }

      this.$nextTick(() => {
        this.initialized = true
      })

      this.fetchProjects()
    },
    exportsAllModal() {
      this.showExportAllModal = true
    },
    fetchProjects() {
      this.loading = true

      axios.get('/dashboard/admin/projects/', {
        params: {
          page_size: this.perPage,
          page: this.currentPage,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
          ...this.searchBy,
        },
      })
        .then(res => {
          this.projects = res.data.results
          this.totalRecords = res.data.count
          this.loading = false
        })
        .catch(error => {
          this.loadingError = error?.response?.data?.detail || 'Error fetching projects'
          this.loading = false
        })
    },
    editProject(project) {
      this.$router.push({ name: 'projectDetails', params: { id: project.id } })
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
    pageChanged(page) {
      this.currentPage = page

      this.fetchProjects()
    },
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc

      this.fetchProjects()
    },
    searchSubmitHandler() {
      this.currentPage = 1

      this.fetchProjects()
    },
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.projects.map(project => project.id) : []
    },
    exportProject(project) {
      this.exportingProjectIds.push(project.id)

      const fileName = `Project-${project.name}`
      const payload = {
        ids: [project.id],
        export_all: false,
      }
      this.exportProjects(payload, fileName)
        .then(() => {
          this.exportingProjectIds = this.exportingProjectIds.filter(projectId => projectId !== project.id)
        })
    },
    exportMultipleProjects() {
      if (this.selectedRecords.length === 0) {
        return
      }

      this.exportingProjects = true
      const payload = {
        ids: this.selectedRecords,
        export_all: false,
      }

      this.exportProjects(payload, 'Projects')
        .then(() => {
          this.exportingProjects = false
          this.selectedRecords = []
        })
    },

    exportProjects(data, fileName) {
      return axios.post('/dashboard/admin/projects/export/', data)
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting project(s)',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
    },
    submitDelete() {
      if (this.currentPage > 1 && this.projects.length === 1) {
        this.currentPage -= 1
      }
      this.fetchProjects()
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
