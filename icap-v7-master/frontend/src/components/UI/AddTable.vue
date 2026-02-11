<template>
  <b-form>
    <b-input-group>
      <b-input-group-prepend>
        <b-button
          :variant="buttonVariant"
          :disabled="mode === 'test'"
          style="opacity: 1"
          @click="onAdd"
        >
          <feather-icon
            v-if="mode !== 'test'"
            icon="PlusIcon"
            size="12"
          />
          <span>{{ label }}</span>
        </b-button>
      </b-input-group-prepend>
      <b-form-input
        v-if="onCreate || onUpdate"
        v-model="tableName"
        type="text"
        placeholder="table name"
        :autofocus="true"
        class="mr-7px"
        @keydown.enter.prevent="onPressEnter"
      />
      <feather-icon
        v-if="onCreate"
        v-b-tooltip.hover
        title="Create Table"
        icon="SaveIcon"
        size="16"
        class="my-auto mr-5px cursor-pointer"
        @click="onCreateTable"
      />
      <div
        v-if="!onCreate && !onUpdate"
        class="table-selector-wrapper mr-7px"
      >
        <TableSelector />
      </div>
      <feather-icon
        v-if="!onCreate && !onUpdate && mode !== 'test'"
        v-b-tooltip.hover
        :title="isEditDisabled ? '' : 'Rename Table'"
        icon="EditIcon"
        size="16"
        class="my-auto mr-5px"
        :class="editIconClasses"
        :disabled="isEditDisabled"
        @click="!isEditDisabled && handleEditClick()"
      />
      <feather-icon
        v-if="!onCreate && !onUpdate && table.length > 0 && mode !== 'test'"
        v-b-tooltip.hover
        title="Delete Table"
        icon="TrashIcon"
        size="16"
        class="my-auto cursor-pointer"
        @click="onDelete"
      />

      <feather-icon
        v-if="onUpdate && tableName !== table[selectedTableId].table_name"
        v-b-tooltip.hover
        title="Save Table"
        icon="SaveIcon"
        size="16"
        class="my-auto mr-5px cursor-pointer"
        @click="onRename"
      />
      <feather-icon
        v-if="onCreate || onUpdate"
        v-b-tooltip.hover
        title="Close"
        icon="DeleteIcon"
        size="16"
        class="my-auto ml-5px cursor-pointer"
        @click="onClose"
      />
    </b-input-group>

  </b-form>
</template>

<script>
import {
  BInputGroup, BInputGroupPrepend, BButton, BFormInput, BForm, VBTooltip,
} from 'bootstrap-vue'
import TableSelector from '@/components/UI/TableSelector.vue'
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import axios from 'axios'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BInputGroup,
    BInputGroupPrepend,
    BButton,
    BFormInput,
    BForm,
    TableSelector,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    buttonVariant: {
      type: String,
      required: false,
      default() {
        return 'primary'
      },
    },
  },
  data() {
    return {
      tableName: '',
      onCreate: false,
      onUpdate: false,
    }
  },
  computed: {
    table() {
      return this.$store.getters['dataView/table']
    },
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },
    selectedBatch() {
      return this.$store.getters['batch/selectedBatch']
    },
    selectedTableId() {
      return this.$store.getters['dataView/selectedTableId']
    },
    selectedTableName() {
      return this.$store.getters['dataView/selectedTableName']
    },
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition']
    },
    mode() {
      return this.$store.getters['dataView/mode']
    },
    isEditDisabled() {
      // return this.mode === 'view' || this.loading
      return true
    },
    editIconClasses() {
      return {
        'cursor-pointer': !this.isEditDisabled,
        'text-muted': this.isEditDisabled,
        'text-primary': !this.isEditDisabled,
      }
    },
  },
  created() {
    bus.$on('dataView/deleteTable', this.onDelete)
  },
  destroyed() {
    bus.$off('dataView/deleteTable', this.onDelete)
    this.onCreate = false
    this.onUpdate = false
  },
  methods: {
    handleEditClick() {
      if (!this.isEditDisabled) {
        this.onEdit()
      }
    },
    onAdd() {
      this.tableName = `Main_${this.tableNamePostfix()}`
      this.onUpdate = false
      this.onCreate = true
    },
    onCreateTable() {
      if (!this.isUnique()) {
        return
      }
      const data = {
        tableId: this.table.length,
        tableName: this.tableName,
        selectedTableId: this.selectedTableId,
      }

      this.onCreate = false

      this.$emit('add', data)
    },
    onEdit() {
      this.onCreate = false
      this.onUpdate = true
      this.tableName = this.table[this.selectedTableId].table_name
    },
    onRename() {
      if (!this.isUnique()) return

      this.$store.dispatch('dataView/renameTable', {
        tableName: this.tableName,
        tableId: this.selectedTableId,
      })

      bus.$emit('dataView/saveTableData')

      this.onUpdate = false
    },
    async onDelete(data = {}) {
      const { tableId } = data
      const tableIdToDelete = data.tableId || this.selectedTableId
      const tableNameToDelete = this.table[tableIdToDelete]?.table_name

      if (!tableNameToDelete) return

      // 1. Remove from Vuex store
      this.$store.dispatch('dataView/deleteTable', {
        tableId: tableId || this.selectedTableId,
      })
      this.$store.commit('dataView/SET_SELECTED_TABLE_BY_ID', 0)
      bus.$emit('dataView/saveTableData')

      // 2. Remove from selectedBatch.data_json
      if (this.selectedBatch) {
        await this.deleteTableFromDocument(tableNameToDelete)
      }
    },
    onClose() {
      this.onUpdate = false
      this.onCreate = false
    },
    onPressEnter() {
      if (this.onCreate) {
        this.onCreateTable()
      } else if (this.onUpdate) {
        if (this.tableName !== this.table[this.selectedTableId].table_name) {
          this.onRename()
        }
      }
    },
    tableNamePostfix() {
      let tableNamePostfix = -1

      this.table.forEach(item => {
        const splitedTableName = item.table_name.split('_')

        if (splitedTableName[0] === 'Main') {
          if (splitedTableName.length === 2) {
            const currentTablePostfix = parseInt(splitedTableName[1], 10)

            if (!Number.isInteger(currentTablePostfix)) return

            if (currentTablePostfix > tableNamePostfix) {
              tableNamePostfix = currentTablePostfix
            }
          }
        }
      })

      return tableNamePostfix + 1
    },
    isUnique() {
      const unique = this.table.every(item => this.tableName !== item.table_name)

      if (!unique) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Duplicate Table Name',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }

      return unique
    },
    isMatchingTable(child, tableNameToDelete) {
      return (
        child.type === 'table'
    && [child.table_name, child.name, child.id].includes(tableNameToDelete)
      )
    },
    async deleteTableFromDocument(tableNameToDelete) {
      try {
        const batchData = this.selectedBatch?.data_json || {}
        const documentId = this.selectedDocumentId
        const transactionId = this.$route.params.id

        const document = batchData.nodes?.find(doc => doc.id === documentId)
        if (!document || !Array.isArray(document.children)) return

        // Check if table exists
        const tableExistsInDocument = document.children.some(child => this.isMatchingTable(child, tableNameToDelete))

        if (!tableExistsInDocument) return

        // Remove matching table
        document.children = document.children.filter(
          child => !this.isMatchingTable(child, tableNameToDelete),
        )

        const payload = {
          batch_id: this.selectedBatch.id,
          data_json: batchData,
        }

        const res = await axios.put('/pipeline/update_batch/', payload)
        if (res) {
          this.$store.dispatch('batch/removeTableFromTransaction', {
            batchId: this.selectedBatch.id,
            documentId,
            tableName: tableNameToDelete,
          })
          await this.$store.dispatch('batch/fetchBatch', {
            selectedTransaction: transactionId,
            selectFirstDocument: true,
          })

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Success',
              text: `Table "${tableNameToDelete}" deleted from document successfully`,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
        }
      } catch (error) {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Error',
            text: 'Failed to delete table from batch',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
    }
    ,

  },
}
</script>

<style scoped>
.btn {
  padding: 0.75rem !important;
  font-size: 12px;
}

.input-group:focus-within {
  box-shadow: none;
}

.form-control {
  height: 35px;
}

.table-selector-wrapper {
  width: 150px;
  height: 35px;
  font-size: 12px;
}

.mr-5px {
  margin-right: 5px !important;
}

.mr-7px {
  margin-right: 7px !important;
}

.ml-5px {
  margin-left: 5px !important;
}

.font-12px {
  font-size: 12px;
}
</style>
