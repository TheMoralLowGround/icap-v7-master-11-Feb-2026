<template>
  <div>
    <div class="d-flex justify-content-between align-items-center">
      <h2>Customers</h2>

      <div>
        <b-button
          variant="primary"
          @click="openDialog"
        >
          Add Customer
        </b-button>
        <b-button
          variant="success"
          class="ml-1"
          :disabled="submitting"
          @click="$emit('submit')"
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

    <b-card>
      <b-table-simple
        responsive
        striped
        :busy="loading"
        :class="{ 'table-busy': loading }"
      >
        <colgroup>
          <col
            v-for="field in fields"
            :key="field.key"
            :style="{ width: field.width }"
          >
        </colgroup>

        <b-thead>
          <b-tr>
            <template v-for="field in fields">
              <b-th
                v-if="field.sortable"
                :key="field.key"
                :aria-sort="sortField === field.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                @click="toggleSort(field)"
              >
                {{ field.label }}
              </b-th>

              <b-th
                v-else
                :key="field.key"
              >
                {{ field.label }}
              </b-th>
            </template>
          </b-tr>
          <b-tr>
            <template v-for="field of fields">
              <b-th :key="`header-${field.key}`">
                <div
                  v-if="field.searchable"
                  class="d-flex flex-column"
                >
                  <b-form-input
                    v-model="searchFields[field.key]"
                    :placeholder="`Search ${field.label}`"
                    trim
                    :disabled="loading"
                  />
                </div>
              </b-th>
            </template>
          </b-tr>
        </b-thead>

        <b-tbody>
          <template v-if="loading">
            <b-tr>
              <b-td
                :colspan="fields.length"
                class="text-center text-primary my-2"
              >
                <b-spinner class="align-middle" />
                <strong>Loading...</strong>
              </b-td>
            </b-tr>
          </template>

          <template v-else>
            <b-tr
              v-for="(item, index) in renderedItems"
              :key="`row-${item.id || item.tempId || index}`"
            >
              <template v-for="field in fields">
                <b-td :key="`cell-${field.key}-${index}`">
                  <template v-if="field.key === 'action'">
                    <div class="d-flex gap-3 justify-content-end">
                      <feather-icon
                        v-b-tooltip.hover
                        title="Edit Customer"
                        icon="EditIcon"
                        class="cursor-pointer text-primary"
                        size="16"
                        @click="editItem(item)"
                      />
                      <feather-icon
                        v-b-tooltip.hover
                        title="Delete Customer"
                        icon="Trash2Icon"
                        class="cursor-pointer text-danger"
                        size="16"
                        @click="deleteItem(item.id || item.tempId)"
                      />
                    </div>
                  </template>

                  <template v-else>
                    {{ item[field.key] || '' }}
                  </template>
                </b-td>
              </template>
            </b-tr>
          </template>
        </b-tbody>
      </b-table-simple>
      <div
        v-if="!loading && renderedItems.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>
    </b-card>

    <process-customer-modal
      v-model="dialog"
      :editing-item="editingItem"
      :editing-id="editingId"
      @submit="handleSubmit"
      @close="closeDialog"
    />
  </div>
</template>

<script>
import { cloneDeep } from 'lodash'
import {
  BCard,
  BButton,
  BTableSimple,
  BFormInput,
  VBTooltip,
  BSpinner,
  BTr,
  BTbody,
  BThead,
  BTh,
  BTd,
} from 'bootstrap-vue'
import ProcessCustomerModal from './ProcessCustomerModal.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BTr,
    BThead,
    BTbody,
    BTh,
    BTd,
    BCard,
    BButton,
    BTableSimple,
    BFormInput,
    BSpinner,
    ProcessCustomerModal,
  },
  props: {
    value: {
      type: Array,
      default: () => [],
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
      filteredItems: [],
      searchFields: {
        name: '',
      },
      sortField: 'name',
      sortDesc: false,
      fields: [
        {
          key: 'name',
          label: 'Name',
          sortable: true,
          searchable: true,
          width: '80%',
        },
        {
          key: 'action',
          label: 'Actions',
          width: '20%',
        },
      ],
      editingItem: null,
      editingId: null,
    }
  },
  computed: {
    items() {
      return this.value || []
    },
  },
  watch: {
    items: {
      handler() {
        this.setInitialState()
      },
      immediate: true,
      deep: true,
    },
    searchFields: {
      handler() {
        this.onColumnSearch()
      },
      deep: true,
    },
  },
  methods: {
    toggleSort(header) {
      if (header.sortable) {
        if (this.sortField === header.key) {
          this.sortDesc = !this.sortDesc
        } else {
          this.sortField = header.key
          this.sortDesc = false
        }
        this.onColumnSearch()
      }
    },
    openDialog() {
      this.dialog = true
    },
    editItem(item) {
      this.dialog = true
      this.editingId = item.id || item.tempId // Use id or tempId for unsaved items
      this.editingItem = cloneDeep(item)
    },
    handleSubmit(customerData) {
      if (this.editingId) {
        // Update existing customer - find by ID or tempId (safe with search/sort)
        const updatedItems = this.items.map(item => {
          const itemKey = item.id || item.tempId
          if (itemKey === this.editingId) {
            return {
              ...item,
              name: customerData.name,
            }
          }
          return item
        })
        this.$emit('input', updatedItems)
      } else {
        // Add new customer - use tempId for local tracking, Django will assign real ID on save
        const newCustomer = {
          tempId: Date.now(), // Temporary ID for local edit/delete before save
          name: customerData.name,
        }
        this.$emit('input', [...this.items, newCustomer])
      }

      this.closeDialog()
    },
    closeDialog() {
      this.dialog = false
      this.editingItem = null
      this.editingId = null
    },
    deleteItem(itemKey) {
      // Delete by ID or tempId (safe with search/sort)
      const updatedItems = this.items.filter(item => {
        const key = item.id || item.tempId
        return key !== itemKey
      })
      this.$emit('input', updatedItems)
      // No need to call setInitialState - watcher handles it
    },
    onColumnSearch() {
      this.loading = true
      const filteredItems = cloneDeep(this.searchableItems)
      const activeSearches = Object.entries(this.searchFields)?.filter(
        // eslint-disable-next-line no-unused-vars
        ([_, value]) => value !== '' && value !== null && value !== undefined,
      )

      let result = filteredItems?.filter(item => activeSearches.every(([key, searchValue]) => {
        const itemValue = item[key]?.toString().toLowerCase()
        return itemValue && itemValue.includes(searchValue.toLowerCase())
      }))

      // Apply sorting
      if (this.sortField) {
        result = result.sort((a, b) => {
          const aValue = a[this.sortField]?.toString().toLowerCase()
          const bValue = b[this.sortField]?.toString().toLowerCase()
          if (aValue < bValue) return this.sortDesc ? 1 : -1
          if (aValue > bValue) return this.sortDesc ? -1 : 1
          return 0
        })
      }

      this.filteredItems = result
      this.renderedItems = this.filteredItems
      this.loading = false
    },
    setInitialState() {
      // Use original item IDs (from backend) or tempId (for unsaved items)
      this.searchableItems = this.items.map(item => ({
        id: item.id,
        tempId: item.tempId,
        name: item.name || '',
      }))

      this.filteredItems = [...this.searchableItems]
      this.renderedItems = this.filteredItems
      this.onColumnSearch()
    },
  },
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.table-busy {
  opacity: 0.55;
  pointer-events: none;
}
</style>
