<template>
  <div>
    <!-- Table -->
    <div class="d-flex justify-content-end mb-2">
      <b-button
        variant="outline-primary"
        size="sm"
        @click="addItem"
      >
        Add Key Qualifier
      </b-button>
    </div>
    <b-table-simple
      :class="{ 'table-busy': loading }"
      hover
      responsive
    >
      <b-thead>
        <!-- Header Row -->
        <b-tr>
          <b-th
            v-for="column in tableColumns"
            :key="'header-' + column.key"
            class="cursor-pointer"
            :aria-sort="column.sortable && sortBy === column.key ? (sortDesc ? 'descending' : 'ascending') : 'none'"
            @click="column.sortable && handleSort(column.key)"
          >
            <div
              class="d-flex align-items-center"
              :class="column.label === 'Action' ? 'justify-content-end pr-1': 'justify-content-between'"
            >
              {{ column.label }}
              <b-icon
                v-if="column.sortable"
                :icon="sortBy !== column.key ? 'arrow-down-up' : sortDesc ? 'arrow-down' : 'arrow-up'"
                font-scale="0.9"
              />
            </div>
          </b-th>
        </b-tr>

        <!-- Search Row -->
        <b-tr>
          <b-th
            v-for="column in tableColumns"
            :key="'search-' + column.key"
          >
            <b-form-input
              v-if="column.searchable"
              v-model="searchFields[column.key]"
              placeholder="Search"
              size="sm"
              debounce="300"
              @input="filterItems"
            />
          </b-th>
        </b-tr>
      </b-thead>

      <!-- Table Body -->
      <b-tbody>
        <b-tr v-if="loading">
          <b-td
            colspan="3"
            class="text-center text-muted py-4"
          >
            <b-spinner
              variant="primary"
              class="mr-2"
            />
            Loading...
          </b-td>
        </b-tr>
        <b-tr
          v-for="(item, index) in paginatedItems"
          v-else
          :key="index"
        >
          <b-td class="max-table-col-w">
            {{ item.label }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.value }}
          </b-td>
          <b-td>
            <div class="d-flex justify-content-end gap-2">
              <feather-icon
                v-b-tooltip.hover
                icon="EditIcon"
                size="18"
                class="mr-1 cursor-pointer"
                title="Edit Key"
                @click="editItem(item)"
              />
              <feather-icon
                v-b-tooltip.hover
                icon="TrashIcon"
                size="18"
                class="cursor-pointer"
                title="Delete Key"
                @click="deleteItem(item)"
              />
            </div>
          </b-td>
        </b-tr>
        <b-tr v-if="!loading && !filteredItems.length">
          <b-td
            colspan="5"
            class="text-center text-muted"
          >
            No matching records
          </b-td>
        </b-tr>
      </b-tbody>
    </b-table-simple>

    <!-- Pagination Controls -->

    <local-pagination
      :per-page="perPage"
      :total="filteredItems.length"
      :local-length="paginatedItems.length"
      :current-page="currentPage"
      @page-changed="currentPage = $event"
    >
      <div
        class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
      >
        <label class="mr-1">Show</label>
        <v-select
          v-model="perPage"
          :options="perPageOptions"
          :clearable="false"
          class="per-page-selector d-inline-block mx-50"
        />
        <label class="ml-1">entries</label>
      </div>
    </local-pagination>

    <project-key-qualifier-form
      :model-value="dialog"
      :is-edit="isEdit"
      :option-label="selectedItem"
      :existing-items="items"
      :selected-item-index="selectedItemIndex"
      @update:modelValue="dialog = $event"
      @save="handleSave"
    />
  </div>
</template>

<script>
import {
  BButton,
  BFormInput,
  BIcon,
  BTableSimple,
  BTbody, BTd,
  BTh,
  BThead, BTr,
  VBTooltip,
  BSpinner,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'
import vSelect from 'vue-select'
import LocalPagination from '../LocalPagination.vue'
import ProjectKeyQualifierForm from './ProjectKeyQualifierForm.vue'

export default {
  directives: { 'b-tooltip': VBTooltip },
  components: {
    BIcon,
    BFormInput,
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTbody,
    BTd,
    vSelect,
    LocalPagination,
    BButton,
    ProjectKeyQualifierForm,
    BSpinner,
  },
  props: {
    qualifierName: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      currentPage: 1,
      perPage: 10,
      perPageOptions: [10, 25, 50, 100],
      sortBy: '',
      sortDesc: false,
      dialog: false,
      isEdit: false,
      selectedItem: {},
      selectedItemIndex: -1, // Added missing data property
      searchFields: {
        label: '',
        value: '',
      },
      searchableItems: [],
      tableColumns: [
        {
          key: 'label', label: 'Label', sortable: true, searchable: true,
        },
        {
          key: 'value', label: 'Value', sortable: true, searchable: true,
        },
        { key: 'action', label: 'Action' },
      ],
    }
  },
  computed: {
    items() {
      return this.$store.getters['project/getQualifierOptions']?.(this.qualifierName) || []
    },
    filteredItems() {
      const activeSearches = Object.entries(this.searchFields).filter(([, value]) => value)
      let filtered = cloneDeep(this.searchableItems)

      if (activeSearches.length > 0) {
        filtered = filtered.filter(item => activeSearches.every(([key, val]) => item[key]?.toString().toLowerCase().includes(val.toLowerCase())))
      }

      return filtered
    },
    paginatedItems() {
      const start = (this.currentPage - 1) * this.perPage
      return this.filteredItems.slice(start, start + this.perPage)
    },

  },
  watch: {
    items: {
      handler(newItems) {
        if (Array.isArray(newItems)) {
          const mappedItems = newItems.map((item, originalIndex) => ({
            ...item,
            originalIndex, // Track original index
          }))

          this.searchableItems = cloneDeep(mappedItems)
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    handleSort(column) {
      if (this.sortBy === column) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = column
        this.sortDesc = false
      }

      // Sort the main searchableItems array directly
      this.searchableItems.sort((a, b) => {
        const aVal = a[this.sortBy] ?? ''
        const bVal = b[this.sortBy] ?? ''
        return this.sortDesc
          ? bVal.toString().localeCompare(aVal.toString())
          : aVal.toString().localeCompare(bVal.toString())
      })
    },

    filterItems() {
      this.loading = true
      this.currentPage = 1
      setTimeout(() => {
        this.loading = false
      }, 400)
    },

    addItem() {
      this.dialog = true
      this.isEdit = false
      this.selectedItem = {}
      this.selectedItemIndex = -1
    },

    // Fixed editItem method - now uses the original index
    editItem(item) {
      this.dialog = true
      this.isEdit = true
      // Remove originalIndex before editing to avoid data pollution
      const { originalIndex, ...itemWithoutIndex } = item
      this.selectedItem = cloneDeep(itemWithoutIndex)
      this.selectedItemIndex = originalIndex
    },

    // Fixed deleteItem method - now uses the original index
    deleteItem(item) {
      const { originalIndex } = item
      if (originalIndex !== undefined && originalIndex >= 0) {
        const newItems = [...this.items]
        newItems.splice(originalIndex, 1)
        this.$store.dispatch('project/updateQualifierOptions', {
          qualifierName: this.qualifierName,
          options: newItems,
        })
      }
    },

    // Fixed handleSave method
    handleSave(item) {
      this.dialog = false

      // Ensure all required properties are always present
      const cleanItem = {
        label: item.label || '',
        value: item.value || '',
      }

      const newItems = [...this.items]

      if (this.isEdit && this.selectedItemIndex !== -1) {
        // Update existing item
        newItems[this.selectedItemIndex] = cleanItem
      } else {
        // Add new item
        newItems.push(cleanItem)
      }

      this.$store.dispatch('project/updateQualifierOptions', {
        qualifierName: this.qualifierName,
        options: newItems,
      })

      // Reset selection
      this.selectedItemIndex = -1
    },
  },
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.per-page-selector {
  width: 90px;
}
</style>
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
