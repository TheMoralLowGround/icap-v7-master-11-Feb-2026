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
              @click="addDefinition = true"
            >
              Add Definition
            </b-button>

            <b-button
              variant="outline-primary"
              class="ml-1"
              @click="importDefinition = true"
            >
              Import Definitions
            </b-button>

            <b-button
              :disabled="selectedRecords.length === 0 || exportingDefinitions"
              variant="outline-primary"
              class="ml-1"
              @click="exportMultipleDefinitions"
            >
              Export Definitions
              <b-spinner
                v-if="exportingDefinitions"
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
            <template
              v-for="tableColumn of tableColumns"
            >
              <b-th
                v-if="tableColumn.key === 'select'"
                :key="tableColumn.key"
              >
                <b-form-checkbox
                  v-model="allRecordsSeleted"
                  :disabled="definitions.length === 0"
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
            v-for="(definition, definitionIndex) of definitions"
            :key="definitionIndex"
          >
            <b-td>
              <b-form-checkbox
                v-model="selectedRecords"
                :value="definition.id"
              />
            </b-td>
            <b-td>
              {{ definition.definition_id }}
            </b-td>
            <b-td>
              {{ definition.vendor }}
            </b-td>
            <b-td>{{ definition.type }}</b-td>
            <b-td>
              <feather-icon
                :icon="definition.cw1 ? 'CheckIcon' : 'XIcon'"
                size="18"
              />
            </b-td>
            <b-td>
              {{ formatedDate(definition.updated_at) }}
            </b-td>
            <b-td>
              <div class="text-nowrap">
                <feather-icon
                  v-b-tooltip.hover
                  icon="EditIcon"
                  size="18"
                  class="mr-1 cursor-pointer"
                  title="Edit Definition"
                  @click.stop="editDefinition = definition"
                />
                <feather-icon
                  v-b-tooltip.hover
                  icon="CopyIcon"
                  size="18"
                  class="mr-1 cursor-pointer"
                  title="Clone Definition"
                  @click.stop="cloneDefinition = definition"
                />
                <feather-icon
                  v-if="exportSystemName !== null"
                  v-b-tooltip.hover
                  icon="SendIcon"
                  class="mr-1 cursor-pointer"
                  size="18"
                  title="Send Definition"
                  @click.stop="sendDefinition = definition"
                />

                <feather-icon
                  v-if="!exportingDefinitionIds.includes(definition.id)"
                  v-b-tooltip.hover
                  icon="DownloadIcon"
                  class="mr-1 cursor-pointer"
                  size="18"
                  title="Export Definition"
                  @click.stop="exportDefinition(definition)"
                />
                <b-spinner
                  v-if="exportingDefinitionIds.includes(definition.id)"
                  class="mr-1"
                  small
                  label="Small Spinner"
                />

                <feather-icon
                  v-b-tooltip.hover
                  icon="TrashIcon"
                  class="cursor-pointer"
                  size="18"
                  title="Delete Definition"
                  @click.stop="deleteDefinition = definition"
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
        <b-spinner
          variant="primary"
        />
      </div>

      <div
        v-if="!loading && definitions.length === 0"
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
          :local-records="definitions.length"
          @page-changed="pageChanged"
        />
      </div>

    </b-card>

    <delete-definition
      v-if="deleteDefinition"
      :definition="deleteDefinition"
      @modal-closed="deleteDefinition = null"
      @deleted="fetchDefinitions"
    />

    <send-definition
      v-if="sendDefinition"
      :definition="sendDefinition"
      :export-system-name="exportSystemName"
      @modal-closed="sendDefinition = null"
    />

    <definition-form
      v-if="addDefinition"
      mode="add"
      @modal-closed="addDefinition = false"
      @saved="fetchDefinitions"
    />

    <definition-form
      v-if="editDefinition"
      :definition="editDefinition"
      mode="edit"
      @modal-closed="editDefinition = false"
      @saved="fetchDefinitions"
    />

    <definition-form
      v-if="cloneDefinition"
      :definition="cloneDefinition"
      mode="clone"
      @modal-closed="cloneDefinition = false"
      @saved="fetchDefinitions"
    />

    <import-definitions
      v-if="importDefinition"
      @modal-closed="importDefinition = false"
      @imported="fetchDefinitions"
    />
  </div>
</template>

<script>
import {
  VBTooltip, BSpinner, BAlert, BCard, BRow, BCol, BButton, BTableSimple, BThead, BTr, BTh, BTbody, BForm, BFormInput, BTd, BFormCheckbox,
} from 'bootstrap-vue'
import axios from 'axios'
import moment from 'moment-timezone'
import vSelect from 'vue-select'
import exportFromJSON from 'export-from-json'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import DeleteDefinition from './DeleteDefinition.vue'
import DefinitionForm from './DefinitionForm.vue'
import SendDefinition from './SendDefinition.vue'
import ImportDefinitions from './ImportDefinitions/ImportDefinitions.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    DeleteDefinition,
    DefinitionForm,
    BSpinner,
    BAlert,
    BCard,
    BButton,
    BRow,
    BCol,
    SendDefinition,
    ImportDefinitions,
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
  },
  data() {
    return {
      definitions: [],
      tableColumns: [
        {
          key: 'select',
        },
        {
          key: 'definition_id', label: 'Profile ID', sortable: true, customSearch: true,
        },
        {
          key: 'vendor', label: 'Customer', sortable: true, customSearch: true,
        },
        {
          key: 'type', label: 'Type', sortable: true, customSearch: true,
        },
        {
          key: 'cw1', label: 'Cw1', sortable: true, customSearch: true,
        },
        { key: 'updated_at', label: 'Updated Date', sortable: true },
        { key: 'actions', label: 'Actions' },
      ],
      deleteDefinition: null,
      loading: true,
      loadingError: null,
      expanded: false,
      addDefinition: false,
      editDefinition: null,
      cloneDefinition: null,
      exportSystemName: null,
      sendDefinition: null,
      importDefinition: false,
      currentPage: 1,
      perPage: 10,
      totalRecords: 0,
      perPageOptions: [10, 25, 50, 100],
      sortBy: 'id',
      sortDesc: true,
      searchBy: {
        definition_id: null,
        vendor: null,
        type: null,
        cw1: null,
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
      exportingDefinitions: false,
      exportingDefinitionIds: [],
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
        this.fetchDefinitions()
      }
    },
    stickyFilters: {
      handler() {
        localStorage.setItem('definitions-filter', JSON.stringify(this.stickyFilters))
      },
      deep: true,
    },
    selectedRecords(newValue) {
      if (this.definitions.length > 0 && newValue.length === this.definitions.length) {
        this.allRecordsSeleted = true
      } else {
        this.allRecordsSeleted = false
      }
    },
    definitions() {
      this.selectedRecords = this.selectedRecords.filter(id => {
        const index = this.definitions.findIndex(definition => definition.id === id)
        return index !== -1
      })
    },
  },
  created() {
    this.initDefinitions()
  },
  methods: {
    async initDefinitions() {
      this.loading = true

      const definitionsFilterData = localStorage.getItem('definitions-filter')
      if (definitionsFilterData) {
        const definitionsFilter = JSON.parse(definitionsFilterData)
        if (definitionsFilter.searchBy) {
          this.searchBy = definitionsFilter.searchBy
        }
        if (definitionsFilter.perPage) {
          this.perPage = definitionsFilter.perPage
        }
      }
      this.$nextTick(() => {
        this.initialized = true
      })

      // Fetch Data Export Config
      try {
        const res = await axios.get('/settings/data_export_config/')
        this.exportSystemName = res.data?.export_system_name || null
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching data export config'
        this.loading = false
        return
      }

      this.fetchDefinitions()
    },
    fetchDefinitions() {
      this.loading = true

      axios.get('/definitions/', {
        params: {
          page_size: this.perPage,
          page: this.currentPage,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
          ...this.searchBy,
        },
      })
        .then(res => {
          this.definitions = res.data.results
          this.totalRecords = res.data.count
          this.loading = false
        })
        .catch(error => {
          this.loadingError = error?.response?.data?.detail || 'Error fetching definitions'
          this.loading = false
        })
    },
    formatedDate(dateString) {
      return moment.utc(dateString).tz('America/New_York').format('DD/MM/YYYY HH:mm')
    },
    pageChanged(page) {
      this.currentPage = page
      this.fetchDefinitions()
    },
    customSort(sortBy) {
      const sortDesc = sortBy === this.sortBy ? !this.sortDesc : false
      this.sortBy = sortBy
      this.sortDesc = sortDesc
      this.fetchDefinitions()
    },
    searchSubmitHandler() {
      this.currentPage = 1
      this.fetchDefinitions()
    },
    exportMultipleDefinitions() {
      if (this.selectedRecords.length === 0) {
        return
      }
      this.exportingDefinitions = true
      this.exportDefinitions(this.selectedRecords, 'Definitions')
        .then(() => {
          this.exportingDefinitions = false
        })
    },
    exportDefinition(definition) {
      this.exportingDefinitionIds.push(definition.id)
      const fileName = `Definition-${definition.definition_id}-${definition.type}`
      this.exportDefinitions([definition.id], fileName)
        .then(() => {
          this.exportingDefinitionIds = this.exportingDefinitionIds.filter(definitionId => definitionId !== definition.id)
        })
    },
    exportDefinitions(ids, fileName) {
      return axios.post('/pipeline/export_definitions/', { ids })
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting definition(s)',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
    },
    toggleRecordsSelection(checked) {
      this.selectedRecords = checked ? this.definitions.map(definition => definition.id) : []
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
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
