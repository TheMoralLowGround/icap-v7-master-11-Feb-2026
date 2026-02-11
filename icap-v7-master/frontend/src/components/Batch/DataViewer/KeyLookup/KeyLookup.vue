<!--
 Organization: AIDocbuilder Inc.
 File: KeyLookup.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-20

 Description:
   This component provides an interface for executing key lookup operations based on user-defined queries. It allows users to
   input and manage multiple queries, run lookups, and display the resulting data. The component supports dynamic addition,
   deletion, and expansion of queries, along with error handling and status indicators during the lookup process.

 Main Features:
   - Display loading spinner and error message during data fetch operations.
   - Support for adding, deleting, and expanding queries.
   - Display results based on SQL queries and store the results.
   - Handle lookup execution with proper feedback and status management.
   - Supports integration with Vuex for global state management.

 Dependencies:
   - BootstrapVue for UI components (BAlert, BSpinner, BOverlay).
   - Axios for HTTP requests.
   - Lodash for deep cloning and comparison of data.
   - Vuex for state management related to lookup operations.

-->

<template>
  <b-overlay
    class="h-100"
    :show="executingLookup"
    :opacity="0.6"
  >
    <template #overlay>
        &nbsp;
    </template>

    <div
      class="lookup-container"
    >
      <div
        v-if="loading"
        class="text-center"
      >
        <b-spinner variant="primary" />
      </div>

      <b-alert
        variant="danger"
        :show="!loading && loadingError ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ loadingError }}
          </p>
        </div>
      </b-alert>

      <div
        v-if="!loading && !loadingError"
        class="lookup-content"
      >
        <query
          v-for="(query, index) of queries"
          ref="query"
          :key="index"
          v-model="queries[index]"
          :query-result-options="queryResultOptions[index]"
          :query-index="index"
          :expanded="queryExpandStatus[index]"
          @toogle-expanded="toogleQueryExpandStatus(index)"
          @delete="deleteQuery(index)"
        />
      </div>
    </div>
  </b-overlay>
</template>

<script>
import {
  BAlert, BSpinner, VBTooltip, BOverlay,
} from 'bootstrap-vue'
import axios from '@/rules-backend-axios'
import { isEqual, cloneDeep } from 'lodash'

import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import Query from './Query/Query.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    Query,
    BAlert,
    BSpinner,
    BOverlay,
  },
  props: {
    value: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      loadingError: null,
      table: null,
      queries: [],
      queryExpandStatus: [],
    }
  },
  computed: {
    out() {
      return cloneDeep(this.queries)
    },
    executingLookup: {
      get() {
        return this.$store.getters['lookup/executing']
      },
      set(value) {
        this.$store.commit('lookup/SET_EXECUTING', value)
      },
    },
    enableSubmit() {
      return this.queries.some(query => query.sql !== '')
    },
    queryResultOptions() {
      const indexWiseoptions = []
      let options = []
      this.queries.forEach((query, index) => {
        indexWiseoptions[index] = options
        if (query.table) {
          const tableColumns = this.$store.getters['lookup/tableColumns'](query.table)
          options = options.concat(tableColumns.map(tableColumn => ({
            label: `Query Result #${index + 1} - ${tableColumn.name}`,
            value: `<QR>${index}.${tableColumn.name}</QR>`,
          })))
        }
      })
      return indexWiseoptions
    },
    profileName() {
      return this.$store.getters['batch/batch'].definitionId
    },
  },
  watch: {
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
    enableSubmit() {
      this.$store.commit('lookup/SET_ENABlE_SUBMIT', this.enableSubmit)
    },
  },
  created() {
    bus.$on('dataView/addQueries', this.addQueries)
    bus.$on('dataView/runLookup', this.runLookup)
    this.setInternalState()
    this.initializeLookup()
  },
  destroyed() {
    bus.$off('dataView/addQueries', this.addQueries)
    bus.$off('dataView/runLookup', this.runLookup)
  },
  methods: {
    setInternalState() {
      this.queries = cloneDeep(this.value)
      this.queryExpandStatus = this.queries.map(() => true)
    },
    initializeLookup() {
      this.loading = true
      this.$store.dispatch('lookup/initialize')
        .then(() => {
          this.loadingError = null
          this.loading = false
        }).catch(error => {
          this.loadingError = error.message
          this.loading = false
        })
    },
    runLookup() {
      this.executingLookup = true

      axios.post('/run_lookup/', {
        queries: this.queries.map(query => ({
          sql: query.sql,
        })),
        definition_version: this.$store.getters['dataView/selectedDefinitionVersion'],
        keys: this.$store.getters['batch/selectedDocumentKeysForLookup'],
      }).then(res => {
        this.$store.commit('lookup/SET_RESULTS', res.data.query_results)
        this.executingLookup = false
      }).catch(error => {
        const message = error?.response?.data?.detail || 'Error executing lookup'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        if (error?.response?.data?.query_results) {
          this.$store.commit('lookup/SET_RESULTS', error.response.data.query_results)
        } else {
          this.$store.commit('lookup/SET_RESULTS', [])
        }
        this.executingLookup = false
      })
    },
    addQueries(count) {
      const defaultQuery = {
        table: null,
        group: {
          operator: 'AND',
          items: [{
            type: 'rule',
            data: {
              column: 'PROFILE_NAME',
              operator: '=',
              value: this.profileName,
              valueType: 'input',
            },
          }],
        },
        additionalKeys: {
          items: [],
        },
        sql: '',
      }

      const lastRowIndex = this.queries.length - 1
      const newItems = []
      const expandStatus = []
      for (let i = 0; i < count; i += 1) {
        newItems.push(cloneDeep(defaultQuery))
        expandStatus.push(true)
      }

      this.queries = this.queries.concat(newItems)
      this.queryExpandStatus = this.queryExpandStatus.concat(expandStatus)

      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },
    scrollToIndex(index) {
      this.$refs.query[index].$el.scrollIntoView()
    },
    deleteQuery(index) {
      this.queries.splice(index, 1)
      this.queryExpandStatus.splice(index, 1)
    },
    toogleQueryExpandStatus(index) {
      this.queryExpandStatus.splice(index, 1, !this.queryExpandStatus[index])
    },
  },
}
</script>

<style scoped>
.lookup-container {
    height: 100%;
    position: relative;
}

.lookup-content {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    overflow-y: auto;
}
</style>
