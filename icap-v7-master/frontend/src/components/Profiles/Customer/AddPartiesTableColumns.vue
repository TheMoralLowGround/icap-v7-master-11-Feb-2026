<template>
  <b-modal
    :visible="value"
    :title="`Add/Remove Columns - ${tableName}`"
    no-close-on-backdrop
    size="lg"
    centered
    ok-title="Save"
    @ok="onSave"
    @hidden="$emit('modal-closed')"
    @cancel="onCancel"
  >
    <div class="d-flex flex-column gap-y-3">
      <div class="d-flex justify-content-end">
        <b-button
          v-if="safeColumnOptions.length && internalSelected.length !== safeColumnOptions.length"
          size="sm"
          variant="link"
          :class="{ 'mr-2': internalSelected.length }"
          @click="selectAll"
        >
          Select All
        </b-button>
        <b-button
          v-if="internalSelected.length > 0"
          size="sm"
          variant="link"
          class="text-danger"
          @click="clearAll"
        >
          Clear
        </b-button>
      </div>

      <label class="text-muted small">Select Columns</label>

      <!-- Custom dropdown implementation -->
      <div
        v-click-outside="closeDropdown"
        class="custom-dropdown-wrapper"
      >
        <!-- Display field with selected count -->
        <div
          class="custom-dropdown-search"
          :class="{ 'dark-mode': isDark }"
        >
          <b-form-input
            ref="searchInput"
            v-model="searchQuery"
            :placeholder="searchPlaceholder"
            @click="handleInputClick"
            @focus="handleInputFocus"
            @keydown.esc="closeDropdown"
          />
        </div>

        <!-- Dropdown options -->
        <div
          v-if="showDropdown"
          class="custom-dropdown-options"
          :class="{ 'dark-mode': isDark }"
          @click.stop
        >
          <div class="custom-dropdown-options-list">
            <div
              v-for="option in filteredSearchOptions"
              :key="option.value"
              class="custom-dropdown-option"
              :class="{
                'selected': internalSelected.includes(option.value),
                'dark-mode': isDark,
              }"
              @click="toggleOption(option)"
            >
              <span
                v-if="internalSelected.includes(option.value)"
                class="mr-2"
              >✓</span>
              {{ option.text }}
            </div>

            <div
              v-if="filteredSearchOptions.length === 0"
              class="custom-dropdown-no-results"
            >
              No matching options found
            </div>
          </div>
        </div>

        <div class="mx-2">
          <span class="text-success">{{ internalSelected.length || 0 }} {{ internalSelected.length === 1 ? 'column' : 'columns' }}</span> selected out of
          <span class="text-primary">{{ safeColumnOptions.length || 0 }} columns</span>
        </div>
      </div>
    </div>
  </b-modal>
</template>

<script>
import {
  BModal,
  BButton,
  BFormInput,
} from 'bootstrap-vue'
import useAppConfig from '@core/app-config/useAppConfig'
import { computed } from '@vue/composition-api'

export default {
  setup() {
    const { skin } = useAppConfig()

    const isDark = computed(() => skin.value === 'dark')

    return { skin, isDark }
  },
  components: {
    BModal,
    BButton,
    BFormInput,
  },
  directives: {
    clickOutside: {
      bind(el, binding, vnode) {
        // eslint-disable-next-line no-param-reassign
        el.clickOutsideEvent = function handleClickOutside(event) {
          if (!(el === event.target || el.contains(event.target))) {
            vnode.context[binding.expression](event)
          }
        }
        document.body.addEventListener('click', el.clickOutsideEvent)
      },
      unbind(el) {
        document.body.removeEventListener('click', el.clickOutsideEvent)
      },
    },
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    tableName: {
      type: String,
      default: '',
    },
    columnOptions: {
      type: Array,
      default: () => [],
    },
    projectKeyItems: {
      type: Array,
      default: () => [],
    },
    selectedColumns: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      internalSelected: [],
      showDropdown: false,
      searchQuery: '',
    }
  },
  computed: {
    safeColumnOptions() {
      // Filter projectKeyItems based on party/table name
      // Only show keys where:
      // 1. type === 'addressBlockPartial'
      // 2. keyValue starts with tableName (case-insensitive)
      if (this.projectKeyItems && this.projectKeyItems.length > 0 && this.tableName) {
        const tableNameLower = this.tableName.toLowerCase()

        return this.projectKeyItems.filter(item => {
          if (!item || !item.keyValue) return false

          const keyValueLower = item.keyValue.toLowerCase()
          return (
            item.type === 'addressBlockPartial'
            && keyValueLower.startsWith(tableNameLower)
          )
        }).map(item => ({
          key: item.keyValue,
          label: item.label || item.keyValue,
        }))
      }

      // Fallback to columnOptions if projectKeyItems not available
      return (this.columnOptions || []).filter(col => col && (col.key || col.column_name))
    },
    filteredOptions() {
      return this.safeColumnOptions.map(col => ({
        value: col.key || col.column_name,
        text: col.label || col.column_name,
      }))
    },
    filteredSearchOptions() {
      if (!this.searchQuery) return this.filteredOptions

      const query = this.searchQuery.toLowerCase()
      return this.filteredOptions.filter(option => option.text.toLowerCase().includes(query))
    },
    searchPlaceholder() {
      return this.internalSelected.length
        ? `${this.internalSelected.length} columns selected`
        : 'Search or select columns...'
    },
  },
  watch: {
    selectedColumns: {
      handler(newVal) {
        if (!Array.isArray(newVal)) return
        this.internalSelected = [...newVal]
      },
      immediate: true,
    },
    value(newVal) {
      if (newVal) {
        this.syncSelectedColumns()
      }
    },
  },
  methods: {
    handleInputClick() {
      this.showDropdown = true
      this.$nextTick(() => {
        this.$refs.searchInput.focus()
      })
    },
    handleInputFocus() {
      this.showDropdown = true
    },
    toggleOption(option) {
      const index = this.internalSelected.indexOf(option.value)
      if (index > -1) {
        this.internalSelected.splice(index, 1)
      } else {
        this.internalSelected.push(option.value)
      }
    },
    selectAll() {
      this.internalSelected = this.safeColumnOptions.map(col => col.key || col.column_name)
      this.showDropdown = false
    },
    clearAll() {
      this.internalSelected = []
      this.showDropdown = false
    },
    onSave() {
      this.$emit('save', {
        tableName: this.tableName,
        columns: this.internalSelected,
      })
      this.showDropdown = false
      this.$emit('modal-closed')
    },
    onCancel() {
      this.syncSelectedColumns()
      this.showDropdown = false
    },
    syncSelectedColumns() {
      if (!Array.isArray(this.selectedColumns)) return
      this.internalSelected = [...this.selectedColumns]
    },
    closeDropdown() {
      this.showDropdown = false
      this.searchQuery = ''
    },
  },
}
</script>

<style scoped>
.custom-dropdown-search input:focus {
  border-color: #7367f0;
  box-shadow: 0 0 0 0.2rem rgba(115, 103, 240, 0.25);
}

.dark-mode .custom-dropdown-search input:focus {
  border-color: #7367f0;
  box-shadow: 0 0 0 0.2rem rgba(115, 103, 240, 0.5);
}

.custom-dropdown-search {
  position: relative;
  z-index: 1;
}

.custom-dropdown-search input {
  cursor: pointer;
}

.custom-dropdown-options {
  position: absolute;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  background-color: white;
  z-index: 1000;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  margin-top: 0.25rem;
}

/* Dark mode styles */
.custom-dropdown-search.dark-mode input {
  background-color: #283046;
  border-color: #3b4253;
  color: #d0d2d6;
}

.custom-dropdown-options.dark-mode {
  background-color: #283046;
  border-color: #3b4253;
}

.text-muted {
  color: #6c757d;
}

/* Custom dropdown styles */
.custom-dropdown-wrapper {
  position: relative;
  margin-bottom: 1rem;
}

.custom-dropdown-option {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.custom-dropdown-option.selected {
  background-color: #7367f0;
  color: white;
}

.custom-dropdown-option.selected:hover {
  background-color: #5d50e8;
  color: white;
}

.custom-dropdown-option:hover:not(.selected) {
  background-color: #e0ddfa;
}

/* Dark mode styles */
.custom-dropdown-options.dark-mode {
  background-color: #283046;
  border-color: #3b4253;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.3);
}

.custom-dropdown-option.dark-mode {
  color: #d0d2d6;
}

.custom-dropdown-option.dark-mode:hover:not(.selected) {
  background-color: #3b4253;
}

.custom-dropdown-option.dark-mode.selected {
  background-color: #7367f0;
  color: white;
}

.custom-dropdown-option.dark-mode.selected:hover {
  background-color: #5d50e8;
  color: white;
}

.custom-dropdown-no-results {
  padding: 1rem;
  text-align: center;
  color: #6c757d;
}
</style>
