<template>
  <div>
    <!-- <pre>
      {{ displayedItems }}
    </pre> -->
    <b-table-simple
      hover
      responsive
    >
      <b-thead>
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
            />
          </b-th>
        </b-tr>
      </b-thead>
      <b-tbody>
        <b-tr
          v-for="(item, index) in displayedItems"
          :key="item.uid"
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
          <b-td>
            <div class="d-flex justify-content-end gap-2">
              <feather-icon
                v-b-tooltip.hover
                icon="EditIcon"
                size="18"
                class="mr-1 cursor-pointer"
                title="Edit Key"
                @click="editItem(item, index)"
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
        <b-tr v-if="!displayedItems.length">
          <b-td
            colspan="4"
            class="text-center text-muted"
          >
            No keys added yet
          </b-td>
        </b-tr>
      </b-tbody>
    </b-table-simple>

    <!-- Pagination Info -->
    <div
      v-if="filteredItems.length > perPage"
      class="d-flex justify-content-between align-items-center mt-1"
    >
      <small class="text-muted">
        Showing {{ displayedItems.length }} of {{ filteredItems.length }} keys
      </small>
      <b-button
        variant="link"
        size="sm"
        class="p-0"
        @click="toggleViewAll"
      >
        {{ showAll ? 'Show Less' : 'View All' }}
      </b-button>
    </div>

    <!-- Edit Modal -->
    <b-modal
      v-model="showEditModal"
      title="Edit Key"
      centered
      size="md"
      :no-close-on-backdrop="true"
      @ok="saveEdit"
    >
      <b-form>
        <!-- <pre>
          {{ editingItem }}
        </pre> -->
        <b-form-group
          label="Key Label"
          label-for="edit-keyLabel"
        >
          <b-form-input
            id="edit-keyLabel"
            v-model="editingItem.keyLabel"
            placeholder="Enter key label"
          />
        </b-form-group>
        <b-form-group
          label="Key Value"
          label-for="edit-keyValue"
        >
          <b-form-input
            id="edit-keyValue"
            v-model="editingItem.keyValue"
            placeholder="Enter key value"
          />
        </b-form-group>
        <b-form-group
          label="Type"
          label-for="edit-type"
        >
          <v-select
            id="edit-type"
            v-model="editingItem.type"
            :options="typeOptions"
            :clearable="false"
            placeholder="Select Type"
          />
        </b-form-group>
        <b-form-group
          label="Max Length"
          label-for="edit-maxLength"
        >
          <b-form-input
            id="edit-maxLength"
            v-model.number="editingItem.maxLength"
            type="number"
            placeholder="Enter Max Length"
          />
        </b-form-group>
        <b-form-group
          label="Min Length"
          label-for="edit-minLength"
        >
          <b-form-input
            id="edit-minLength"
            v-model.number="editingItem.minLength"
            type="number"
            placeholder="Enter Min Length"
          />
        </b-form-group>
      </b-form>
    </b-modal>
  </div>
</template>

<script>
import vSelect from 'vue-select'
import {
  BTableSimple,
  BThead,
  BTbody,
  BTr,
  BTh,
  BTd,
  BFormInput,
  BIcon,
  BButton,
  BModal,
  BForm,
  BFormGroup,
  VBTooltip,
} from 'bootstrap-vue'

export default {
  name: 'DataAssemblyProjectKeys',
  directives: { 'b-tooltip': VBTooltip },
  components: {
    vSelect,
    BTableSimple,
    BThead,
    BTbody,
    BTr,
    BTh,
    BTd,
    BFormInput,
    BIcon,
    BButton,
    BModal,
    BForm,
    BFormGroup,
  },
  props: {
    items: {
      type: Array,
      default: () => [],
    },
    perPage: {
      type: Number,
      default: 10,
    },
  },
  data() {
    return {
      sortBy: '',
      sortDesc: false,
      searchFields: {
        keyLabel: '',
        keyValue: '',
        type: '',
      },
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
          key: 'action', label: 'Action', sortable: false, searchable: false,
        },
      ],
      typeOptions: ['key', 'table', 'addressBlock', 'addressBlockPartial', 'lookupCode', 'compound'],
      showEditModal: false,
      editingItem: {},
      editingIndex: -1,
      showAll: false,
    }
  },
  computed: {
    filteredItems() {
      let filtered = [...this.items]

      // Apply search filters
      const activeSearches = Object.entries(this.searchFields).filter(([, value]) => value)
      if (activeSearches.length > 0) {
        filtered = filtered.filter(item => activeSearches.every(([key, val]) => {
          const itemValue = item[key] || ''
          return String(itemValue).toLowerCase().includes(val.toLowerCase())
        }))
      }

      // Apply sorting
      if (this.sortBy) {
        filtered.sort((a, b) => {
          const aVal = String(a[this.sortBy] || '')
          const bVal = String(b[this.sortBy] || '')
          return this.sortDesc
            ? bVal.localeCompare(aVal)
            : aVal.localeCompare(bVal)
        })
      }

      return filtered
    },
    paginatedItems() {
      return this.filteredItems.slice(0, this.perPage)
    },
    displayedItems() {
      return this.showAll ? this.filteredItems : this.paginatedItems
    },
  },
  methods: {
    toggleViewAll() {
      this.showAll = !this.showAll
    },
    handleSort(column) {
      if (this.sortBy === column) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = column
        this.sortDesc = false
      }
    },
    editItem(item, index) {
      this.editingItem = { ...item }
      this.editingIndex = index
      this.showEditModal = true
    },
    saveEdit() {
      if (this.editingIndex > -1) {
        this.$emit('update-item', {
          uid: this.editingItem.uid,
          item: { ...this.editingItem },
        })
      }
      this.showEditModal = false
      this.editingItem = {}
      this.editingIndex = -1
    },
    deleteItem(item) {
      this.$emit('delete-item', item.uid)
    },
  },
}
</script>

<style scoped>
.max-table-col-w {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
