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
          :key="`doc-type-${item.id || item.DocType}-${index}`"
        >
          <b-td class="max-table-col-w">
            {{ item.docType }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.docCode }}
          </b-td>
          <b-td>
            <b-form-checkbox
              v-model="item.addToProcess"
              class="d-inline-block"
              @change="onChangeAddToProcess(item)"
            />
          </b-td>
          <b-td>
            <div class="d-flex justify-content-end gap-2">
              <feather-icon
                v-b-tooltip.hover
                icon="EditIcon"
                size="18"
                class="mr-1 cursor-pointer"
                title="Edit Doctype"
                @click="editItem(item)"
              />
              <feather-icon
                v-b-tooltip.hover
                icon="TrashIcon"
                size="18"
                class="cursor-pointer"
                title="Delete Doctype"
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
        cols="12"
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
    <project-doctype-form
      :model-value="dialog"
      :is-edit="isEdit"
      :doctypes-item="selectedItem"
      :existing-items="items"
      @update:modelValue="dialog = $event"
      @save="handleSave"
    />
    <import-doctype-dialog
      :model-value="importDialog"
      @update:modelValue="importDialog = $event"
      @import="handleImport"
    />
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BFormInput, BIcon,
  BTableSimple, BTbody, BTd, BTh, BThead, BTr,
  VBTooltip, BSpinner, BFormCheckbox,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'
import vSelect from 'vue-select'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import LocalPagination from '../LocalPagination.vue'
import ProjectDoctypeForm from './ProjectDoctypeForm.vue'
import ImportDoctypeDialog from './ImportDoctypeDialog.vue'

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
    BFormCheckbox,
    LocalPagination,
    ProjectDoctypeForm,
    ImportDoctypeDialog,
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
      importDialog: false,
      isEdit: false,
      isUpdatingCheckbox: false,
      selectedItem: {},
      searchFields: {
        docType: '',
        docCode: '',
      },
      searchableItems: [],
      tableColumns: [
        {
          key: 'docType', label: 'Doc Type', sortable: true, searchable: true,
        },
        {
          key: 'docCode', label: 'Doc Code', sortable: true, searchable: true,
        },
        {
          key: 'addToProcess', label: 'Add to Process', sortable: true, searchable: false,
        },
        { key: 'action', label: 'Action' },
      ],
    }
  },
  computed: {
    items() {
      return this.$store.getters['project/docTypes'] || []
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
        if (this.isUpdatingCheckbox) {
          this.isUpdatingCheckbox = false
          return
        }

        if (Array.isArray(newItems)) {
          const mappedItems = newItems.map((item, index) => ({
            ...item,
            addToProcess: item.addToProcess ?? false,
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
    bus.$on('project:add-doc-type', this.addItem)
    bus.$on('project:import-doctypes', this.openImportDialog)
    setTimeout(() => {
      this.loading = false
    }, 800)
  },
  beforeDestroy() {
    bus.$off('project:add-doc-type', this.addItem)
    bus.$off('project:import-doctypes', this.openImportDialog)
  },
  methods: {
    onChangeAddToProcess(item) {
      this.isUpdatingCheckbox = true

      const storeItem = this.items.find(e => e.docType === item.docType)
      if (storeItem) {
        storeItem.addToProcess = item.addToProcess
      }

      const searchableItem = this.searchableItems.find(e => e.docType === item.docType)
      if (searchableItem) {
        searchableItem.addToProcess = item.addToProcess
      }
    },
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
      this.$store.dispatch('project/updateDocTypes', newItems)
    },
    handleSave(item) {
      const newItems = [...this.items]

      if (this.isEdit && item.index !== undefined) {
        const { index, ...cleanItem } = item
        newItems[index] = cleanItem
      } else {
        newItems.unshift(item)
      }
      this.$store.dispatch('project/updateDocTypes', newItems)
      this.dialog = false
    },
    openImportDialog() {
      this.importDialog = true
    },
    handleImport(importedData) {
      // Replace all doctypes with imported data
      this.$store.dispatch('project/updateDocTypes', importedData)
      this.importDialog = false

      // Show success message
      this.$toast({
        component: ToastificationContent,
        props: {
          title: `Successfully imported ${importedData.length} doctype(s)`,
          icon: 'CheckIcon',
          variant: 'success',
        },
      })
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
