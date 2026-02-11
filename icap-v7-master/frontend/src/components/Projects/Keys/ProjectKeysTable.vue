<template>
  <div>
    <div class="d-flex justify-content-end mb-2">
      <ImportYamlFile
        v-if="showYamlModal"
        v-model="showYamlModal"
        :project-id="projectId"
        @imported="yamlImported"
      />
    </div>
    <!-- Table -->
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
            colspan="7"
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
          :key="item.keyValue + '-' + index"
        >
          <b-td class="max-table-col-w">
            {{ item.keyLabel }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.keyValue }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.type }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ item.qualifier }}
          </b-td>
          <!-- <b-td class="max-table-col-w">
            {{ item.prompt }}
          </b-td> -->
          <b-td class="max-table-col-w">
            {{ (item.project_prompt && item.project_prompt.DocClass) || '' }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ (item.project_prompt && item.project_prompt.Field_Description) || '' }}
          </b-td>
          <b-td class="max-table-col-w">
            {{ (item.project_prompt && item.project_prompt.Rules_Description) || '' }}
          </b-td>
          <b-td>
            <b-form-checkbox
              v-model="item.required"
              class="d-inline-block"
              @change="onChangeRequired(item)"
            />
          </b-td>
          <b-td>
            <b-form-checkbox
              v-model="item.addToProcess"
              :disabled="item.required"
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
                title="Edit Key"
                @click="editItem(item)"
              />
              <feather-icon
                v-b-tooltip.hover
                icon="TrashIcon"
                size="18"
                class="cursor-pointer"
                title="Delete Key"
                @click="deleteItem(item.index)"
              />
            </div>
          </b-td>
        </b-tr>
        <b-tr v-if="!loading && !filteredItems.length">
          <b-td
            colspan="7"
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
          class="per-page-selector d-inline-block mx-20"
        />
        <label class="ml-1">entries</label>
      </div>
    </local-pagination>

    <project-keyForm
      :model-value="dialog"
      :is-edit="isEdit"
      :project-key-item="selectedItem"
      :existing-items="items"
      @update:modelValue="dialog = $event"
      @save="handleSave"
    />
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BFormInput,
  BIcon,
  BTableSimple,
  BTbody, BTd,
  BTh,
  BThead, BTr,
  VBTooltip,
  BSpinner,
  // BButton,
  BFormCheckbox,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'
import vSelect from 'vue-select'
import LocalPagination from '../LocalPagination.vue'
import ProjectKeyForm from './ProjectKeyForm.vue'
import ImportYamlFile from '../DataAssembly/ImportYamlFile.vue'

export default {
  directives: { 'b-tooltip': VBTooltip },
  components: {
    BIcon, BFormInput, BTableSimple, BThead, BTr, BTh, BTbody, BTd, vSelect, BSpinner, LocalPagination, ProjectKeyForm, BFormCheckbox, ImportYamlFile,
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
        keyLabel: '',
        keyValue: '',
        type: '',
        qualifier: '',
        modType: '',
        compoundKeys: '',
        DocClass: '',
        Rules_Description: '',
        Field_Description: '',
      },
      showYamlModal: false,
      isUpdatingCheckbox: false,
      searchableItems: [],
      tableColumns: [
        {
          key: 'keyLabel', label: 'Key Label', sortable: true, searchable: true,
        },
        {
          key: 'keyValue', label: 'Key Value', sortable: true, searchable: true,
        },
        {
          key: 'type', label: 'Type', sortable: true, searchable: true,
        },
        {
          key: 'qualifier', label: 'Qualifier', sortable: true, searchable: true,
        },
        // {
        //   key: 'prompt', label: 'Prompt', sortable: true, searchable: true,
        // },
        {
          key: 'DocClass', label: 'Doc Class', sortable: true, searchable: true,
        },
        {
          key: 'Field_Description', label: 'Field Description', sortable: true, searchable: true,
        },
        {
          key: 'Rules_Description', label: 'Rules Description', sortable: true, searchable: true,
        },
        {
          key: 'required', label: 'Required', sortable: true, searchable: false,
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
      return this.$store.getters['project/keyItems']
    },

    filteredItems() {
      const activeSearches = Object.entries(this.searchFields).filter(([, value]) => value)
      let filtered = cloneDeep(this.searchableItems)

      if (activeSearches.length > 0) {
        filtered = filtered.filter(item => activeSearches.every(([key, val]) => {
          // Handle nested project_prompt fields
          let itemValue = ''
          if (key === 'DocClass' || key === 'Field_Description' || key === 'Rules_Description') {
            itemValue = (item.project_prompt && item.project_prompt[key]) || ''
          } else {
            itemValue = item[key] || ''
          }
          return String(itemValue).toLowerCase().includes(val.toLowerCase())
        }))
      }

      return filtered
    },

    paginatedItems() {
      const start = (this.currentPage - 1) * this.perPage
      return this.filteredItems.slice(start, start + this.perPage)
    },
    projectId() {
      return this.$route && this.$route.params && this.$route.params.id
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
    bus.$on('project:add-key', this.addItem)
    bus.$on('project:upload-model', this.openModelUploadDialog)
    setTimeout(() => {
      this.loading = false
    }, 800)
  },
  beforeDestroy() {
    bus.$off('project:add-key', this.addItem)
    bus.$off('project:upload-model', this.openModelUploadDialog)
  },
  methods: {
    openModelUploadDialog() {
      this.showYamlModal = true
    },

    onChangeRequired(item) {
      this.isUpdatingCheckbox = true
      const storeItem = this.items.find(e => e.keyValue === item.keyValue)

      if (storeItem) {
        storeItem.required = item.required
        // If required is set to true, automatically set addToProcess to true
        if (item.required) {
          storeItem.addToProcess = true
        }
      }

      const searchableItem = this.searchableItems.find(e => e.keyValue === item.keyValue)
      if (searchableItem) {
        searchableItem.required = item.required
        // If required is set to true, automatically set addToProcess to true
        if (item.required) {
          searchableItem.addToProcess = true
        }
      }
    },
    onChangeAddToProcess(item) {
      this.isUpdatingCheckbox = true
      const storeItem = this.items.find(e => e.keyValue === item.keyValue)

      if (storeItem) {
        storeItem.addToProcess = item.addToProcess
      }

      const searchableItem = this.searchableItems.find(e => e.keyValue === item.keyValue)
      if (searchableItem) {
        searchableItem.addToProcess = item.addToProcess
      }
    },
    yamlImported() {
      this.showYamlModal = false
      this.fetchProject()
    },
    async fetchProject() {
      await this.$store.dispatch('project/fetchProjectDetail', this.$route.params.id)
    },
    handleSort(column) {
      if (this.sortBy === column) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = column
        this.sortDesc = false
      }

      // Sort the searchableItems array
      this.searchableItems.sort((a, b) => {
        // Handle nested project_prompt fields
        let aVal = ''
        let bVal = ''
        if (column === 'DocClass' || column === 'Field_Description' || column === 'Rules_Description') {
          aVal = String((a.project_prompt && a.project_prompt[column]) || '')
          bVal = String((b.project_prompt && b.project_prompt[column]) || '')
        } else {
          aVal = String(a[column] || '')
          bVal = String(b[column] || '')
        }

        return this.sortDesc
          ? bVal.localeCompare(aVal)
          : aVal.localeCompare(bVal)
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
      this.$store.dispatch('project/updateKeyItems', newItems)
    },

    handleSave(item) {
      this.dialog = false

      const newItems = [...this.items]

      if (this.isEdit && item.index !== undefined) {
        const { index, ...cleanItem } = item
        newItems[index] = cleanItem
      } else {
        newItems.unshift(item)
      }

      this.$store.dispatch('project/updateKeyItems', newItems)
    },
  },
}
</script>

<style scoped>
.per-page-selector {
  width: 90px;
}
</style>
<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
