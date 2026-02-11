<template>
  <b-modal
    v-model="showModal"
    centered
    :title="title"
    size="xl"
    modal-class="scrollable-modal"
    @hidden="$emit('modal-closed')"
  >
    <validation-observer ref="processForm">
      <div class="modal-content-container">
        <!-- Process select box at the top with validation -->
        <div class="mb-2">
          <validation-provider
            #default="{ errors }"
            name="Process"
            :rules="'required'"
            vid="process"
            mode="eager"
          >
            <b-form-group
              label="Select Process"
              :state="errors.length > 0 ? false : null"
            >
              <v-select
                ref="vSelect"
                v-model="selectedProfile"
                :options="profiles"
                :reduce="profile => profile"
                placeholder="Select Process"
                label="name"
                :clearable="true"
                @open="scrollToSelected(profiles, selectedProfile)"
              />
              <small class="text-danger">{{ errors[0] }}</small>
            </b-form-group>
          </validation-provider>
        </div>

        <!-- Table displaying annotation datasets -->
        <div class="table-container">
          <b-table-simple
            :class="{
              'table-busy': loading
            }"
            class="annotation-datasets-table"
          >
            <!-- Table headers -->
            <b-thead class="sticky-header">
              <b-tr>
                <template v-for="tableColumn of tableColumns">
                  <!-- Checkbox for selecting all records -->
                  <b-th
                    v-if="tableColumn.key === 'select'"
                    :key="tableColumn.key"
                  >
                    <b-form-checkbox
                      v-model="allRecordsSelected"
                      :disabled="datasets.length === 0"
                      @change="toggleRecordsSelection"
                    />
                  </b-th>

                  <!-- Sortable columns -->
                  <b-th
                    v-if="tableColumn.key !== 'select' && tableColumn.sortable"
                    :key="tableColumn.key"
                    :aria-sort="sortBy === tableColumn.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                    @click="customSort(tableColumn.key)"
                  >
                    {{ tableColumn.label }}
                  </b-th>

                  <!-- Non-sortable columns -->
                  <b-th
                    v-if="tableColumn.key !== 'select' && !tableColumn.sortable"
                    :key="tableColumn.key"
                  >
                    {{ tableColumn.label }}
                  </b-th>
                </template>
              </b-tr>
              <!-- Search inputs row -->
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

            <!-- Table body -->
            <b-tbody v-if="!loading">
              <b-tr
                v-for="(dataset, datasetIndex) of datasets"
                :key="datasetIndex"
              >
                <b-td>
                  <b-form-checkbox
                    v-model="selectedRecords"
                    :value="dataset.id"
                  />
                </b-td>
                <b-td>
                  {{ dataset.id }}
                </b-td>
                <!-- <b-td>
                  {{ dataset.vendor }}
                </b-td> -->
                <b-td class="max-table-col-w">
                  {{ dataset.process }}
                </b-td>
                <b-td class="max-table-col-w">
                  <show-document-types
                    :document-types="dataset.document_types"
                    :max-visible="3"
                  />
                </b-td>
                <b-td>
                  <show-document-types
                    :document-types="dataset.entities"
                    :max-visible="3"
                  />
                </b-td>
                <b-td class=".max-table-col-w">
                  {{ dataset.language }}
                </b-td>
                <b-td class="max-table-col-w">
                  <span>
                    {{ Array.isArray(dataset.notes) ? dataset.notes.map(note => note.note).join(', ') : '' }}
                  </span>
                </b-td>
              </b-tr>
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
            v-if="!loading && datasets.length === 0"
            class="text-center m-3"
          >
            No records found!
          </div>
        </div>

        <!-- Pagination outside of scrollable area -->
        <div
          v-if="!loading"
          class="pagination-container mx-2 mt-1 mb-2"
        >
          <detailed-pagination
            :per-page="perPage"
            :current-page="currentPage"
            :total-records="totalRecords"
            :local-records="datasets.length"
            @page-changed="pageChanged"
          />
        </div>

        <!-- Error Alert -->
        <b-alert
          variant="danger"
          :show="error !== null"
          class="mt-3"
        >
          <div class="alert-body">
            <p>{{ error }}</p>
          </div>
        </b-alert>

        <!-- Success Alert -->
        <b-alert
          variant="success"
          :show="successMessage !== null"
          class="mt-3"
        >
          <div class="alert-body">
            <p>{{ successMessage }}</p>
          </div>
        </b-alert>
      </div>
    </validation-observer>

    <!-- Modal footer with close and submit buttons -->
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Close
      </b-button>
      <b-button
        variant="primary"
        :disabled="isSubmitDisabled"
        @click="onSubmit()"
      >
        Submit
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BButton, BModal, BSpinner, BAlert, BTableSimple, BThead, BTbody, BTh, BTd, BTr, BFormInput, BFormCheckbox, BForm, BFormGroup,
} from 'bootstrap-vue'
import axios from 'axios'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import vSelect from 'vue-select'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'
import ShowDocumentTypes from './ShowDocumentTypes.vue'
import 'vue-select/dist/vue-select.css'

export default {
  components: {
    vSelect,
    BButton,
    BModal,
    BSpinner,
    BAlert,
    BTableSimple,
    BThead,
    BTbody,
    BTh,
    BTd,
    BTr,
    BFormInput,
    BFormCheckbox,
    BForm,
    BFormGroup,
    DetailedPagination,
    ShowDocumentTypes,
    ValidationProvider,
    ValidationObserver,
  },
  props: {
    title: {
      type: String,
      required: false,
      default: 'Annotation Datasets',
    },
    apiEndpoint: {
      type: String,
      required: false,
      default: '/api/pipeline/get_annotation_batches',
    },
  },
  data() {
    return {
      showModal: true,
      selectedProfile: null,
      loading: false,
      submitting: false,
      datasets: [],
      profiles: [],
      error: null,
      successMessage: null,

      // Pagination
      currentPage: 1,
      perPage: 50,
      totalRecords: 0,

      // Sorting
      sortBy: 'created_at',
      sortDesc: true,

      // Search filters
      searchBy: {
        id: null,
        process: null,
        document_types: null,
        entities: null,
        language: null,
        notes: null,
      },

      // Selection
      selectedRecords: [],
      allRecordsSelected: false,

      // Table configuration
      tableColumns: [
        {
          key: 'select',
          sortable: false,
          customSearch: false,
        },
        {
          key: 'id',
          label: 'ID',
          sortable: true,
          customSearch: true,
        },
        // {
        //   key: 'vendor',
        //   label: 'Vendor',
        //   sortable: true,
        //   customSearch: true,
        // },
        {
          key: 'process',
          label: 'Process',
          sortable: false,
          customSearch: true,
        },
        {
          key: 'document_types',
          label: 'Document Types',
          sortable: true,
          customSearch: true,
        },
        {
          key: 'entities',
          label: 'Entities',
          sortable: true,
          customSearch: true,
        },
        {
          key: 'language',
          label: 'Language',
          sortable: false,
          customSearch: false,
        },
        {
          key: 'notes',
          label: 'Notes',
          sortable: true,
          customSearch: true,
        },
      ],
    }
  },
  computed: {
    selectedBatches() {
      return this.datasets.filter(dataset => this.selectedRecords.includes(dataset.id))
    },
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    projectCountries() {
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

      return result
    },
    isSubmitDisabled() {
      return this.submitting
             || this.selectedRecords.length === 0
    },
  },
  mounted() {
    this.fetchDatasets()
    this.fetchProfiles()
  },
  methods: {
    // Fetch datasets from API
    fetchDatasets() {
      this.loading = true
      this.error = null
      this.successMessage = null

      const params = {
        page_size: this.perPage,
        page: this.currentPage,
        sort_by: this.sortBy,
        sort_desc: this.sortDesc,
        ...this.searchBy,
      }

      // Filter out null/empty search parameters
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === '') {
          delete params[key]
        }
      })

      axios.get(this.apiEndpoint, { params })
        .then(res => {
          this.datasets = res.data.results || []
          this.totalRecords = res.data.count || 0
          this.loading = false
        })
        .catch(error => {
          this.loading = false
          this.error = error?.response?.data?.detail || 'Error fetching annotation datasets'
        })
    },

    // Submit selected batches with process name
    async onSubmit() {
      // Clear any previous errors
      this.error = null
      this.successMessage = null

      // Validate the form first
      const isValid = await this.$refs.processForm.validate()
      if (!isValid) {
        return
      }

      // Additional validation (business logic)
      if (!this.selectedProfile) {
        this.error = 'Please select a process first.'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Validation Error',
            text: 'Please select a process first.',
            icon: 'AlertTriangleIcon',
            variant: 'warning',
          },
        })
        return
      }

      if (this.selectedRecords.length === 0) {
        this.error = 'Please select at least one batch to submit.'
        return
      }

      this.submitting = true

      const payload = {
        linked_batches: this.selectedBatches,
        process_name: this.selectedProfile,
        selectedProfile: null,
      }

      axios.post('/pipeline/create_training_dataset_batch/', payload)
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Training transaction created successfully!',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.successMessage = 'Training transaction created successfully!'
          this.submitting = false
          this.selectedRecords = []
          this.allRecordsSelected = false
          this.$emit('submitted', res.data)
          this.showModal = false
        })
        .catch(error => {
          this.submitting = false
          this.error = error?.response?.data?.detail || 'Error creating training transaction'
        })
    },

    // Pagination handler
    pageChanged(page) {
      this.currentPage = page
      this.fetchDatasets()
    },

    // Sorting handler
    customSort(column) {
      if (this.sortBy === column) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = column
        this.sortDesc = false
      }
      this.currentPage = 1
      this.fetchDatasets()
    },

    // Search handler
    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchDatasets()
    },

    // Selection handlers
    toggleRecordsSelection() {
      if (this.allRecordsSelected) {
        this.selectedRecords = this.datasets.map(dataset => dataset.id)
      } else {
        this.selectedRecords = []
      }
    },

    // Action handlers
    downloadDataset() {},
    scrollToSelected(options, selectedValue) {
      this.$nextTick(() => {
        // Helper function to scroll a dropdown menu to the selected item
        const scrollDropdownToSelected = (dropdownMenu, selectedIndex) => {
          if (dropdownMenu && selectedIndex >= 0) {
            // Calculate scroll position by assuming each item has a uniform height
            const itemHeight = dropdownMenu.scrollHeight / options.length

            // Adjust scrollTop to bring the selected item closer to the top
            const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
            // eslint-disable-next-line no-param-reassign
            dropdownMenu.scrollTop = scrollPosition
          }
        }

        // Get references to dropdown menus
        const dropdownMenuItems = this.$refs.vSelect?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options?.indexOf(selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
      })
    },
    async fetchProfiles() {
      try {
        const res = await axios.post('/dashboard/profiles/filter_list/', { project_countries: this.projectCountries }, {
          params: {
            paginate: false,
          },
        })
        this.profiles = res.data?.map(p => p.name)
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error(error)
      }
    },
  },
}
</script>

<style scoped>
/* Modal container styling */
.scrollable-modal .modal-dialog {
  max-height: 80vh;
  margin: 10vh auto;
}

.scrollable-modal .modal-content {
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.scrollable-modal .modal-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.modal-content-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(80vh - 120px); /* Account for header and footer */
}

/* Table container - scrollable */
.table-container {
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  max-height: calc(80vh - 200px); /* Account for pagination and select box */
  border-radius: 0.375rem;
}

/* Sticky header */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 10;
}

.sticky-header th {
  border-top: none;
}

/* Pagination container - fixed at bottom */
.pagination-container {
  flex-shrink: 0;
  padding: 0.75rem 1rem;
  margin: 0 !important;
}

/* Table styling */
.annotation-datasets-table {
  margin-bottom: 0;
  min-width: 300px; /* Reduced minimum width */
}

.annotation-datasets-table td,
.annotation-datasets-table th {
  /* white-space: nowrap; */
  padding: 0.2rem; /* Reduced padding */
  vertical-align: middle;
}

/* Utility classes */
.cursor-pointer {
  cursor: pointer;
}

.table-busy-spinner {
  min-height: 150px; /* Reduced spinner container height */
  display: flex;
  align-items: center;
  justify-content: center;
}

.text-nowrap {
  white-space: nowrap;
}

.table-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
.max-cell-w {
  max-width: 500px;
  width: 300px;
  overflow-wrap: break-word;
  white-space: normal;
}
</style>
