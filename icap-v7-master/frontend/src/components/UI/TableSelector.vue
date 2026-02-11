<template>
  <div
    v-if="tableOptions.length"
    class="h-100"
  >
    <v-select
      v-model="selectedTable"
      :clearable="false"
      :options="tableOptions"
      :reduce="option => option.value"
      class="table-selector h-100"
      :class="{'verification-table-selector': mainMode === 'verification'}"
    />
  </div>
</template>

<script>
import vSelect from 'vue-select'
import { VBTooltip } from 'bootstrap-vue'
import bus from '@/bus'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
  },
  computed: {
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    // Definition tables
    definitionTables() {
      return this.$store.getters['dataView/selectedDefinition']?.table || []
    },
    selectedTableName() {
      return this.$store.getters['dataView/selectedTableName']
    },
    // Document tables
    documentTables() {
      return this.$store.getters['batch/selectedDocument']?.tables || []
    },
    // Merged list: definition tables + document tables not in definition
    tableOptions() {
      const options = []
      const addedNames = new Set()

      // Add definition tables first
      this.definitionTables.forEach(t => {
        options.push({ label: t.table_name, value: t.table_name })
        addedNames.add(t.table_name)
      })

      // Add document tables that aren't in definition
      this.documentTables.forEach(t => {
        if (!addedNames.has(t.table_name)) {
          options.push({ label: t.table_name, value: t.table_name })
        }
      })

      return options
    },
    selectedTable: {
      get() {
        const { selectedTableName } = this
        if (!selectedTableName) return null

        // Check if it exists in our options
        const exists = this.tableOptions.some(opt => opt.value === selectedTableName)
        if (exists) {
          return { label: selectedTableName, value: selectedTableName }
        }
        return null
      },
      set(value) {
        if (!value) return
        this.handleTableSelection(value)
      },
    },
  },
  methods: {
    async handleTableSelection(tableName) {
      const prevTableName = this.selectedTableName

      // Check if table exists in definition
      const existsInDefinition = this.definitionTables.some(t => t.table_name === tableName)

      // If not in definition, create it
      if (!existsInDefinition) {
        const tableId = this.definitionTables.length
        await this.$store.dispatch('dataView/addTable', {
          tableName,
          tableId,
          isAuto: 'auto',
        })
      }

      // Set the selected table by name
      this.$store.commit('dataView/SET_SELECTED_TABLE_NAME', tableName)
      this.$store.commit('dataView/SET_SELECTED_TABLE_ID', tableName)

      // Emit table change event
      bus.$emit('dataView/onTableChange', {
        curentTableId: tableName,
        prevTableId: prevTableName,
      })
    },
  },
}
</script>

<style lang="scss">
.table-selector {
  .vs__dropdown-toggle {
    height: 100%;
    border-top-left-radius: 0rem !important;
    border-bottom-left-radius: 0rem !important;
  }
}

.verification-table-selector {
  .vs__dropdown-toggle {
    border-top-left-radius: 0.357rem !important;
    border-bottom-left-radius: 0.357rem !important;
  }
}
</style>
