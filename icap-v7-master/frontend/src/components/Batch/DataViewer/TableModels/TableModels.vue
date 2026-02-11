<!--
  Organization: AIDocbuilder Inc.
  File: TableModels.vue
  Version: 6.0

  Authors:
    - Vinay - Initial implementation
    - Ali - Code enhancement and component design

  Last Updated By: Ali
  Last Updated At: 2024-12-11

  Description:
    This component manages the configuration of table models with dynamic fields and validations.
    It supports both basic and advanced settings for table models and integrates with Vuex for state management.

  Main Features:
    - Dynamic rendering of fields based on model type and visibility settings.
    - Advanced field toggle functionality for enhanced user experience.
    - Validation integration using VeeValidate.
    - Customizable field visibility and permissions.

  Dependencies:
    - Bootstrap Vue for UI components.
    - VeeValidate for form validation.
    - Lodash for deep object manipulation.
    - Event bus for inter-component communication.

  Notes:
    - Ensure that Vuex store provides `tableSettings` and `batch` data for proper functionality.
-->

<template>
  <div
    ref="tableModelsWrapper"
    class="table-model-wrapper"
  >
    <b-col md="12">
      <validation-observer
        ref="tableModelForm"
        mode="eager"
      >
        <b-form
          @submit.prevent
        >
          <b-row>
            <template
              v-for="field of visibleNonAdvancedModelFields"
            >              <table-model-field
              :key="field.key"
              v-model="model[field.key]"
              :field="field"
              :validation-rules="validationRules[field.key]"
              :gl-action-options="glActionOptions"
              @selection-input="shapeSelectionInputHandler($event, field.key)"
              @item-deleted="shapeSelectionItemDeleteHandler($event, field.key)"
            />
            </template>
            <b-button
              v-if="model.type === 'autoPattern'"
              variant="outline-primary"
              class="atm-btn"
              @click="goToAutomatedTableModel"
            >
              Automated Table Model
            </b-button>
            <template v-if="visibleAdvancedModelFields.length > 0">
              <b-col cols="12">
                Advanced Settings
                <feather-icon
                  v-if="displayAdvancedFields"
                  icon="ChevronDownIcon"
                  class="cursor-pointer"
                  size="20"
                  @click.stop="toogleAdvancedFields"
                />
                <feather-icon
                  v-else
                  icon="ChevronUpIcon"
                  class="cursor-pointer"
                  size="20"
                  @click.stop="toogleAdvancedFields"
                />
              </b-col>
              <b-col
                v-show="displayAdvancedFields"
                cols="12"
              >
                <b-row>
                  <template
                    v-for="field of visibleAdvancedModelFields"
                  >
                    <table-model-field
                      v-if="shouldDisplayTableModelField(field)"
                      :key="field.key"
                      v-model="model[field.key]"
                      :field="field"
                      :validation-rules="validationRules[field.key]"
                      :gl-action-options="glActionOptions"
                    />
                  </template>
                </b-row>
                <b-row>
                  <template
                    v-for="field of visibleAdvancedModelFields"
                  >
                    <table-model-field
                      v-if="field.type === 'numeric'"
                      :key="field.key"
                      v-model="model[field.key]"
                      class="mt-2"
                      :field="field"
                      :validation-rules="validationRules[field.key]"
                      :gl-action-options="glActionOptions"
                    />
                  </template>
                </b-row>
                <b-row
                  v-if="batchProject === 'CustomsEntryUpdate'"
                  class="sumOf"
                >
                  Sum of Charge Amount
                </b-row>
                <b-row
                  v-if="batchProject === 'CustomsEntryUpdate'"
                  class="pb-2"
                >
                  <template
                    v-for="fieldGroup of visibleAdvancedModelFields"
                  >
                    <!-- For sumOfChargeAmount block -->
                    <template v-if="fieldGroup.type === 'sumOfChargeAmount'">
                      <b-col
                        v-for="field in fieldGroup.fields"
                        :key="field.key"
                        cols="6"
                        md="2"
                      >
                        <table-model-field
                          v-model="model.sumOfChargeAmount[field.key]"
                          :field="field"
                          :validation-rules="validationRules[field.key]"
                          :gl-action-options="glActionOptions"
                        />
                      </b-col>
                    </template>
                  </template>
                </b-row>
              </b-col>
            </template>
          </b-row>
        </b-form>
      </validation-observer>
    </b-col>
  </div>
</template>
<script>
import {
  VBTooltip, BCol, BRow, BForm, BButton,
} from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import { ValidationObserver } from 'vee-validate'

import bus from '@/bus'
import TableModelField from './TableModelField.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BCol,
    BRow,
    TableModelField,
    ValidationObserver,
    BForm,
    BButton,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      model: {},
      initialized: false,
      hiddenFields: ['InsertType', 'posCheck', 'chunkThreshold', 'shapeCheck'],
      displayAdvancedFields: false,
      customPermission: false,
    }
  },
  computed: {
    modelFields() {
      return this.$store.getters['applicationSettings/tableSettings'].model.fields
    },
    selectedTableName() {
      return this.$store.getters['dataView/selectedTableName']
    },
    visibleModelFields() {
      return this.modelFields.filter(item => {
        if (item.applicableForType && !item.applicableForType.includes(this.modelType)) {
          return false
        }

        if (this.hiddenFields.includes(item.key)) {
          return false
        }

        // Exclude 'sheetName' and 'sheetNameIdentifierCondition' if customPermission is false
        if (!this.customPermission && (item.key === 'sheetName' || item.key === 'sheetNameIdentifierCondition')) {
          return false
        }

        return true
      })
    },
    visibleAdvancedModelFields() {
      return this.visibleModelFields.filter(item => (item.advanced === 'true'))
    },
    visibleNonAdvancedModelFields() {
      return this.visibleModelFields.filter(item => (item.advanced !== 'true'))
    },
    batchProject() {
      return this.$store.getters['batch/batch']?.project
    },
    out() {
      return cloneDeep(this.model)
    },
    modelType() {
      return this.model.type
    },
    validationRules() {
      return {
        type: 'required',
        headerTrigger: 'required',
        close: 'required',
        open: ['tableOpenBlock', 'dynamicOpenBlock'].includes(this.modelType) ? 'required|selectTextFromImage' : '',
        tableStart: 'required',
        separator: 'required',
      }
    },
    glActionOptions() {
      let options = []
      if (this.modelType === 'tableLR') {
        options = ['notMerge', 'geoMain']
      } else if (this.modelType === 'tableOpenBlock') {
        options = ['multiOpenBlock', 'notRemoveHeader']
      }
      return options
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
    modelType() {
      if (this.initialized) {
        if (this.modelType === 'tableLR') {
          this.model.gLAction = 'notMerge'
        } else {
          this.model.gLAction = ''
        }
      }
    },
    model: {
      handler(val) {
        if (val.multishipmentType === 'Multisheet Multishipment' || val.multishipmentType === 'Eachsheet Single Shipment') {
          this.customPermission = true
        } else {
          this.customPermission = false
        }
      },
      deep: true,
    },
  },
  created() {
    this.setInternalState()

    this.$nextTick(() => {
      this.initialized = true
    })

    bus.$on('validateTableModel', this.validateTableModel)
  },
  destroyed() {
    bus.$off('validateTableModel', this.validateTableModel)
  },
  methods: {
    // Initializes or resets the internal model state based on `value` and `modelFields`
    setInternalState() {
      const item = {}
      // Iterates over each field in modelFields
      this.modelFields.forEach(modelField => {
        let value

        // Checks if the field exists in `value` and assigns it
        if (this.value[modelField.key] !== undefined) {
          value = this.value[modelField.key]
        } else if (modelField.defaultValue !== undefined) {
          if (modelField.key === 'forceLiner') {
            value = 'false'
          } else {
            value = modelField.defaultValue
          }
        } else {
          value = ''
        }

        // Handles advanced fields with null values, assigning an empty string
        if (value === null && modelField.advanced) {
          value = ''
        }

        // Sets the processed value in the `item` object
        item[modelField.key] = value
      })

      // Updates the component's model with the processed `item`
      this.model = item

      const sumField = this.visibleAdvancedModelFields.find(f => f.key === 'sumOfChargeAmount')
      if (sumField && sumField.fields) {
        if (!this.model.sumOfChargeAmount) {
          // Make sure the parent object exists
          this.$set(this.model, 'sumOfChargeAmount', {
            dty: false,
            vat: false,
            oth: false,
          })
        }
      }
    },

    // Handles input changes in shape selection and updates the `openPositions` field
    shapeSelectionInputHandler(data, field) {
      if (field !== 'open') {
        return // Only processes 'open' field changes
      }

      // If there are no positions or only one item, assigns the start position directly
      if (!this.model?.openPositions || data.totalItems === 1) {
        this.model.openPositions = data.selectionData.startPos.toString()
        return
      }

      // Splits the current `openPositions` into an array
      const openPositions = this.model.openPositions.split('|')

      // Updates the position at the specified index or the first position
      openPositions[data.index === -1 ? 0 : data.index] = data.selectionData.startPos

      // Joins the updated positions back into a pipe-separated string
      this.model.openPositions = openPositions.join('|')
    },

    // Handles deletion of a specific position in `openPositions`
    shapeSelectionItemDeleteHandler(index, field) {
      if (field !== 'open') {
        return // Only processes 'open' field deletions
      }

      const openPositions = this.model.openPositions.split('|')

      // If the index is invalid, exits the method
      if (index >= openPositions.length) {
        return
      }

      // Removes the position at the specified index
      openPositions.splice(index, 1)

      // Joins the updated positions back into a pipe-separated string
      this.model.openPositions = openPositions.join('|')
    },

    // Toggles the visibility of advanced fields in the UI
    toogleAdvancedFields() {
      this.displayAdvancedFields = !this.displayAdvancedFields
    },

    // Validates the table model form and executes a callback with the validation result
    validateTableModel(callback) {
      this.$refs.tableModelForm.validate().then(success => {
        callback(success)
      })
    },

    // Navigates to the automated table model route
    goToAutomatedTableModel() {
      this.$router.push({ name: 'automated-table-model' })
    },

    // Determines whether a specific table model field should be displayed
    shouldDisplayTableModelField(field) {
      return field.type !== 'numeric'
      && (field.key !== 'ignoreChargesTable'
      || (field.key === 'ignoreChargesTable' && this.batchProject === 'CustomsEntryUpdate'))
    },
  },
}
</script>

<style scoped>
.table-model-wrapper {
    height: 100%!important;
    overflow-y: scroll;
}
.atm-btn {
  height: 37px;
  margin-top: 28px;
}
.sumOf{
  padding-top: 2rem;
  padding-left: .5rem;
}
</style>
