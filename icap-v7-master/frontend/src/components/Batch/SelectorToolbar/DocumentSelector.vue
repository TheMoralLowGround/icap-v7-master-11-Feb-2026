<template>
  <div>
    <!-- Vue-select dropdown component -->
    <v-select
      ref="vSelect"
      v-model="documentId"
      :clearable="false"
      :options="options"
      :loading="loadingDocumentData"
      @open="scrollToSelected"
    >
      <!-- Custom spinner template -->
      <template #spinner="{ loading }">
        <b-spinner
          v-if="loading"
          variant="primary"
          small
        />
      </template>
    </v-select>
  </div>
</template>

<script>
import vSelect from 'vue-select'
import { BSpinner } from 'bootstrap-vue'

export default {
  components: {
    vSelect,
    BSpinner,
  },
  computed: {
    // Fetches the current mode from the store (e.g., 'verification').
    mainMode() {
      return this.$store.getters['dataView/mainMode']
    },
    currentRouteName() {
      return this.$route.name // Returns the current route name from Vue Router
    },
    selectedDocument() {
      return this.$store.getters['batch/selectedDocument'] // Returns the current route name from Vue Router
    },
    // Two-way binding for the selected document ID from the store.
    documentId: {
      get() {
        return this.$store.getters['batch/selectedDocumentId']
      },
      set(value) {
        // Updates the selected document ID in the store.
        this.$store.commit('batch/SET_SELECTED_DOCUMENT_ID', value)
      },
    },
    // Generates a list of document keys from the batch documents stored in Vuex.
    options() {
      const selectedBatchId = this.$store.getters['batch/batch']?.id
      const docs = this.$store.getters['batch/documents']

      if (!selectedBatchId) return []

      return Object.values(docs) // all transactions
        .flatMap(transaction => Object.entries(transaction) // [batchId, documents] pairs
          .filter(([batchId]) => batchId === selectedBatchId)
          .flatMap(([, documents]) => Object.keys(documents)))
    },

    // Indicates whether the document data is currently loading.
    loadingDocumentData() {
      return this.$store.getters['batch/loadingDocumentData']
    },
    // Retrieves the selected node data from the store.
    selectedNode() {
      return this.$store.getters['batch/selectedNode']
    },
    selectedLayoutId() {
      return this.$store.getters['batch/documentData']?.pages[0]?.layout_id
    },
    // Fetches the verification details for the batch from the store.
    verificationDetails() {
      return this.$store.getters['batch/verificationDetails']
    },
    tables() {
      return this.$store.getters['batch/selectedDocument']?.tables || []
    },
    table() {
      return this.$store.getters['dataView/table'] || []
    },
    selectedTableName() {
      const table = this.table || []
      const tables = this.tables || []

      // Prioritize document tables over definition tables
      if (tables.length > 0) {
        return tables[0].table_name
      }
      if (table.length > 0) {
        return table[0].table_name
      }
      return 'Main_0'
    },
  },
  watch: {
    selectedLayoutId: {
      async handler() {
        await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
      },
      deep: true,
    },
    'selectedDocument.vendor': {
      async  handler() {
        // if (newVendor) {
        //   await this.$store.dispatch('dataView/fetchDefinition', this.currentRouteName)
        // }
        await this.$store.dispatch('batch/fetchProfileKeys')
      },
      immediate: false,
    },
    // Watches for changes in the selected document ID.
    documentId: {
      async handler(oldVal, newVal) {
        if (this.mainMode === 'verification' && oldVal !== newVal) {
          const batchId = `${this.documentId.split('.')[0]}.${this.documentId.split('.')[1]}`
          const batch = this.verificationDetails.find(e => e.id === batchId)
          // Ensure table data is loaded
          await this.$store.dispatch('batch/loadDocumentData')
          // Prioritize document tables over definition tables for default selection
          const defaultTableName = this.getDefaultTableName()
          if (defaultTableName) {
            this.$store.commit('dataView/SET_SELECTED_TABLE_BY_ID', 0)
            this.$store.commit('dataView/SET_SELECTED_TABLE_NAME', defaultTableName)
          }
          this.$store.dispatch('dataView/setDJsonTableList', batch)
          this.$store.commit('batch/SET_BATCH', { id: batchId, subPath: batch?.sub_path || '' })
          this.$store.dispatch('batch/setEditableNode', null)
        } else {
          // Ensure table data is loaded even outside verification mode
          await this.$store.dispatch('batch/loadDocumentData')
          // Prioritize document tables over definition tables for default selection
          const defaultTableName = this.getDefaultTableName()
          if (defaultTableName) {
            this.$store.commit('dataView/SET_SELECTED_TABLE_BY_ID', 0)
            this.$store.commit('dataView/SET_SELECTED_TABLE_NAME', defaultTableName)
          }
        }
      },
      immediate: true,
    },

    // Watches for changes in the selected node and ensures the document ID matches the selected node's docId.
    selectedNode() {
      if (this.selectedNode?.docId !== this.documentId && this.selectedNode?.highlight) {
        this.documentId = this.selectedNode.docId
      }
    },

  },
  mounted() {
    if (this.mainMode === 'verification' && this.documentId) {
      // Prioritize document tables over definition tables for default selection
      const defaultTableName = this.getDefaultTableName()

      if (defaultTableName) {
        this.$store.commit('dataView/SET_SELECTED_TABLE_BY_ID', 0)
        this.$store.commit('dataView/SET_SELECTED_TABLE_NAME', defaultTableName)
      }

      const batchId = `${this.documentId.split('.')[0]}.${this.documentId.split('.')[1]}`
      const batch = this.verificationDetails.find(e => e.id === batchId)

      this.$store.dispatch('dataView/setDJsonTableList', batch)
      this.$store.commit('batch/SET_BATCH', { id: batchId, subPath: batch?.sub_path || '' })
      this.$store.dispatch('batch/setEditableNode', null)
    }
  },
  methods: {
    // Get default table name - prioritize document tables over definition tables
    getDefaultTableName() {
      if (this.tables.length > 0) {
        return this.tables[0].table_name
      }
      if (this.table.length > 0) {
        return this.table[0].table_name
      }
      return null
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs.vSelect.$refs.dropdownMenu
        const selectedIndex = this.options?.indexOf(this.documentId)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.options.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
