<template>
  <b-modal
    v-model="showModal"
    size="lg"
    :title="`${isEdit ? 'Edit' : 'Add'} Record`"
    @ok="onSubmit"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
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

      <template v-if="!loading && !loadingError">
        <div v-if="isEdit">
          <b-table-simple
            class="custom-table h-100"
          >
            <b-thead>
              <b-tr>
                <b-th width="33%">
                  Table
                </b-th>
                <b-th width="33%">
                  ID
                </b-th>
                <b-th width="33%">
                  Profile
                </b-th>
              </b-tr>
            </b-thead>
            <b-tbody>
              <b-tr>
                <b-td>
                  {{ tableName }}
                </b-td>
                <b-td>
                  {{ defaultRecord.ID }}
                </b-td>
                <b-td>
                  {{ defaultRecord.PROFILE_NAME }}
                </b-td>
              </b-tr>
            </b-tbody>
          </b-table-simple>
        </div>

        <template v-if="!isEdit">
          <b-row>
            <b-col :lg="environmentRequired ? 6 : 12">
              <b-form-group
                label="Table"
              >
                <v-select
                  ref="vSelect"
                  v-model="tableName"
                  transition=""
                  :clearable="false"
                  :options="tableOptions"
                  @open="scrollToSelected"
                />
              </b-form-group>
            </b-col>
            <b-col :lg="environmentRequired ? 6 : 12">
              <b-form-group
                v-if="environmentRequired"
                label="Environment"
              >
                <v-select
                  v-model="environment"
                  transition=""
                  :clearable="false"
                  :options="environmentOptions"
                />
              </b-form-group>
            </b-col>
          </b-row>

          <div class="mb-1">
            Procees: {{ profileName }}
          </div>
        </template>

        <b-table-simple
          v-if="tableName"
          ref="table"
          class="custom-table h-100 mb-0"
          sticky-header="500px"
        >
          <b-thead>
            <b-tr>
              <b-th width="40%">
                Column Name
              </b-th>
              <b-th width="60%">
                Value
              </b-th>
            </b-tr>
          </b-thead>
          <b-tbody>
            <b-tr
              v-for="field of fields"
              :key="field"
            >
              <b-td>{{ field }}</b-td>
              <b-td>
                <b-form-input
                  v-model="record[field]"
                  type="text"
                  :placeholder="field"
                />
              </b-td>
            </b-tr>
          </b-tbody>
        </b-table-simple>

        <b-alert
          class="my-1"
          variant="danger"
          :show="errorMessage !== null ? true : false"
        >
          <div class="alert-body">
            <p>
              {{ errorMessage }}
            </p>
          </div>
        </b-alert>

        <detailed-error-messages :messages="detailedErrorMessages" />
      </template>
    </b-card-text>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="submitting || !enableSubmit"
        @click="ok()"
      >
        Submit
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BButton, BModal, BSpinner, BCardText, BAlert, BFormInput, BTableSimple, BThead, BTr, BTh, BTd, BTbody, BFormGroup, BRow, BCol,
} from 'bootstrap-vue'
import axios from '@/rules-backend-axios'
import vSelect from 'vue-select'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import DetailedErrorMessages from './DetailedErrorMessages.vue'

export default {
  components: {
    BButton,
    BModal,
    BSpinner,
    BCardText,
    BAlert,
    BFormInput,
    BTableSimple,
    BThead,
    BTr,
    BTh,
    BTd,
    BTbody,
    DetailedErrorMessages,
    vSelect,
    BFormGroup,
    BRow,
    BCol,
  },
  props: {
    isEdit: {
      type: Boolean,
      required: true,
    },
    defaultRecord: {
      type: Object,
      required: false,
      default() {
        return null
      },
    },
    defaultTableName: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      record: {},
      tableName: null,
      environment: null,
      loading: false,
      loadingError: null,
      showModal: true,
      submitting: false,
      errorMessage: null,
      detailedErrorMessages: [],
    }
  },
  computed: {
    selectedDefintionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },
    tableOptions() {
      return this.$store.getters['lookup/tables']
    },
    fields() {
      const excludeFields = ['ID', 'PROFILE_NAME']
      let tableColumns = this.$store.getters['lookup/tableColumns'](this.tableName)
      tableColumns = tableColumns.map(tableColumn => tableColumn.name)
      tableColumns = tableColumns.filter(field => !excludeFields.includes(field))
      return tableColumns
    },
    profileName() {
      return this.$store.getters['dataView/selectedDefinition'].definition_id
    },
    lookupOptions() {
      return this.$store.getters['lookup/options']
    },
    environmentRequired() {
      return !this.isEdit && this.lookupOptions.useMultipleEnvWiseDbs
    },
    environmentOptions() {
      return this.lookupOptions.environmentOptions
    },
    enableSubmit() {
      if (this.loading || this.loadingError) {
        return false
      }

      if (this.tableName === null) {
        return false
      }

      if (this.environmentRequired && this.environment === null) {
        return false
      }

      return true
    },
  },
  watch: {
    fields: {
      handler() {
        if (this.initialized) {
          this.resetLocalRecord()
        }
      },
      deep: true,
    },
  },
  created() {
    this.initializeForm()
  },
  methods: {
    initializeForm() {
      this.loading = true
      this.$store.dispatch('lookup/initialize')
        .then(() => {
          this.tableName = this.defaultTableName
          this.resetLocalRecord(this.defaultRecord)

          this.$nextTick(() => {
            this.initialized = true
          })

          this.loadingError = null
          this.loading = false
        }).catch(error => {
          this.loadingError = error.message
          this.loading = false
        })
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs.vSelect.$refs.dropdownMenu
        const selectedIndex = this.tableOptions.indexOf(this.tableName)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.tableOptions.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
    resetLocalRecord(data) {
      const record = {}
      this.fields.forEach(field => {
        record[field] = data ? data[field] || null : null
      })
      this.record = record
    },
    onSubmit(event) {
      event.preventDefault()
      this.submitting = true

      let formData
      let operation
      if (this.isEdit) {
        formData = {
          table_name: this.tableName,
          updated_record: this.record,
          record_id: this.defaultRecord.ID,
          definition_version: this.selectedDefintionVersion,
        }
        operation = axios.post('/modify_db_record/', formData)
      } else {
        const record = {
          ...this.record,
        }
        if (this.environmentRequired) {
          record.ENVIRONMENT = this.environment
        }

        formData = {
          table_name: this.tableName,
          profile_name: this.profileName,
          record,
        }
        operation = axios.post('/add_record_to_db/', formData)
      }

      operation
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.submitting = false
          this.errorMessage = null
          this.detailedErrorMessages = []
          this.showModal = false
        }).catch(error => {
          this.errorMessage = error?.response?.data?.detail || 'Error updating record'
          this.detailedErrorMessages = error?.response?.data?.messages || []
          this.submitting = false
        })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
