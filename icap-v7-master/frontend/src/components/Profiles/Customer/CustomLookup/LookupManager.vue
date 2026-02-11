<template>
  <div class="lookup-manager">
    <!-- <pre>
      {{ lookupItems }}
    </pre> -->
    <h4
      class="cursor-pointer pb-1"
      @click="showQuery = !showQuery"
    >
      Lookup Queries
      <feather-icon
        :icon="showQuery ? 'ChevronDownIcon' : 'ChevronUpIcon'"
        size="16"
        class="me-1"
      />
    </h4>
    <b-collapse
      v-model="showQuery"
      class="mb-3"
    >
      <validation-observer ref="lookupForm">
        <b-form @submit.prevent="runLookup">
          <div class="d-flex justify-content-start align-items-center mb-1 gap-2 mt-2">
            <b-button
              variant="outline-primary"
              type="button"
              @click="addLookup"
            >
              <feather-icon
                icon="PlusIcon"
                class="mr-25"
              />
              <span>Add Lookup</span>
            </b-button>

            <div
              v-if="hasLookupData"
              style="width: 120px;"
            >
              <v-select
                v-model="globalOperationType"
                :options="['OR', 'AND']"
                :clearable="false"
                placeholder="condition"
              />
            </div>

            <b-button
              v-if="hasLookupData"
              variant="primary"
              type="submit"
              :disabled="runningLookup"
            >
              <b-spinner
                v-if="runningLookup"
                small
                class="mr-25"
              />
              <feather-icon
                v-else
                icon="PlayIcon"
                class="mr-25"
              />
              <span>Run Lookup</span>
            </b-button>
            <b-button
              v-if="isLookupEnabled"
              variant="outline-danger"
              type="button"
              @click="removeLookup"
            >
              <span>Remove Applied Lookup</span>
            </b-button>
          </div>

          <div
            v-if="localLookupItems.length === 0 || localLookupItems.every(item => !item.query || item.query.length === 0)"
            class="text-center text-muted py-2 border rounded"
          >
            No lookups configured. Click "Add Lookup" to get started.
          </div>

          <!-- Nested loop: iterate tables, then queries -->
          <div
            v-for="(tableItem, tableIndex) in localLookupItems"
            :key="`table-${tableIndex}`"
          >
            <div
              v-for="(query, queryIndex) in tableItem.query"
              :key="`${tableIndex}-${queryIndex}`"
            >
              <lookup-item
                :value="query"
                :query-result-options="queryResultOptions"
                :query-index="queryIndex"
                @input="updateLookup(tableIndex, queryIndex, $event)"
                @delete="deleteLookup(tableIndex, queryIndex)"
              />
            </div>
          </div>
        </b-form>
      </validation-observer>
    </b-collapse>
  </div>
</template>

<script>
import {
  BCollapse,
  BButton,
  BSpinner,
  BForm,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { ValidationObserver } from 'vee-validate'
import { mapGetters } from 'vuex'
import { cloneDeep } from 'lodash'
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import LookupItem from './LookupItem.vue'

const defaultQuery = {
  queryOperationType: 'OR',
  queryData: [],
}

export default {
  components: {
    LookupItem,
    BCollapse,
    BButton,
    BSpinner,
    vSelect,
    ValidationObserver,
    BForm,
  },
  props: {
    queryResultOptions: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      localLookupItems: [],
      loading: false,
      errorMessage: null,
      showQuery: false,
      runningLookup: false,
    }
  },
  computed: {
    ...mapGetters('profile', ['lookupItems']),
    currentProcessName() {
      return this.$store.getters['profile/currentProcessName']
    },
    isLookupEnabled() {
      return this.$store.getters['lookup/isLookupEnabled']
    },
    tableOptions() {
      const allTables = this.$store.getters['lookup/tables'] || []
      return allTables.filter(t => t.toLowerCase().includes('custom_master'))
    },
    tableName() {
      const [firstTable] = this.tableOptions || []
      return firstTable || 'CUSTOM_MASTER'
    },
    hasLookupData() {
      return this.localLookupItems.some(item => item.query && item.query.length > 0)
    },
    globalOperationType: {
      get() {
        const tableItem = this.localLookupItems.find(item => item.table === this.tableName)
        return tableItem?.globalOperationType || 'OR'
      },
      set(value) {
        const tableItem = this.localLookupItems.find(item => item.table === this.tableName)
        if (tableItem) {
          tableItem.globalOperationType = value
          this.updateStore()
        }
      },
    },
    lookupPayload() {
      // Build the complete payload structure
      const tableItem = this.localLookupItems.find(item => item.table === this.tableName)
      if (!tableItem || !tableItem.query || tableItem.query.length === 0) {
        return null
      }

      return {
        table: tableItem.table,
        globalOperationType: tableItem.globalOperationType || 'OR',
        query: tableItem.query.map(q => ({
          queryData: q.queryData || [],
          queryOperationType: q.queryOperationType || 'OR',
        })),
      }
    },
  },
  watch: {
    lookupItems: {
      handler(val) {
        this.localLookupItems = cloneDeep(val)
        // Ensure structure is correct
        this.ensureStructure()
      },
      immediate: true,
    },
  },
  created() {
    this.lookupTableInitialized()

    // Listen for column updates from SearchTemplate
    bus.$on('profile/columnsUpdated', this.lookupTableInitialized)
  },
  destroyed() {
    this.$store.commit('lookup/SET_LOOKUP_ENABLED', false)

    // Clean up event listener
    bus.$off('profile/columnsUpdated', this.lookupTableInitialized)
  },
  methods: {
    lookupTableInitialized() {
      this.loading = true
      this.$store.dispatch('lookup/initialize', {
        processName: this.currentProcessName,
      })
        .then(() => {
          this.loading = false
        }).catch(error => {
          this.loading = false
          this.errorMessage = error?.data?.response?.error || 'Error loading lookups'
        })
    },
    ensureStructure() {
      // Ensure we always have the nested structure
      if (this.localLookupItems.length === 0) {
        this.localLookupItems = [{
          table: this.tableName,
          globalOperationType: 'OR',
          query: [],
        }]
      }

      // Convert old flat structure if exists
      this.localLookupItems = this.localLookupItems.map(item => {
        if (item.queryData && !item.query) {
          // Old structure, convert it
          return {
            // table: item.table || this.tableName,
            globalOperationType: item.globalOperationType || 'OR',
            query: [{
              queryqueryOperationType: item.queryqueryOperationType || 'OR',
              queryData: item.queryData,
            }],
          }
        }
        // Ensure globalOperationType exists in already nested structure
        if (!item.globalOperationType) {
          return {
            ...item,
            globalOperationType: 'OR',
          }
        }
        return item
      })
    },
    addLookup() {
      // Find if we already have a table entry
      let tableItem = this.localLookupItems.find(item => item.table === this.tableName)

      if (!tableItem) {
        // Create new table entry
        tableItem = {
          table: this.tableName,
          globalOperationType: 'OR',
          query: [],
        }
        this.localLookupItems.push(tableItem)
      }

      // Add new query to the table
      tableItem.query.push(cloneDeep(defaultQuery))
      this.updateStore()
    },
    updateLookup(tableIndex, queryIndex, queryItem) {
      this.localLookupItems[tableIndex].query[queryIndex] = cloneDeep(queryItem)
      this.updateStore()
    },
    deleteLookup(tableIndex, queryIndex) {
      this.localLookupItems[tableIndex].query.splice(queryIndex, 1)

      // If no queries left, remove the table entry
      if (this.localLookupItems[tableIndex].query.length === 0) {
        this.localLookupItems.splice(tableIndex, 1)
      }

      this.updateStore()
    },
    updateStore() {
      // Clean up: remove tables with no queries
      const cleanedItems = this.localLookupItems.filter(item => item.query && item.query.length > 0)
      this.$store.commit('profile/SET_LOOKUP_ITEMS', cloneDeep(cleanedItems))
    },
    removeLookup() {
      this.$emit('remove-lookup', { tableName: this.tableName })
      this.$store.commit('lookup/SET_LOOKUP_ENABLED', false)
    },
    async runLookup() {
      // Validate the form first
      const isValid = await this.$refs.lookupForm.validate()

      if (!isValid) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Validation Error',
            icon: 'AlertTriangleIcon',
            text: 'Please fill in all required fields (Column, Operator, and Value) before running the lookup.',
            variant: 'warning',
          },
        })
        return
      }

      if (!this.lookupPayload) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error',
            icon: 'AlertTriangleIcon',
            text: 'No lookup data to run',
            variant: 'warning',
          },
        })
        return
      }

      this.runningLookup = true
      try {
        this.$store.commit('lookup/SET_LOOKUP_ENABLED', true)
        // Get process name from profile store
        // const processName = this.$store.getters['profile/currentProcessName']

        // Emit event to parent SearchTemplate component to refresh table
        // Pass the lookup payload to be used in the API request
        this.$emit('refresh-table', {
          tableName: this.tableName,
          lookupData: this.lookupPayload,
        })

        // Show success message
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Success',
            icon: 'CheckIcon',
            text: `Lookup executed successfully. Refreshing ${this.tableName} table...`,
            variant: 'success',
          },
        })
      } catch (error) {
        const errorMessage = error?.response?.data?.error || error?.response?.data?.detail || 'Error running lookup'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error',
            icon: 'AlertTriangleIcon',
            text: errorMessage,
            variant: 'danger',
          },
        })
      } finally {
        this.runningLookup = false
      }
    },
  },
}
</script>

<style scoped>
.lookup-manager {
  padding: 15px;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
