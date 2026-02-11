<template>
  <div class="parties-search mb-3">
    <!-- Search Input -->
    <SearchInDdh
      :disabled="loading"
      aria-label="Search organizations input"
      @search="handleSearch"
    />

    <!-- Loading State -->
    <div
      v-if="loading"
      class="text-center p-3"
    >
      <b-spinner
        variant="primary"
        label="Loading search results"
      />
      <p class="mt-2 mb-0 text-muted">
        Searching organizations...
      </p>
    </div>

    <!-- Error State -->
    <b-alert
      v-if="errorMessage"
      variant="danger"
      show
      class="mt-2"
      role="alert"
    >
      {{ errorMessage }}
    </b-alert>

    <!-- Results Table -->
    <div
      v-if="showResults && !loading"
      class="mt-3"
    >
      <b-card
        no-body
        class="shadow-sm"
        role="region"
        aria-label="Search results table"
      >
        <!-- No Results Message -->
        <div
          v-if="results.length === 0"
          class="p-3 text-muted text-center"
          role="alert"
        >
          No results found for "{{ searchQuery }}"
        </div>

        <!-- Results Table -->
        <div v-else>
          <!-- Action Buttons -->
          <div class="p-2 border-bottom bg-light">
            <b-row
              align-h="between"
              align-v="center"
            >
              <b-col cols="auto">
                <small class="text-muted">
                  {{ selectedItems.length }} selected of {{ totalRecords }} results
                </small>
              </b-col>
              <b-col cols="auto d-flex gap-2">
                <b-button
                  variant="outline-secondary"
                  size="sm"
                  :disabled="!selectedItems.length"
                  class="me-2"
                  aria-label="Clear selected items"
                  @click="clearSelection"
                >
                  Clear
                </b-button>
                <b-button
                  variant="primary"
                  size="sm"
                  :disabled="!selectedItems.length"
                  class="me-2"
                  aria-label="Add selected items"
                  @click="addSelected"
                >
                  Add {{ selectedItems.length }}
                </b-button>
                <b-button
                  variant="outline-danger"
                  size="sm"
                  aria-label="Close results table"
                  @click="closeTable"
                >
                  Close
                </b-button>
              </b-col>
            </b-row>
          </div>

          <!-- Table -->
          <b-table-simple
            responsive
            striped
            hover
            :busy="loading"
            aria-label="Organizations search results"
          >
            <b-thead>
              <b-tr>
                <b-th
                  v-for="field in tableFields"
                  :key="field.key"
                  :aria-sort="field.sortable ? 'none' : null"
                >
                  {{ field.label }}
                </b-th>
              </b-tr>
            </b-thead>
            <b-tbody>
              <b-tr
                v-for="(item, index) in results"
                :key="`row-${item.address_id || index}`"
              >
                <!-- Selection Column -->
                <b-td>
                  <b-form-checkbox
                    :id="`checkbox-${item.address_id || index}`"
                    :checked="isSelected(item)"
                    :aria-label="`Select ${item.org_name || 'organization'}`"
                    @change="toggleSelection(item)"
                  />
                </b-td>
                <!-- Data Columns -->
                <b-td>{{ item.org_name || '-' }}</b-td>
                <b-td>{{ item.cw1_code || '-' }}</b-td>
                <b-td>{{ item.short_code || '-' }}</b-td>
                <b-td>{{ item.address_line1 || '-' }}</b-td>
                <b-td>{{ item.address_line2 || '-' }}</b-td>
                <b-td>{{ item.city || '-' }}</b-td>
                <b-td>
                  <LookupDetails
                    :id="item.address_id"
                    :item="item"
                    aria-label="View details"
                  />
                </b-td>
              </b-tr>
            </b-tbody>
          </b-table-simple>

          <!-- Pagination -->
          <div
            class="mx-2 mt-2 mb-3"
          >
            <detailed-pagination
              :per-page="perPage"
              :current-page="currentPage"
              :total-records="totalRecords"
              :local-records="results.length"
              aria-label="Pagination controls"
              @page-changed="pageChanged"
            />
          </div>
        </div>
      </b-card>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import {
  BRow,
  BCol,
  BCard,
  BFormCheckbox,
  BButton,
  BTableSimple,
  BThead,
  BTbody,
  BTr,
  BTh,
  BTd,
  BSpinner,
  BAlert,
} from 'bootstrap-vue'
import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import SearchInDdh from './SearchInDdh.vue'
import LookupDetails from './LookupDetails.vue'

export default {
  name: 'PartiesSearch',
  components: {
    BRow,
    BCol,
    BCard,
    BFormCheckbox,
    BButton,
    BTableSimple,
    BThead,
    BTbody,
    BTr,
    BTh,
    BTd,
    BSpinner,
    BAlert,
    DetailedPagination,
    SearchInDdh,
    LookupDetails,
  },
  props: {
    apiEndpoint: {
      type: String,
      default: '/pipeline/semantic_address_match/',
    },
    perPage: {
      type: Number,
      default: 5,
    },
  },
  data() {
    return {
      searchQuery: '',
      results: [],
      selectedItems: [],
      showResults: false,
      loading: false,
      errorMessage: '',
      currentPage: 1,
      totalRecords: 0,
      currentFilters: {}, // Store current filters
      tableFields: [
        { key: 'select', label: '', sortable: false },
        { key: 'org_name', label: 'Organization Name', sortable: true },
        { key: 'cw1_code', label: 'Account Number', sortable: true },
        { key: 'short_code', label: 'Short Code', sortable: true },
        { key: 'address_line1', label: 'Address Line 1', sortable: true },
        { key: 'address_line2', label: 'Address Line 2', sortable: true },
        { key: 'city', label: 'City', sortable: true },
        { key: 'action', label: '', sortable: false },
      ],
    }
  },
  methods: {
    async handleSearch({ filters }) {
      this.loading = true
      this.errorMessage = ''

      // Reset to page 1 when new search/filter is applied
      this.currentPage = 1
      this.clearSelection()
      // Store current filters for pagination
      this.currentFilters = { ...filters }

      try {
        const response = await this.fetchFromAPI(filters)
        this.results = response?.data || []
        this.showResults = true
        this.updatePagination(response)
      } catch (error) {
        this.errorMessage = `Search failed: ${error.message}`
        this.results = []
      } finally {
        this.loading = false
      }
    },

    async fetchFromAPI(filters) {
      const requestBody = {
        filters: Object.fromEntries(
          Object.entries(filters).filter(([, value]) => value.trim() !== ''),
        ),
        page: this.currentPage,
        per_page: this.perPage,
      }
      // this.selectedItems = []
      try {
        const response = await axios.post(this.apiEndpoint, requestBody)
        return response.data
      } catch (error) {
        const message = error?.response?.data?.detail || error.message || 'Search request failed'
        throw new Error(message)
      }
    },

    updatePagination(response) {
      this.totalRecords = response.pagination?.total_count || this.results.length
      this.currentPage = response.pagination?.current_page || this.currentPage
    },

    async pageChanged(page) {
      this.currentPage = page
      // Use stored filters for pagination
      await this.handleSearchWithFilters(this.currentFilters)
    },

    // Method for pagination that doesn't reset to page 1
    async handleSearchWithFilters(filters) {
      this.loading = true
      this.errorMessage = ''

      try {
        const response = await this.fetchFromAPI(filters)
        this.results = response?.data || []
        this.updatePagination(response)
      } catch (error) {
        this.errorMessage = `Search failed: ${error.message}`
        this.results = []
      } finally {
        this.loading = false
      }
    },

    formatDistance(value) {
      if (value == null) return '-'
      const num = parseFloat(value)
      return Number.isNaN(num) ? '-' : num.toFixed(3)
    },

    toggleSelection(item) {
      const itemId = this.getUniqueItemId(item)
      const index = this.selectedItems.findIndex(
        selected => this.getUniqueItemId(selected) === itemId,
      )
      if (index > -1) {
        this.selectedItems.splice(index, 1)
      } else {
        this.selectedItems.push({ ...item })
      }
    },

    isSelected(item) {
      const itemId = this.getUniqueItemId(item)
      return this.selectedItems.some(
        selected => this.getUniqueItemId(selected) === itemId,
      )
    },

    getUniqueItemId(item) {
      return item.address_id || item.cw1_code || item.id || JSON.stringify(item)
    },

    clearSelection() {
      this.selectedItems = []
    },

    addSelected() {
      this.$emit('items-selected', [...this.selectedItems])
      this.clearSelection()
    },

    closeTable() {
      this.resetResults()
    },

    resetResults() {
      this.showResults = false
      this.searchQuery = ''
      this.results = []
      this.selectedItems = []
      this.currentPage = 1
      this.currentFilters = {}
      this.errorMessage = ''
    },
  },
}
</script>

<style scoped>
.parties-search {
  margin-bottom: 1.5rem;
}

/* .table-hover tbody tr:hover {
  background-color: rgba(0, 123, 255, 0.05);
} */

.table-busy {
  opacity: 0.65;
  pointer-events: none;
}

.shadow-sm {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* Responsive design */
@media (max-width: 768px) {
  .results-table {
    font-size: 0.85rem;
  }

  .results-table td,
  .results-table th {
    padding: 0.5rem;
  }

  .shadow-sm {
    box-shadow: none;
  }

  .p-2 {
    padding: 0.75rem !important;
  }

  .btn {
    font-size: 0.85rem;
    padding: 0.375rem 0.75rem;
  }
}
</style>
