<!--
 Organization: AIDocbuilder Inc.
 File: AdditionalKeys.vue
 Version: 6.0

 Authors:
   - Ali - Initial implementation

 Last Updated By: Ali
 Last Updated At: 2024-12-20

 Description:
   This component manages a collection of `AdditionalKeyItem` components, allowing users to add or remove key items
   within a query group. Each `AdditionalKeyItem` represents a single key with selectable target columns and keys
   from predefined options. The component allows dynamic management of key items, and communicates with the parent
   through Vue's v-model binding and event handling.

 Features:
   - Dynamically adds and removes key items in a query group.
   - Customizes border color based on the depth of the query group.
   - Tooltips on icons for enhanced user interaction.
   - Integrates with child components for managing key selections.

 Dependencies:
   - `AdditionalKeyItem`: A child component that manages individual key item selection.
   - `BootstrapVue` for tooltips.
   - `Lodash` for deep cloning and comparison of data.

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
      <h4>
        Additional Keys
      </h4>
      <div>
        <feather-icon
          v-b-tooltip.hover
          title="Add Key"
          icon="PlusIcon"
          class="cursor-pointer mx-auto"
          size="20"
          @click="addItem()"
        />
      </div>
    </div>

    <div
      v-for="(item, itemIndex) of queryData.items"
      :key="itemIndex"
    >
      <additional-key-item
        v-model="queryData.items[itemIndex]"
        :table-columns="tableColumns"
        :query-result-options="queryResultOptions"
        @delete="deleteItem(itemIndex)"
      />
    </div>
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import AdditionalKeyItem from './AdditionalKeyItem.vue'

const defaultKeyItem = {
  target_column: null,
  target_key: null,
}

export default {
  name: 'AdditionalKeys',
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    AdditionalKeyItem,
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
    addItem() {
      let item = null
      item = cloneDeep(defaultKeyItem)
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
