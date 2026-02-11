<!--
 Organization: AIDocbuilder Inc.
 File: TableModelField.vue
 Version: 1.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code implementation and component design

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component renders a flexible form field model within a table.
   The field adapts dynamically based on the `field` type, allowing support for various input types
   such as text, select, numeric, checkbox, custom dropdowns, and more.

 Main Features:
   - Dynamically generates form inputs based on field configuration.
   - Supports validation using `vee-validate` for text and select inputs.
   - Renders custom components for specialized input types like sliders, pipe-separated inputs, cell range selectors, and capture text fields.
   - Integrates options filtering for select fields based on batch file type and multi-shipment settings.
   - Emits input changes and custom events for real-time updates.

 Dependencies:
   - `bootstrap-vue` for layout and form structure.
   - `vue-select` for dropdowns.
   - `vee-validate` for validation.
   - Custom components: `PipeSeparatedInput`, `FormInput`, `CaptureTextInput`, `CellRangeSelector`, `AutoPatternInput`, `NumericSlider`.

 Notes:
   - `setInternalState` ensures synchronization between `internalValue` and `value` props.
   - Scoped styles maintain layout integrity for checkboxes and dropdowns.
   - Additional filtering logic supports specific use cases like batch type and multi-shipment validation.
-->

<template>
  <b-col
    :lg="getColumnSize()"
  >
    <validation-provider
      v-if="field.type === 'text'"
      #default="{ errors }"
      :name="field.label ? field.label : field.key"
      :rules="validationRules"
      :vid="field.key"
    >
      <b-form-group
        :label="field.label ? field.label: field.key"
      >
        <form-input
          v-model="internalValue"
          type="text"
          :placeholder="field.key"
          :state="errors.length > 0 ? false:null"
        />
        <small class="text-danger">{{ errors[0] }}</small>
      </b-form-group>
    </validation-provider>

    <validation-provider
      v-if="field.type === 'select'"
      #default="{ errors }"
      :name="field.label ? field.label: field.key"
      :rules="validationRules"
      :vid="field.key"
    >

      <b-form-group
        :ref="field.key"
        :label="field.label ? field.label: field.key"
        :state="errors.length > 0 ? false:null"
      >
        <v-select
          v-model="internalValue"
          :label="options[field.optionsId].lableKey"
          :options="selectOptions(field.optionsId, field.filterByFileType)"
          :reduce="option => option[options[field.optionsId].valueKey]"
          @open="onDropdownOpen(field.key)"
        />
        <small class="text-danger">{{ errors[0] }}</small>
      </b-form-group>
    </validation-provider>

    <b-row v-if="field.type === 'numeric'">
      <div class="w-100 mr-1">
        {{ field.label }}
        <numeric-slider
          v-model="internalValue"
          :field="field"
        />
      </div>
    </b-row>

    <b-row v-if="field.type === 'checkbox'">
      <b-form-checkbox
        class="checkbox"
        :checked="internalValue"
        @change="(value) => internalValue = value.toString()"
      >
        {{ field.label }}
      </b-form-checkbox>
    </b-row>

    <validation-provider
      v-if="field.type === 'custom-select-gLAction'"
      #default="{ errors }"
      :name="field.label ? field.label: field.key"
      :rules="validationRules"
      :vid="field.key"
    >
      <b-form-group
        :ref="field.key"
        :label="field.label ? field.label: field.key"
        :state="errors.length > 0 ? false:null"
      >
        <v-select
          v-model="internalValue"
          :options="glActionOptions"
          @open="onDropdownOpen(field.key)"
        />
        <small class="text-danger">{{ errors[0] }}</small>
      </b-form-group>
    </validation-provider>

    <pipe-separated-input
      v-if="field.type === 'pipeSeparatedInput'"
      v-model="internalValue"
      :label="field.label ? field.label: field.key"
      selection-value-attr="text"
      listenable-input
      :validation-rules="validationRules"
      :validation-key="field.key"
    />

    <pipe-separated-input
      v-if="field.type === 'pipeSeparatedInputShape'"
      v-model="internalValue"
      :label="field.label ? field.label: field.key"
      selection-value-attr="textToShape"
      listenable-input
      :validation-rules="validationRules"
      :validation-key="field.key"
      @selection-input="$emit('selection-input', $event)"
      @item-deleted="$emit('item-deleted', $event)"
    />

    <b-form-group
      v-if="field.type === 'captureText'"
      :label="field.label ? field.label: field.key"
    >
      <capture-text-input
        v-model="internalValue"
        :label="field.label ? field.label: field.key"
        :validation-key="field.key"
        type="text"
      />
    </b-form-group>

    <b-form-group
      v-if="field.type === 'cellRangeSelector'"
      :label="field.label ? field.label: field.key"
    >
      <cell-range-selector
        v-model="internalValue"
        :label="field.label ? field.label: field.key"
        :validation-key="field.key"
        :initialize-expanded="false"
        :validation-rules="validationRules"
        :deletable="field.key === 'tableEnd' || field.key === 'identifier' ? true : false"
      />
    </b-form-group>

    <b-form-group
      v-if="field.type === 'autoPattern'"
      :label="field.label ? field.label : field.key"
    >
      <auto-pattern-input
        v-model="internalValue"
        type="text"
      />
    </b-form-group>
  </b-col>
</template>

<script>

import {
  BFormGroup, BCol, BRow, BFormCheckbox,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import PipeSeparatedInput from '@/components/UI/PipeSeparatedInput.vue'
import FormInput from '@/components/UI/FormInput.vue'
import CaptureTextInput from '@/components/UI/CaptureTextInput/CaptureTextInput.vue'
import CellRangeSelector from '@/components/UI/CellRangeSelector/CellRangeSelector.vue'
import AutoPatternInput from '@/components/UI/AutoPatternInput/AutoPatternInput.vue'
import NumericSlider from '@/components/UI/NumericSlider.vue'

export default {
  components: {
    BFormGroup,
    BCol,
    BRow,
    vSelect,
    ValidationProvider,
    PipeSeparatedInput,
    FormInput,
    CaptureTextInput,
    CellRangeSelector,
    AutoPatternInput,
    NumericSlider,
    BFormCheckbox,
  },
  props: {
    field: {
      type: Object,
      required: true,
    },
    value: {
      type: [String, Number, Array, Object, Boolean],
      required: false,
      default() {
        return null
      },
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    glActionOptions: {
      type: Array,
      required: false,
      default() {
        return []
      },
    },
  },
  data() {
    return {
      internalValue: '',
    }
  },
  computed: {
    options() {
      return {
        ...this.$store.getters['applicationSettings/options'],
        ...this.$store.getters['definitionSettings/options'],
      }
    },
    out() {
      return this.internalValue
    },
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
    },
    multiShipment() {
      return this.$store.getters['batch/multiShipment']
    },
  },
  watch: {
    out: {
      handler(val) {
        if (val !== this.value) {
          this.$emit('input', val)
        }
      },
    },
    value: {
      handler(val) {
        if (val !== this.out) {
          this.setInternalState()
        }
      },
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.internalValue = this.value
    },
    onDropdownOpen(key) {
      this.$nextTick(() => {
        this.$refs[key].$el.scrollIntoView()
      })
    },
    selectOptions(optionsId, filterByFileType) {
      let options = this.options[optionsId].items

      if (filterByFileType) {
        const batchFileType = this.isExcelBatch ? 'excel' : 'pdf'
        // Filter options based on file type
        options = options.filter(option => option.applicableFor.includes(batchFileType))
      }
      // Add check for multiShipment
      if (!this.multiShipment) {
        // Exclude the multishipment option if multiShipment is false
        options = options.filter(option => option.value !== 'multishipment')
      }
      return options
    },
    getColumnSize() {
      if (this.field.key === 'patterns') {
        return 10
      }

      if (this.field.key === 'autoPatterns') {
        return 6
      }

      if (this.field.type === 'numeric') {
        return 4
      }

      return 2
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style lang="scss" scoped>
.checkbox {
  margin-top: 2.5rem;
  margin-left: 1.5rem;
}
</style>
