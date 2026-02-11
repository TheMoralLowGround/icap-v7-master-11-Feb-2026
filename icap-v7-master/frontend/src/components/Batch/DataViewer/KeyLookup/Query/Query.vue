<!--
 Organization: AIDocbuilder Inc.
 File: Query.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component represents an individual query in the query builder interface, displaying a toggleable section
   for editing the query's table, group, additional keys, and SQL query. It handles dynamic updates to query
   data and generates the corresponding SQL query based on user input. The component supports expanding and
   collapsing the query details section and integrates with child components for managing groups and additional keys.

 Features:
   - Displays a toggleable query section with SQL query generation.
   - Allows dynamic selection of a table, group, and additional keys.
   - Generates SQL query based on selected table and conditions.
   - Integrates with child components for managing query groups and additional keys.
   - Includes tooltips for interactive icons like add and delete.

 Dependencies:
   - `QueryGroup`: A child component for managing query groups.
   - `AdditionalKeys`: A child component for managing additional key selections.
   - `BootstrapVue` for UI components and tooltips.
   - `VueSelect` for table and query column selections.
   - `Lodash` for deep cloning and data comparison.

-->

<template>
  <b-card
    class="border-secondary"
  >
    <div
      class="d-flex align-items-center"
      style="column-gap:10px;"
    >
      <div>
        <feather-icon
          v-if="!expanded"
          icon="ChevronRightIcon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="$emit('toogle-expanded')"
        />
        <feather-icon
          v-if="expanded"
          icon="ChevronDownIcon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="$emit('toogle-expanded')"
        />
      </div>
      <h5 class="mb-0">
        Query #{{ queryIndex + 1 }}
      </h5>
      <div>
        <feather-icon
          v-b-tooltip.hover
          title="Delete Query"
          icon="Trash2Icon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="$emit('delete')"
        />
      </div>
    </div>

    <div
      v-if="expanded"
      class="mt-50"
    >
      <div style="width:350px;">
        <b-form-group label="Table">
          <v-select
            ref="tableOptions"
            v-model="queryData.table"
            :options="tableOptions"
            @open="scrollToSelected"
          />
        </b-form-group>
      </div>

      <query-group
        v-model="queryData.group"
        :table-columns="tableColumns"
        :depth="0"
        :query-result-options="queryResultOptions"
      />

      <div style="padding-top: 15px;">
        <additional-keys
          v-model="queryData.additionalKeys"
          :table-columns="tableColumns"
          :depth="0"
          :query-result-options="queryResultOptions"
        />
      </div>

      <div
        v-if="sqlQuery"
        class="my-1"
      >
        <div>SQL:</div>
        <b-alert
          class="my-50"
          variant="primary"
          show
        >
          <div class="alert-body">
            <p>
              {{ sqlQuery }}
            </p>
          </div>
        </b-alert>
      </div>
    </div>
  </b-card>
</template>

<script>
import {
  BFormGroup, BAlert, BCard, VBTooltip,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'
import QueryGroup from './QueryGroup.vue'
import AdditionalKeys from './AdditionalKeys.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BFormGroup,
    BAlert,
    vSelect,
    QueryGroup,
    BCard,
    AdditionalKeys,
  },
  props: {
    queryIndex: {
      type: Number,
      required: true,
    },
    value: {
      type: Object,
      required: true,
    },
    queryResultOptions: {
      type: Array,
      required: true,
    },
    expanded: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      queryData: {},
    }
  },
  computed: {
    out() {
      const out = cloneDeep(this.queryData)
      out.sql = this.sqlQuery
      return out
    },
    tableOptions() {
      return this.$store.getters['lookup/tables']
    },
    tableColumns() {
      const { table } = this.queryData
      if (!table) {
        return []
      }

      return this.$store.getters['lookup/tableColumns'](table)
    },
    sqlQuery() {
      const { table } = this.queryData
      let sqlQuery = ''
      if (!table) {
        return sqlQuery
      }
      sqlQuery = `SELECT * FROM "${table}"`
      const parsedCondition = this.parseGroup(this.queryData.group)
      if (parsedCondition !== '') {
        sqlQuery += ` WHERE ${parsedCondition}`
      }
      return sqlQuery
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
  },
  created() {
    this.setInternalState()
  },
  methods: {
    // Initializes the query data from the parent component's `value` prop.
    setInternalState() {
      this.queryData = cloneDeep(this.value)
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs?.tableOptions?.$refs?.dropdownMenu

        const selectedIndex = this.tableOptions.indexOf(this.queryData.table)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.tableOptions.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
    // Recursively parses a query group to generate its condition string.
    parseGroup(group) {
      const rules = []
      group.items.forEach(groupItem => {
        let rule = ''
        if (groupItem.type === 'rule') {
          rule = this.parseRule(groupItem.data)
        } else if (groupItem.type === 'group') {
          rule = this.parseGroup(groupItem.data)
          if (rule !== '') {
            rule = `( ${rule} )`
          }
        }
        if (rule !== '') {
          rules.push(rule)
        }
      })
      return rules.join(` ${group.operator} `)
    },
    // Parses individual rule conditions and formats them for SQL query generation.
    parseRule(rule) {
      let ruleString = ''

      if (!rule.column || !rule.operator || !rule.value) {
        return ruleString
      }

      let ruleValue = rule.value
      if (rule.valueType === 'input') {
        ruleValue = `<I>${rule.value}</I>`
      }

      if (rule.operator === 'ILIKE') {
        ruleString = `LOWER(${rule.column}) LIKE LOWER('${ruleValue}')`
      } else if (rule.operator === 'FUZZY MATCH') {
        ruleString = `UTL_MATCH.JARO_WINKLER_SIMILARITY(LOWER(${rule.column}), LOWER('${ruleValue}')) > 93`
      } else {
        ruleString = `"${rule.column}" ${rule.operator} '${ruleValue}'`
      }

      return ruleString
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
