<template>
  <div class="search-component">
    <!-- Header with title and buttons -->
    <div class="search-header mb-3">
      <!-- <h5 class="search-title mb-0">
        Search Organizations
      </h5> -->
      <div class="d-flex gap-2">
        <b-button
          variant="primary"
          size="sm"
          class="search-btn me-2"
          :disabled="isDisabled || !isSearchValid"
          aria-label="Search organizations"
          @click="performSearch"
        >
          <feather-icon
            icon="SearchIcon"
            size="14"
            class="me-1"
          />
          Search
        </b-button>
        <b-button
          variant="outline-secondary"
          size="sm"
          class="clear-btn"
          :disabled="isDisabled || !hasSearchValues"
          aria-label="Clear search fields"
          @click="clearSearch"
        >
          <feather-icon
            icon="XIcon"
            size="14"
            class="me-1"
          />
          Clear
        </b-button>
      </div>
    </div>

    <!-- Search input fields -->
    <b-row class="search-boxes g-3">
      <b-col md="3">
        <b-form-group
          label="Organization Name"
          label-for="org-name-input"
        >
          <b-form-input
            id="org-name-input"
            v-model="searchFields.orgName"
            placeholder="Search Organization Name"
            class="search-input"
            debounce="500"
            aria-describedby="org-name-help"
            @update="onFieldChange"
          />
        </b-form-group>
      </b-col>
      <b-col md="3">
        <b-form-group
          label="Address"
          label-for="org-name-input"
        >
          <b-form-input
            id="address-line1-name-input"
            v-model="searchFields.address_line1"
            placeholder="Search Address Line1"
            class="search-input"
            debounce="500"
            aria-describedby="address-line1-name-help"
            @update="onFieldChange"
          />
        </b-form-group>
      </b-col>

      <b-col md="3">
        <b-form-group
          label="Account Number"
          label-for="cw1-code-input"
        >
          <b-form-input
            id="cw1-code-input"
            v-model="searchFields.cw1_code"
            placeholder="Search Account Number"
            class="search-input"
            debounce="500"
            aria-describedby="cw1-code-help"
            @update="onFieldChange"
          />
        </b-form-group>
      </b-col>

      <b-col md="3">
        <b-form-group
          label="Address Short Code"
          label-for="short-code-input"
        >
          <b-form-input
            id="short-code-input"
            v-model="searchFields.short_code"
            placeholder="Search by address short code"
            class="search-input"
            debounce="500"
            aria-describedby="short-code-help"
            @update="onFieldChange"
          />
        </b-form-group>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import {
  BCol, BRow, BFormGroup, BFormInput, BButton,
} from 'bootstrap-vue'

export default {
  name: 'SearchInDdh',
  components: {
    BRow,
    BCol,
    BFormGroup,
    BFormInput,
    BButton,
  },
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      searchFields: {
        orgName: '',
        address_line1: '',
        cw1_code: '',
        short_code: '',
      },
    }
  },
  computed: {
    isDisabled() {
      return this.disabled
    },
    hasSearchValues() {
      return Object.values(this.searchFields).some(value => value.trim() !== '')
    },
    isSearchValid() {
      return this.hasSearchValues
    },
  },
  methods: {
    onFieldChange() {
      if (this.hasSearchValues) {
        this.performSearch()
      } else {
        this.clearSearch()
      }
    },
    performSearch() {
      // Send all data in filters object with correct field names
      const filters = {}

      // Map internal field names to API field names
      if (this.searchFields.orgName.trim() !== '') {
        filters.org_name = this.searchFields.orgName.trim()
      }
      if (this.searchFields.address_line1.trim() !== '') {
        filters.address_line1 = this.searchFields.address_line1.trim()
      }
      if (this.searchFields.cw1_code.trim() !== '') {
        filters.cw1_code = this.searchFields.cw1_code.trim()
      }
      if (this.searchFields.short_code.trim() !== '') {
        filters.short_code = this.searchFields.short_code.trim()
      }

      // Emit with only filters, page, and per_page - no query field
      this.$emit('search', {
        filters,
        page: 1,
        per_page: 100,
      })
    },
    clearSearch() {
      this.searchFields = {
        orgName: '',
        cw1_code: '',
        address_line1: '',
        short_code: '',
      }
      this.$emit('search', {
        filters: {},
        page: 1,
        per_page: 100,
      })
    },
  },
}
</script>

<style scoped>
.search-component {
  margin-bottom: 1.5rem;
}

.search-header {
  display: flex;
  justify-content: end;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e9ecef;
}

.search-title {
  color: #343a40;
  font-weight: 600;
  font-size: 1.25rem;
}

.search-btn,
.clear-btn {
  display: inline-flex;
  align-items: center;
  font-weight: 500;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.search-btn:disabled,
.clear-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.search-label {
  font-weight: 500;
  color: #343a40;
  font-size: 0.9rem;
  margin-bottom: 0.4rem;
}

.search-input {
  font-size: 0.875rem;
  border-radius: 0.25rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.15);
}

.search-boxes .col-md-4 {
  margin-bottom: 1rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .search-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .search-btn,
  .clear-btn {
    flex: 1;
    justify-content: center;
  }

  .search-label {
    font-size: 0.85rem;
  }

  .search-input {
    font-size: 0.85rem;
  }

  .search-title {
    font-size: 1.15rem;
  }
}
</style>
