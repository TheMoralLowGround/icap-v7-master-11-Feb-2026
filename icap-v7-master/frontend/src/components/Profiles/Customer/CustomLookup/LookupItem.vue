<template>
  <div class="lookup-item border rounded p-1 mb-1">
    <div class="d-flex justify-content-between align-items-center mb-1">
      <h6 class="mb-0">
        Lookup Query #{{ queryIndex + 1 }}
      </h6>
      <feather-icon
        v-b-tooltip.hover
        title="Delete Lookup"
        icon="Trash2Icon"
        class="cursor-pointer"
        size="20"
        @click="$emit('delete')"
      />
    </div>

    <div class="query-rules-section mt-1">
      <div class="d-flex align-items-center justify-content-between mb-1">
        <div
          class="d-flex align-items-center"
          style="column-gap: 10px;"
        >
          <b-button
            variant="outline-primary"
            class="btn-icon"
            @click="addQueryRule"
          >
            <feather-icon
              icon="PlusIcon"
              class="mr-25"
            />
            <span>Add Rule</span>
          </b-button>

          <div style="width: 120px;">
            <v-select
              v-model="lookupData.queryOperationType"
              :options="['AND', 'OR']"
              :clearable="false"
              placeholder="Operation"
            />
          </div>
        </div>
      </div>

      <div
        v-for="(rule, index) in lookupData.queryData"
        :key="index"
      >
        <div
          class="d-flex align-items-start my-50"
          style="column-gap: 10px;"
        >
          <validation-provider
            #default="{ errors }"
            name="Column"
            :vid="`column-${queryIndex}-${index}`"
            rules="required"
            style="flex-basis:340px;"
          >
            <b-form-group
              :state="errors.length > 0 ? false : null"
              class="mb-0"
            >
              <v-select
                :ref="`columnOptions-${index}`"
                v-model="rule.column"
                :options="columnOptions"
                :clearable="false"
                placeholder="Select Column"
                @input="onColumnChange(index)"
                @open="scrollToSelected(columnOptions, rule.column, `columnOptions-${index}`)"
              />
              <small class="text-danger">{{ errors[0] }}</small>
            </b-form-group>
          </validation-provider>
          <validation-provider
            #default="{ errors }"
            name="Operator"
            :vid="`operator-${queryIndex}-${index}`"
            rules="required"
            style="flex-basis:200px;"
          >
            <b-form-group
              :state="errors.length > 0 ? false : null"
              class="mb-0"
            >
              <v-select
                v-model="rule.operator"
                :options="getOperatorOptionsForColumn(rule.column)"
                :reduce="option => option.value"
                :clearable="false"
                placeholder="Operator"
              />
              <small class="text-danger">{{ errors[0] }}</small>
            </b-form-group>
          </validation-provider>
          <div
            class="d-flex"
            style="flex-basis:500px;"
          >
            <div>
              <v-select
                v-model="rule.valueType"
                style="width: 160px;"
                :options="valueTypeOptions"
                label="label"
                :reduce="option => option.value"
                :clearable="false"
                @input="onValueTypeChange(index)"
              />
            </div>

            <div class="flex-grow-1 px-1">
              <validation-provider
                v-if="rule.valueType === 'input'"
                #default="{ errors }"
                name="Value"
                :vid="`value-input-${queryIndex}-${index}`"
                mode="eager"
                rules="required"
              >
                <b-form-group
                  class="mb-0"
                  :state="errors.length > 0 ? false : null"
                >
                  <b-form-input
                    v-model="rule.keyValue"
                    placeholder="Enter value"
                    class="ml-1 w-100"
                    :state="errors.length > 0 ? false : null"
                  />
                  <small class="text-danger ml-2">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>

              <validation-provider
                v-if="rule.valueType === 'key'"
                #default="{ errors }"
                name="Value"
                :vid="`value-key-${queryIndex}-${index}`"
                mode="eager"
                rules="required"
              >
                <b-form-group
                  class="mb-0"
                  :state="errors.length > 0 ? false : null"
                >
                  <v-select
                    :ref="`keyOptions-${index}`"
                    v-model="rule.keyValue"
                    :options="combinedKeyAndSubkeyOptions"
                    :clearable="false"
                    placeholder="Select Key"
                    class="ml-1 w-100"
                    :state="errors.length > 0 ? false : null"
                    @open="scrollToSelected(combinedKeyAndSubkeyOptions, rule.keyValue, `keyOptions-${index}`)"
                  />
                  <small class="text-danger ml-2">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </div>
          </div>
          <!-- <div style="width: 100px;">
            <v-select
              v-model="rule.operationType"
              :options="['AND', 'OR']"
              :clearable="false"
              placeholder=""
            />
          </div> -->

          <div>
            <feather-icon
              v-b-tooltip.hover
              title="Delete Rule"
              icon="Trash2Icon"
              class="cursor-pointer mx-auto"
              size="20"
              @click.stop="deleteQueryRule(index)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  BFormInput, BButton, VBTooltip, BFormGroup,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { ValidationProvider } from 'vee-validate'
import { isEqual, cloneDeep } from 'lodash'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

const defaultQueryRule = {
  column: null,
  operator: null,
  valueType: 'key',
  keyValue: null,
  // operationType: 'OR',
}

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
    BFormInput,
    BButton,
    ValidationProvider,
    BFormGroup,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    queryIndex: {
      type: [String, Number],
      default: () => 1,
    },
    queryResultOptions: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      lookupData: {
        queryData: [],
        queryOperationType: 'OR',
      },
      valueTypeOptions: [
        { label: 'Key', value: 'key' },
        { label: 'Input', value: 'input' },
      ],
    }
  },
  computed: {
    out() {
      const output = cloneDeep(this.lookupData)
      // Don't strip queryOperationType from output, keep it at query level
      // Don't add table property here, it's already at the parent level in LookupManager
      return output
    },
    tableOptions() {
      const allTables = this.$store.getters['lookup/tables'] || []
      return allTables.filter(t => t.toLowerCase().includes('custom_master'))
    },
    tableColumns() {
      const table = this.tableOptions[0]
      if (!table) return []
      return this.$store.getters['lookup/tableColumns'](table) || []
    },
    columnOptions() {
      return this.tableColumns.map(col => col.name)
    },
    compoundKeys() {
      return this.$store.getters['definitionSettings/compoundKeys'] || []
    },
    qualifierKeys() {
      return this.$store.getters['definitionSettings/keyQualifiers'] || []
    },
    optionsKeys() {
      return this.$store.getters['definitionSettings/keyItems'] || []
    },
    combinedKeyAndSubkeyOptions() {
      const options = new Set()

      if (Array.isArray(this.compoundKeys)) {
        this.compoundKeys.forEach(ck => {
          if (ck?.name) {
            options.add(ck.name)
            if (ck.keyItems && Array.isArray(ck.keyItems)) {
              ck.keyItems.forEach(item => {
                options.add(item.keyLabel || item)
              })
            }
          }
        })
      }

      if (Array.isArray(this.qualifierKeys)) {
        this.qualifierKeys.forEach(qk => {
          if (qk?.name) {
            options.add(qk.name)
            if (qk.options && Array.isArray(qk.options)) {
              qk.options.forEach(option => {
                options.add(option.value)
              })
            }
          }
        })
      }

      if (Array.isArray(this.optionsKeys)) {
        this.optionsKeys.forEach(ok => {
          if (ok?.keyLabel) {
            options.add(ok.keyLabel)
          }
        })
      }

      if (Array.isArray(this.queryResultOptions)) {
        this.queryResultOptions.forEach(option => {
          if (option?.value) {
            options.add(option.value)
          }
        })
      }

      return [...options]
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
    getOperatorOptionsForColumn(columnName) {
      // Base operators (always available)
      const baseOperators = [
        { label: '=', value: '=' },
        { label: 'Contain', value: 'contain' },
        { label: 'Starts With', value: 'starts_with' },
      ]

      if (!columnName) {
        return baseOperators
      }

      // Find column metadata
      const columnMetadata = this.tableColumns.find(col => col.name === columnName)

      // If column has SEMANTIC_MATCH true, add semantic match operator
      if (columnMetadata && columnMetadata.semantic_match === true) {
        return [
          ...baseOperators,
          { label: 'Semantic Match', value: 'semantic_match' },
        ]
      }

      return baseOperators
    },
    setInternalState() {
      const incomingData = cloneDeep(this.value)
      this.lookupData = {
        queryData: incomingData.queryData || [],
        queryOperationType: incomingData.queryOperationType || 'AND',
      }
    },
    onValueTypeChange(index) {
      this.lookupData.queryData[index].keyValue = null
    },
    onColumnChange(index) {
      this.lookupData.queryData[index].keyValue = null
    },
    addQueryRule() {
      this.lookupData.queryData.push(cloneDeep(defaultQueryRule))
    },
    deleteQueryRule(index) {
      this.lookupData.queryData.splice(index, 1)
    },
    scrollToSelected(options, selectedValue, refName) {
      this.$nextTick(() => {
        const selectComponent = this.$refs[refName]
        if (!selectComponent || !selectComponent[0]) return

        const dropdownMenu = selectComponent[0].$refs?.dropdownMenu
        if (!dropdownMenu) return

        const selectedIndex = options.indexOf(selectedValue)
        if (selectedIndex >= 0) {
          const itemHeight = dropdownMenu.scrollHeight / options.length
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenu.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style scoped>
.lookup-item {
  border-color: #dee2e6;
}

.query-rules-section {
  border-radius: 5px;
  padding: 10px;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
