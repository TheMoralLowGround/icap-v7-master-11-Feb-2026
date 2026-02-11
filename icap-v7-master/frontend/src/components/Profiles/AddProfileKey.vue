<template>
  <b-modal
    :visible="value"
    :title="title"
    no-close-on-backdrop
    size="lg"
    centered
    ok-title="Add"
    @ok="onSaveKey"
    @hidden="$emit('modal-closed')"
    @cancel="onCancel"
  >
    <div class="d-flex flex-column gap-y-3">
      <div class="d-flex justify-content-end">
        <b-button
          v-if="safeKeyOptions.length && internalSelected.length !== safeKeyOptions.length"
          size="sm"
          variant="link"
          :class="{ 'mr-2': internalSelected.length }"
          @click="selectAll"
        >
          Select All
        </b-button>
        <b-button
          v-if="internalSelected.length > requiredKeys.length"
          size="sm"
          variant="link"
          class="text-danger"
          @click="clearAll"
        >
          Clear
        </b-button>
      </div>

      <label class="text-muted small">Select Keys</label>

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
                'dark-mode': isDark && !option.required,
                'disabled': option.required,
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
          <span class="text-success">{{ internalSelected.length || 0 }} {{ internalSelected.length === 1 ? 'key' : 'keys' }}</span> selected out of
          <span class="text-primary">{{ safeKeyOptions.length || 0 }} keys</span>
        </div>
      </div>
    </div>

    <div
      v-if="errorMessage"
      class="my-4 px-4 py-2 bg-light-danger text-danger rounded"
    >
      {{ errorMessage }}
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
    options: {
      type: Array,
      default: () => [],
    },
    keyOptions: {
      type: Array,
      default: () => [],
    },
    selectedItems: {
      type: Array,
      default: () => [],
    },
    title: {
      type: String,
      default: 'Add New Key',
    },
  },
  data() {
    return {
      errorMessage: null,
      internalSelected: [],
      showDropdown: false,
      searchQuery: '',
    }
  },
  computed: {
    safeKeyOptions() {
      return (this.keyOptions || []).filter(opt => opt && opt.keyValue && opt.keyLabel)
    },
    filteredOptions() {
      return this.safeKeyOptions.map(opt => ({
        value: opt.keyValue,
        text: opt.keyLabel,
        addToProcess: opt.addToProcess ?? false,
        required: opt.required ?? false,
      }))
    },
    filteredSearchOptions() {
      if (!this.searchQuery) return this.filteredOptions

      const query = this.searchQuery.toLowerCase()
      return this.filteredOptions.filter(option => option.text.toLowerCase().includes(query))
    },
    searchPlaceholder() {
      return this.internalSelected.length
        ? `${this.internalSelected.length} keys selected`
        : 'Search or select keys...'
    },
    selectDefaultKeys: {
      get() {
        return this.$store.state.profile?.selectDefaultKeys || false
      },
      set(value) {
        this.$store.commit('profile/updateSelectDefaultKeys', value)
      },
    },
    requiredKeys() {
      return this.safeKeyOptions.filter(opt => opt.required).map(opt => opt.keyValue)
    },
  },
  watch: {
    selectedItems: {
      handler(newVal) {
        if (!Array.isArray(newVal)) return
        this.internalSelected = [...newVal]
      },
      immediate: true,
    },
    value(newVal) {
      if (newVal) {
        this.syncSelectedItems()
      }
    },
    selectDefaultKeys() {
      this.selectDefaultKeysInitially()
    },
  },
  created() {
    this.selectDefaultKeysInitially()
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
      if (option.required) return

      const index = this.internalSelected.indexOf(option.value)
      if (index > -1) {
        this.internalSelected.splice(index, 1)
      } else {
        this.internalSelected.push(option.value)
      }
    },
    selectAll() {
      this.internalSelected = this.safeKeyOptions.map(opt => opt.keyValue)
      this.showDropdown = false
    },
    clearAll() {
      this.internalSelected = this.requiredKeys
      this.showDropdown = false
    },
    selectAllDefaultKeys() {
      this.internalSelected = this.safeKeyOptions.filter(opt => opt.addToProcess).map(opt => opt.keyValue)
      this.showDropdown = false
    },
    onSaveKey() {
      this.$emit('save', this.internalSelected)
      this.showDropdown = false
      this.$emit('modal-closed')
    },
    onCancel() {
      this.syncSelectedItems()
      this.showDropdown = false
    },
    syncSelectedItems() {
      if (!Array.isArray(this.selectedItems)) return
      this.internalSelected = [...this.selectedItems]
    },
    closeDropdown() {
      this.showDropdown = false
      this.searchQuery = ''
    },
    selectDefaultKeysInitially() {
      if (this.selectDefaultKeys) {
        this.selectDefaultKeys = false
        this.selectAllDefaultKeys()
        this.onSaveKey()
      }
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
.custom-dropdown-search{
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

.bg-light-danger {
  background-color: rgba(220, 53, 69, 0.1);
}
.text-muted {
  color: #6c757d;
}

/* Custom dropdown styles */
.custom-dropdown-wrapper {
  position: relative;
  margin-bottom: 1rem;
}

.custom-dropdown-display {
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  padding: 0.375rem 0.75rem;
  cursor: pointer;
  min-height: calc(1.5em + 0.75rem + 2px);
  background-color: white;
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
.custom-dropdown-display.dark-mode {
  background-color: #283046;
  border-color: #3b4253;
  color: #d0d2d6;
}

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

.custom-dropdown-option.disabled, .custom-dropdown-option.disabled:hover {
  background-color: black;
  color: white;
}
</style>
