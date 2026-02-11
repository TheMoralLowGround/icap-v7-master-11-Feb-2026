<!--
 Organization: AIDocbuilder Inc.
 File: QueryGroup.vue
 Version: 6.0

 Authors:
   - Ali - Initial implementation

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component represents a query group in the query builder interface, allowing the user to add rules or subgroups
   for more complex query construction. Each group can contain multiple conditions (rules) or other subgroups. It supports
   dynamic addition and deletion of rules and subgroups, as well as selection of logical operators (AND/OR) for grouping.
   The component is recursive, meaning a group can contain other groups, allowing for hierarchical query structures.

 Features:
   - Adds and deletes query rules and subgroups within a group.
   - Supports logical operators (AND/OR) for grouping conditions.
   - Recursive component structure allows nested query groups.
   - Uses tooltips for interactive icons like add, delete, and logical operator selection.

 Dependencies:
   - `QueryItem`: A child component for managing individual query rules.
   - `BootstrapVue` for UI components and tooltips.
   - `Lodash` for deep cloning and data comparison.

-->

<template>
  <div
    class="query-group"
    :class="{
      'border-primary': depth % 2 === 0,
      'border-secondary': depth % 2 !== 0
    }"
  >
    <div
      class="d-flex align-items-center query-group-actions"
    >
      <div>
        <b-form-select
          v-model="queryData.operator"
          :options="['AND', 'OR']"
          :disabled="queryData.items.length <= 1"
        />
      </div>
      <div>
        <feather-icon
          v-b-tooltip.hover
          title="Add Rule"
          icon="PlusIcon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="addItem('rule')"
        />
      </div>
      <div>
        <feather-icon
          v-b-tooltip.hover
          title="Add Group"
          icon="PlusCircleIcon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="addItem('group')"
        />
      </div>
      <div v-if="depth !== 0">
        <feather-icon
          v-b-tooltip.hover
          title="Delete Group"
          icon="Trash2Icon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="$emit('delete')"
        />
      </div>
    </div>

    <div
      v-for="(item, itemIndex) of queryData.items"
      :key="itemIndex"
    >
      <query-item
        v-if="item.type === 'rule' "
        v-model="queryData.items[itemIndex].data"
        :table-columns="tableColumns"
        :query-result-options="queryResultOptions"
        @delete="deleteItem(itemIndex)"
      />

      <div
        v-if="item.type === 'group'"
        class="my-50"
      >
        <query-group
          v-model="queryData.items[itemIndex].data"
          :table-columns="tableColumns"
          :depth="depth+1"
          :query-result-options="queryResultOptions"
          @delete="deleteItem(itemIndex)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { VBTooltip, BFormSelect } from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import QueryItem from './QueryItem.vue'

const defaultRuleItem = {
  type: 'rule',
  data: {
    column: null,
    operator: null,
    valueType: 'column',
    value: null,
  },
}

export default {
  name: 'QueryGroup',
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    QueryItem,
    BFormSelect,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    tableColumns: {
      type: Array,
      required: true,
    },
    depth: {
      type: Number,
      required: true,
    },
    queryResultOptions: {
      type: Array,
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
      return cloneDeep(this.queryData)
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
    setInternalState() {
      this.queryData = cloneDeep(this.value)
    },
    addItem(type) {
      let item = null
      if (type === 'rule') {
        item = cloneDeep(defaultRuleItem)
      } else if (type === 'group') {
        item = {
          type: 'group',
          data: {
            operator: 'AND',
            items: [cloneDeep(defaultRuleItem)],
          },
        }
      }

      this.queryData.items.push(item)
    },
    deleteItem(index) {
      this.queryData.items.splice(index, 1)
    },
  },
}
</script>

<style scoped>
.query-group {
  padding: 10px;
  border-radius: 5px;
}
.query-group-actions {
  column-gap: 10px;
}
</style>
