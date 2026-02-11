<template>
  <div>
    <div
      v-if="title"
      class="d-flex justify-content-between align-items-center"
    >
      <h2>
        {{ title }}
      </h2>
      <b-button
        v-if="!viewOnly"
        variant="primary"
        @click="dialog = true"
      >
        {{ `Add ${title}` }}
      </b-button>
    </div>
    <b-card-body>
      <b-table-simple
        responsive
        striped
        :busy="loading"
        :class="{ 'table-busy': loading }"
      >
        <colgroup>
          <col
            v-for="field in computedFields"
            :key="field.key"
            :style="{ width: field.width }"
          >
        </colgroup>

        <b-thead>
          <b-tr>
            <template v-for="field in computedFields">
              <b-th
                v-if="field.key !== 'select' && field.sortable"
                :key="field.key"
                :aria-sort="sortField === field.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                @click="toggleSort(field)"
              >
                {{ field.label }}
              </b-th>

              <b-th
                v-if="field.key !== 'select' && !field.sortable"
                :key="field.key"
              >
                {{ field.label }}
              </b-th>
            </template>
          </b-tr>
          <b-tr>
            <template
              v-for="field of computedFields"
            >
              <b-th :key="`header-${field.key}`">
                <div
                  v-if="field.key === 'label'"
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
                :colspan="computedFields.length"
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
              :key="`row-${index}`"
            >
              <template v-for="field in computedFields">
                <b-td
                  :key="`cell-${field.key}-${index}`"
                  class="max-table-col-w"
                >
                  <template v-if="field.key === 'action' && !viewOnly">
                    <div class="d-flex gap-3 justify-content-end">
                      <feather-icon
                        v-b-tooltip.hover
                        title="Delete Document Vendor"
                        icon="Trash2Icon"
                        class="cursor-pointer text-danger"
                        size="16"
                        @click="deleteItem(item.index)"
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
      <!-- <div
        v-if="!loading"
        class="mx-2 mt-1 mb-2"
      >
        <detailed-pagination
          :per-page="perPage"
          :current-page="currentPage"
          :total-records="filteredItems.length"
          :local-records="paginatedItems.length"
          @page-changed="pageChanged"
        />
      </div> -->

      <multi-select-form
        v-if="options"
        v-model="dialog"
        :title="`Add ${title}`"
        :options="options"
        :selected-items="items"
        @save="addItems"
      />
    </b-card-body>
  </div>
</template>

<script>
import {
  BCardBody, BButton, BTableSimple, BFormInput, VBTooltip,
  BSpinner, BTr, BThead, BTbody, BTh, BTd,
} from 'bootstrap-vue'
import { cloneDeep } from 'lodash'
// import DetailedPagination from '@/components/UI/DetailedPagination.vue'

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
    BCardBody,
    BButton,
    BTableSimple,
    BFormInput,
    BSpinner,
    // DetailedPagination,
    MultiSelectForm: () => import('./MultiSelectForm.vue'),
  },
  props: {
    items: {
      type: Array,
      required: false,
      default: () => [],
    },
    options: {
      type: Array,
      default: null,
    },
    title: {
      type: String,
      required: false,
      default: '',
    },
    label: {
      type: String,
      required: false,
      default: '',
    },
    viewOnly: {
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
      sortField: 'label',
      sortDesc: false,
      searchFields: {
        label: '',
      },
      fields: [
        {
          key: 'label',
          label: this.label,
          sortable: true,
          class: 'text-left',
        },
        {
          key: 'action',
          label: 'Action',
          sortable: false,
          class: 'text-center',
        },
      ],
      filteredItems: [],
    }
  },
  computed: {
    computedFields() {
      return this.fields.map(field => ({
        ...field,
        label: field.key === 'label' ? this.label : field.label,
        sortable: field.sortable,
        thClass: field.sortable ? 'sortable' : '',
      }))
    },
    // paginatedItems() {
    //   const start = (this.currentPage - 1) * this.perPage
    //   const end = start + this.perPage
    //   return this.filteredItems.slice(start, end)
    // },
  },
  watch: {
    items: {
      handler() {
        this.setInitialState()
      },
      immediate: true,
    },
    searchFields: {
      handler() {
        this.onColumnSearch()
      },
      deep: true,
    },
  },
  methods: {
    // pageChanged(page) {
    //   this.currentPage = page
    // },
    addItems(keys) {
      this.$emit('update:items', keys)
    },
    deleteItem(index) {
      const newItems = [...this.items]
      newItems.splice(index, 1)
      this.$emit('update:items', newItems)
    },
    onColumnSearch() {
      const filteredItems = cloneDeep(this.searchableItems)

      // eslint-disable-next-line no-unused-vars
      const activeSearches = Object.entries(this.searchFields)?.filter(([_, value]) => value !== '' && value !== null && value !== undefined)
      if (activeSearches.length === 0) {
        this.filteredItems = filteredItems
        // SHOW ALL ITEMS WITHOUT PAGINATION
        this.renderedItems = this.filteredItems
        return
      }

      this.filteredItems = filteredItems?.filter(item => activeSearches.every(([key, searchValue]) => {
        const itemValue = item[key]?.toString().toLowerCase()
        return itemValue && itemValue.includes(searchValue.toLowerCase())
      }))
      // SHOW ALL FILTERED ITEMS WITHOUT PAGINATION
      this.renderedItems = this.filteredItems
    },
    onSort(ctx) {
      this.sortField = ctx.sortBy
      this.sortDesc = ctx.sortDesc
    },
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
    setInitialState() {
      this.loading = true

      const mappedItems = this.items
        ?.filter(item => item.vendor !== undefined)
        ?.map((item, index) => ({
          value: item.vendor,
          label: item.vendor,
          index,
        }))

      this.searchableItems = cloneDeep(mappedItems)
      this.filteredItems = cloneDeep(mappedItems) // Initialize filteredItems
      // SHOW ALL ITEMS WITHOUT PAGINATION
      this.renderedItems = this.filteredItems

      this.$nextTick(() => {
        this.loading = false
      })
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-good-table.scss';
.sortable {
  cursor: pointer;
  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
}
</style>
