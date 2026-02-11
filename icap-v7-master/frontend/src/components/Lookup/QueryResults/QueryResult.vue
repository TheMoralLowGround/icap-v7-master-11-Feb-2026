<template>
  <div class="h-100">
    <b-alert
      v-if="!result.exectued"
      class="my-50"
      variant="danger"
      show
    >
      <div class="alert-body">
        <p>
          Query did not exectued
        </p>
      </div>
    </b-alert>
    <template v-else>
      <b-alert
        v-if="result.error"
        class="my-50"
        variant="danger"
        show
      >
        <div class="alert-body">
          <p>
            {{ result.error }}
          </p>
        </div>
      </b-alert>
      <template v-else>
        <div
          v-if="items.length === 0"
          class="text-center"
        >
          No records found
        </div>
        <b-table
          v-else
          :items="items"
          :fields="tableFields"
          :filter="search"
          responsive
          hover
          striped
          sticky-header="100%"
          class="query-result-table"
        >
          <template #cell(actions)="data">
            <div
              v-if="isSameProfile(data.item)"
              class="text-nowrap"
            >
              <feather-icon
                v-b-tooltip.hover="{boundary:'window'}"
                icon="EditIcon"
                size="20"
                class="cursor-pointer ml-50"
                title="Edit Record"
                @click.stop="editRecord = data.item"
              />

              <feather-icon
                v-b-tooltip.hover="{boundary:'window'}"
                icon="Trash2Icon"
                size="20"
                class="cursor-pointer mx-50"
                title="Delete Record"
                @click.stop="deleteRecord = data.item"
              />
            </div>
          </template>
        </b-table>
      </template>
    </template>

    <record-form
      v-if="editRecord"
      :is-edit="true"
      :default-record="editRecord"
      :default-table-name="tableName"
      @modal-closed="editRecord = null"
    />

    <delete-record
      v-if="deleteRecord"
      :record="deleteRecord"
      :table-name="tableName"
      @modal-closed="deleteRecord = null"
    />

  </div>
</template>

<script>
import {
  BTable, BAlert, VBTooltip,
} from 'bootstrap-vue'

import RecordForm from '../RecordForm.vue'
import DeleteRecord from '../DeleteRecord.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BTable,
    BAlert,
    RecordForm,
    DeleteRecord,
  },
  props: {
    result: {
      type: Object,
      required: true,
    },
    search: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      editRecord: null,
      deleteRecord: null,
    }
  },
  computed: {
    items() {
      return this.result.result || []
    },
    currentDefinitionProfile() {
      return this.$store.getters['dataView/selectedDefinition'].definition_id
    },
    tableName() {
      return this.result.source_table
    },
    tableFields() {
      const tableColumns = this.$store.getters['lookup/tableColumns'](this.tableName)
      const fields = tableColumns.map(tableColumn => ({
        key: tableColumn.name,
        label: tableColumn.name,
        sortable: true,
      }))

      fields.push({
        key: 'actions',
      })

      return fields
    },
  },
  methods: {
    isSameProfile(record) {
      return record.PROFILE_NAME === this.currentDefinitionProfile
    },
  },
}
</script>

<style scoped lang="scss">
.query-result-table {
    white-space: nowrap;

    ::v-deep th, ::v-deep td {
        padding: 0.5rem;
    }
}
</style>
