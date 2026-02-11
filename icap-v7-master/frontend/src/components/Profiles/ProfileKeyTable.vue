<template>
  <div>
    <div
      v-if="title"
      class="d-flex justify-content-between align-items-center"
    >
      <h2>
        {{ title }}
      </h2>
      <div>
      <b-button
        variant="primary"
        @click="dialog = true"
      >
        {{ `Add ${title}` }}
      </b-button>
      <b-button
        variant="success"
        :disabled="submitting"
        @click="$emit('submit')"
        class="ml-1"
      >
        <b-spinner
          v-if="submitting"
          small
          class="mr-50"
        />
        Save
      </b-button>
      </div>
    </div>
    <b-card-body>

      <div class="table-responsive">
        <b-table-simple
          :class="{
            'table-busy': loading
          }"
          class="profiles-table"
        >
          <colgroup>
            <col
              v-for="(tableColumn) of headers"
              :key="tableColumn.key"
              :style="{ width: tableColumn.width + '%' }"
            >
          </colgroup>
          <b-thead>
            <b-tr>
              <template
                v-for="tableColumn of headers"
              >
                <!-- <b-th
                  v-if="tableColumn.key === 'select'"
                  :key="tableColumn.key"
                >
                  <b-form-checkbox
                    v-model="allRecordsSeleted"
                    :disabled="profiles.length === 0"
                    @change="toggleRecordsSelection"
                  />
                </b-th> -->

                <b-th
                  v-if="tableColumn.key !== 'select' && tableColumn.sortable"
                  :key="tableColumn.key"
                  :aria-sort="sortBy === tableColumn.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                  @click="toggleSort(tableColumn)"
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
                v-for="tableColumn of headers"
              >
                <b-th
                  v-if="tableColumn.searchable"
                  :key="tableColumn.key"
                >
                  <b-form>
                    <b-form-input
                      v-model="searchFields[tableColumn.key]"
                      trim
                      :disabled="loading"
                      placeholder="Search"
                      @keydown.enter.prevent
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
            <template v-for="(item) of renderedItems">
              <b-tr
                :key="`main-row-${item.label}`"
              >
                <!-- <b-td>
                  <b-form-checkbox
                    v-model="selectedRecords"
                    :value="report.name"
                  />
                </b-td> -->
                <b-td class="max-table-col-w">
                  {{ item.label }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ item.keyValue }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ item.type }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ item.DocClass }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ item.Field_Description }}
                </b-td>
                <b-td class="max-table-col-w">
                  {{ item.Rules_Description }}
                </b-td>
                <b-td>
                  <div class="text-nowrap">
                    <feather-icon
                      v-b-tooltip.hover
                      title="Edit Key"
                      icon="EditIcon"
                      class="cursor-pointer text-primary"
                      size="16"
                      @click="editKey(item)"
                    />
                    <feather-icon
                      v-b-tooltip.hover
                      title="Precedence"
                      icon="ListIcon"
                      class="ml-1 cursor-pointer text-primary"
                      size="16"
                      @click="openSettings(item)"
                    />

                    <feather-icon
                      v-if="!item.required"
                      v-b-tooltip.hover
                      icon="TrashIcon"
                      size="18"
                      class="ml-1 cursor-pointer text-danger"
                      title="Delete Key"
                      @click.stop="deleteItem(item)"
                    />
                  </div>
                </b-td>
              </b-tr>
            </template>

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
        v-if="!loading && renderedItems.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>
      <!-- <div
        v-if="!loading"
        class="mx-2 mt-1 mb-2"
      >
        <detailed-pagination
          :per-page="perPage"
          :current-page="currentPage"
          :total-records="totalRecords"
          :local-records="renderedItems.length"
          @page-changed="pageChanged"
        />
      </div> -->

    </b-card-body>

    <add-profile-key
      v-model="dialog"
      :title="`Add ${title}`"
      :key-options="projectKeyItems"
      :selected-items="selectedKeyValues"
      @save="addItems"
      @modal-closed="dialog = false"
    />
    <profile-key-settings
      v-if="selectedKey"
      :title="`${selectedKey.label} Doc Types`"
      :selected-key="selectedKey"
      @save="saveKeySettings"
      @modal-closed="selectedKey = null"
    />
    <profile-key-form
      v-if="editingKey"
      :model-value="editDialog"
      :profile-key-item="editingKey"
      :project-key-items="projectKeyItems"
      @save="saveEditedKey"
      @modal-closed="closeEditDialog"
    />
  </div>
</template>

<script>
import {
  BCardBody,
  BButton,
  BTableSimple,
  BFormInput,
  VBTooltip,
  BForm,
  BThead,
  BTr,
  BTbody,
  BTh,
  BTd,
  BSpinner,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'
// import DetailedPagination from '@/components/UI/DetailedPagination.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BCardBody,
    BButton,
    BTableSimple,
    BFormInput,
    BForm,
    BThead,
    BTr,
    BTbody,
    BTh,
    BTd,
    BSpinner,
    AddProfileKey: () => import('./AddProfileKey.vue'),
    ProfileKeySettings: () => import('./ProfileKeySettings.vue'),
    ProfileKeyForm: () => import('./ProfileKeyForm.vue'),
    // DetailedPagination,
  },
  props: {
    items: {
      type: Array,
      required: true,
      default: () => [], // Add default empty array
      validator: value => Array.isArray(value), // Add array validation
    },
    projectKeyItems: {
      type: Array,
      required: true,
      default: () => [], // Add default empty array
      validator: value => Array.isArray(value), // Add array validation
    },
    title: {
      type: String,
      default: 'Keys',
    },
    submitting: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialog: false,
      loading: false,
      searchableItems: [],
      renderedItems: [],
      // currentPage: 1,
      // perPage: 10,
      sortBy: 'label',
      sortDesc: false,
      headers: [
        {
          key: 'label',
          label: 'Key Label',
          align: 'start',
          sortable: true,
          searchable: true,
          width: 15,
        },
        {
          key: 'keyValue',
          label: 'Key Value',
          align: 'start',
          sortable: true,
          searchable: true,
          width: 15,
        },
        {
          key: 'type',
          label: 'Type',
          align: 'start',
          sortable: true,
          searchable: true,
          width: 10,
        },
        {
          key: 'DocClass',
          label: 'Doc Class',
          align: 'start',
          sortable: true,
          searchable: true,
          width: 15,
        },
        {
          key: 'Field_Description',
          label: 'Field Description',
          align: 'start',
          sortable: true,
          searchable: true,
          width: 25,
        },
        {
          key: 'Rules_Description',
          label: 'Rules Description',
          align: 'start',
          sortable: true,
          searchable: true,
          width: 25,
        },
        {
          key: 'action',
          label: 'Actions',
          align: 'center',
          sortable: false,
          width: 10,
        },
      ],
      searchFields: {
        label: '',
        type: '',
        DocClass: '',
        Field_Description: '',
        Rules_Description: '',
      },
      localItems: [], // This will store our actual items
      keys: [], // This will persist across steps
      filteredItems: [],
      selectedKey: null,
      editDialog: false,
      editingKey: null,
    }
  },
  computed: {
    totalRecords() {
      return this.searchableItems.length
    },
    isSorted() {
      return header => this.sortBy === header.key
    },
    getSortIcon() {
      return this.sortDesc ? 'ArrowDownIcon' : 'ArrowUpIcon'
    },
    tableItems() {
      return Array.isArray(this.localItems)
        ? this.localItems.map((item, index) => {
          // For backward compatibility, expose process_prompt fields at top level for display
          const processPrompt = item.process_prompt || {}
          return {
            ...item,
            index,
            // Override with process_prompt values if they exist
            DocClass: processPrompt.DocClass || item.DocClass || '',
            Field_Description: processPrompt.Field_Description || item.Field_Description || '',
            Rules_Description: processPrompt.Rules_Description || item.Rules_Description || '',
          }
        })
        : []
    },
    selectedKeyValues() {
      return Array.isArray(this.localItems)
        ? this.localItems.map(item => item.keyValue)
        : []
    },
  },
  watch: {
    searchFields: {
      handler() {
        this.onColumnSearch()
      },
      deep: true,
    },
    items: {
      handler(newItems) {
        // Update localItems when items prop changes (e.g., when project changes)
        this.localItems = this.ensureKeyFields(cloneDeep(newItems))
        this.searchableItems = this.tableItems
        this.onColumnSearch()
      },
      deep: true,
    },
  },
  created() {
    this.localItems = this.ensureKeyFields(cloneDeep(this.items))
    this.searchableItems = this.tableItems
    this.onColumnSearch()
  },
  methods: {
    ensureKeyFields(items) {
      // Ensure all keys have precedence and process_prompt fields initialized
      // Similar to how process_prompt is always present in the key objects
      return items.map(item => ({
        ...item,
        precedence: item.precedence || [],
        process_prompt: item.process_prompt || {
          DocClass: '',
          Field_Description: '',
          Rules_Description: '',
        },
      }))
    },
    saveKeySettings(modifiedKeyItem) {
      const found = this.localItems.find(e => e.keyValue === modifiedKeyItem.keyValue)

      if (found) {
        this.$set(found, 'precedence', modifiedKeyItem.precedence)
      }

      this.$store.commit('profile/SET_SELECTED_KEYS', [...this.localItems])
      this.searchableItems = this.tableItems
      this.onColumnSearch()
    },
    addItems(selectedKeyValues) {
      const existingKeys = this.localItems.filter(i => selectedKeyValues.includes(i.keyValue))
      const existingKeyValues = existingKeys.map(e => e.keyValue)
      const newKeyValues = selectedKeyValues.filter(e => !existingKeyValues.includes(e))

      const newKeys = []

      this.projectKeyItems.forEach(projectKey => {
        if (newKeyValues.includes(projectKey.keyValue)) {
          newKeys.push({
            label: projectKey.keyLabel,
            type: projectKey.type,
            keyValue: projectKey.keyValue,
            required: projectKey.required ?? false,
            addToProcess: projectKey.addToProcess ?? false,
            precedence: [],
            process_prompt: {
              DocClass: projectKey.project_prompt?.DocClass || '',
              Field_Description: projectKey?.project_prompt?.Field_Description || '',
              Rules_Description: projectKey?.project_prompt?.Rules_Description || '',
            },
          })
        }
      })

      this.localItems = [...existingKeys, ...newKeys]

      this.$store.commit('profile/SET_SELECTED_KEYS', this.localItems)

      this.searchableItems = this.tableItems
      this.onColumnSearch()
    },
    editKey(item) {
      this.editDialog = true
      this.editingKey = cloneDeep(item)
    },
    openSettings(item) {
      this.selectedKey = item
    },
    saveEditedKey(updatedKey) {
      // Find and update the key in localItems
      const index = this.localItems.findIndex(k => k.keyValue === updatedKey.keyValue)
      if (index !== -1) {
        // Use Vue.set or splice to ensure reactivity
        this.$set(this.localItems, index, updatedKey)
      }

      // Update Vuex store with complete object (create new array reference)
      this.$store.commit('profile/SET_SELECTED_KEYS', [...this.localItems])

      // Force update table state with new references
      this.searchableItems = this.tableItems.map(item => ({ ...item }))
      this.onColumnSearch()

      // Close dialog
      this.closeEditDialog()
    },
    closeEditDialog() {
      this.editDialog = false
      this.editingKey = null
    },
    deleteItem(itemToDelete) {
      // Update Vuex store
      this.$store.commit('profile/REMOVE_KEY', itemToDelete.keyValue)

      // Update local state
      this.localItems = this.localItems.filter(
        item => item.keyValue !== itemToDelete.keyValue,
      )

      // Update table state
      this.searchableItems = this.tableItems
      this.onColumnSearch()
    },
    toggleSort(header) {
      if (header.sortable) {
        if (this.sortBy === header.key) {
          this.sortDesc = !this.sortDesc
        } else {
          this.sortBy = header.key
          this.sortDesc = false
        }
        this.onColumnSearch()
      }
    },
    // pageChanged(page) {
    //   this.currentPage = page
    //   this.applyPagination()
    // },
    onColumnSearch() {
      const filteredItems = cloneDeep(this.searchableItems)

      // eslint-disable-next-line no-unused-vars
      const activeSearches = Object.entries(this.searchFields)?.filter(([_, value]) => value !== '' && value !== null && value !== undefined)

      let result = filteredItems?.filter(item => activeSearches.every(([key, searchValue]) => {
        const itemValue = item[key]?.toString().toLowerCase()
        return itemValue && itemValue.includes(searchValue.toLowerCase())
      }))

      // Apply sorting
      if (this.sortBy) {
        result = result.sort((a, b) => {
          const aValue = a[this.sortBy]?.toString().toLowerCase()
          const bValue = b[this.sortBy]?.toString().toLowerCase()
          if (aValue < bValue) return this.sortDesc ? 1 : -1
          if (aValue > bValue) return this.sortDesc ? -1 : 1
          return 0
        })
      }

      this.filteredItems = result
      this.renderedItems = this.filteredItems
      this.loading = false
    },

    // PAGINATION METHOD COMMENTED OUT
    // applyPagination() {
    //   const start = (this.currentPage - 1) * this.perPage
    //   const end = start + this.perPage
    //   this.renderedItems = this.filteredItems.slice(start, end)
    // },
  },
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.hover {
  transition: opacity 0.5s ease;
  opacity: 1;
  cursor: pointer;
}
.hover:hover {
  opacity: 0.5;
}
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
.profiles-table td {
  padding: 0.4rem 0.5rem;
  vertical-align: baseline;
}

.profiles-table th {
  padding: 0.8rem 0.5rem;
}

.profiles-table tr.has-row-details {
  border-bottom: none;
}

.table-responsive {
  overflow-x: auto;
  white-space: normal;
}
</style>
