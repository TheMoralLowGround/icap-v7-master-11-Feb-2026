<template>
  <div>
    <!-- Table -->
    <b-table-simple
      :class="{ 'table-busy': loading }"
      hover
      responsive
    >
      <b-thead>
        <b-tr>
          <b-th
            v-for="column in tableColumns"
            :key="'header-' + column.key"
            :aria-sort="column.sortable && sortBy === column.key ? (sortDesc ? 'descending' : 'ascending') : 'none'"
            class="cursor-pointer"
            @click="column.sortable && handleSort(column.key)"
          >
            <div
              class="d-flex  align-items-center"
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
              debounce="200"
              @input="filterItems"
            />
          </b-th>
        </b-tr>
      </b-thead>

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
          :key="`mapped-key-${item.id || item.mappedKey}-${index}`"
        >
          <b-td class="max-table-col-w">
            {{ item.mappedKey }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.keyLabel }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.qualifierValue }}
          </b-td>
          <b-td>
            <div class="d-flex justify-content-end gap-2">
              <feather-icon
                v-b-tooltip.hover
                icon="EditIcon"
                size="18"
                class="mr-1 cursor-pointer"
                title="Edit Mapped Key"
                @click="editItem(item)"
              />
              <feather-icon
                v-b-tooltip.hover
                icon="TrashIcon"
                size="18"
                class="cursor-pointer"
                title="Delete Mapped Key"
                @click="deleteItem(item.index)"
              />
            </div>
          </b-td>
        </b-tr>

        <b-tr v-if="!loading && !filteredItems.length">
          <b-td
            class="text-center text-muted"
            colspan="3"
          >
            No matching records
          </b-td>
        </b-tr>
      </b-tbody>
    </b-table-simple>

    <!-- Pagination -->
    <local-pagination
      :per-page="perPage"
      :total="filteredItems.length"
      :local-length="paginatedItems.length"
      :current-page="currentPage"
      @page-changed="currentPage = $event"
    >
      <div
        class="d-flex align-items-center justify-content-end"
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

    <!-- Mapped Key Dialog -->
    <project-mapped-keyForm
      :model-value="dialog"
      :is-edit="isEdit"
      :mapped-key-item="selectedItem"
      @update:modelValue="dialog = $event"
      @save="handleSave"
    />
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BFormInput, BIcon,
  BTableSimple, BTbody, BTd, BTh, BThead, BTr,
  VBTooltip, BSpinner,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'
import vSelect from 'vue-select'
import LocalPagination from '../LocalPagination.vue'
import ProjectMappedKeyForm from './ProjectMappedKeyForm.vue'

export default {
  directives: { 'b-tooltip': VBTooltip },
  components: {
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTbody,
    BFormInput,
    BTd,
    BIcon,
    vSelect,
    BSpinner,
    LocalPagination,
    ProjectMappedKeyForm,
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
      searchFields: {
        mappedKey: '',
        keyLabel: '',
      },
      searchableItems: [],
      tableColumns: [
        {
          key: 'mappedKey', label: 'Mapped Key', sortable: true, searchable: true,
        },
        {
          key: 'keyLabel', label: 'Key Label', sortable: true, searchable: true,
        },
        {
          key: 'qualifierValue', label: 'Qualifier Value', sortable: true, searchable: true,
        },
        { key: 'action', label: 'Action' },
      ],
    }
  },

  computed: {
    items() {
      return this.$store.getters['project/mappedKeys']
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
          const mappedItems = newItems.map((item, index) => ({
            ...item,
            index,
          }))
          this.searchableItems = cloneDeep(mappedItems)
        }
      },
      deep: true,
      immediate: true,
    },
  },

  created() {
    this.loading = true
    bus.$on('project:add-mapped-key', this.addItem)
    setTimeout(() => {
      this.loading = false
    }, 800)
  },

  beforeDestroy() {
    bus.$off('project:add-mapped-key', this.addItem)
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
    },

    editItem(item) {
      this.dialog = true
      this.isEdit = true
      this.selectedItem = cloneDeep(item)
    },

    deleteItem(index) {
      const newItems = [...this.items]
      newItems.splice(index, 1)
      this.$store.dispatch('project/updateMappedKeys', newItems)
    },

    handleSave(item) {
      const newItems = [...this.items]

      if (this.isEdit && item.index !== undefined) {
        const { index, ...cleanItem } = item
        newItems[index] = cleanItem
      } else {
        newItems.push(item)
      }

      this.$store.dispatch('project/updateMappedKeys', newItems)
      this.dialog = false
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
.table-busy {
  opacity: 0.6;
  pointer-events: none;
}
</style>
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
