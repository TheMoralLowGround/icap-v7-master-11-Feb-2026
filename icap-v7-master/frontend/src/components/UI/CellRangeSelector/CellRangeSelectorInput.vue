<template>
  <validation-provider
    #default="{ errors }"
    :name="label"
    :rules="validationRules"
    :vid="validationKey"
  >
    <b-input-group
      ref="popoverContainer"
      class="input-group-merge"
      :class="{ 'is-invalid': errors.length > 0 }"
    >
      <template #append>
        <b-input-group-text class="d-flex align-items-center py-0 my-0">
          <span class="d-flex align-items-center">
            <feather-icon
              v-if="selectedCellDetails === null"
              v-b-tooltip.hover
              icon="InfoIcon"
              size="15"
              title="Select cell range in excel view to capture value"
            />

            <feather-icon
              v-if="selectedCellDetails !== null"
              v-b-tooltip.hover
              icon="CrosshairIcon"
              size="15"
              class="cursor-pointer"
              :title="captured ? 'Captured!' : 'Capture'"
              @click="capture()"
            />

            <!-- Form Checkbox with Tooltip -->
            <b-form-checkbox
              v-if="isRegex"
              v-model="captureOption"
              v-b-tooltip.hover
              switch
              class="scaled-checkbox"
              style="margin-left: 5px; margin-right: -15px;"
              :title="tooltipText"
            />
          </span>
        </b-input-group-text>

        <span
          v-if="deletable && displayValue"
          class="my-auto"
        >
          <feather-icon
            v-b-tooltip.hover
            icon="Trash2Icon"
            class="cursor-pointer"
            style="margin-left: 0.5rem;"
            size="18"
            title="Clear Selection"
            @click="onDelete()"
          />
        </span>
      </template>

      <b-form-input
        v-model="displayValue"
        :state="errors.length > 0 ? false : null"
        :placeholder="placeholder"
        disabled
      />
    </b-input-group>

    <small class="text-danger">{{ errors[0] }}</small>
  </validation-provider>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import {
  VBTooltip, BFormInput, BInputGroup, BInputGroupText, BFormCheckbox,
} from 'bootstrap-vue'
import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BFormInput,
    BInputGroup,
    BInputGroupText,
    ValidationProvider,
    BFormCheckbox,
  },
  props: {
    value: {
      type: [Object, String],
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    toggleOption: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    id: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    validationKey: {
      type: String,
      required: true,
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    placeholder: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    deletable: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    isRegex: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
  },
  data() {
    return {
      inputItem: {},
      captured: false,
      captureOption: false,
      // popoverId: `popover-${Math.random().toString(36).substr(2, 9)}`, // Generate unique ID
    }
  },
  computed: {
    out() {
      return cloneDeep(this.inputItem)
    },
    getCellRangePermission() {
      return this.$store.getters['dataView/getCellRangePermission']
    },
    showSheetName() {
      return this.getCellRangePermission === 'Capture by Sheet Names'
    },
    showSheetNumber() {
      return this.getCellRangePermission === 'Capture by Sheet Numbers'
    },
    displayValue() {
      const {
        sheetNumber, sheetName, cellRange, cellValue,
      } = this.inputItem

      if (!sheetNumber && !sheetName && !cellRange && !cellValue) {
        return null
      }
      if (this.label === 'Identifier') {
        if (cellRange.includes(':')) {
          // If cellRange is a range like B6:B12, return only cellRange
          return cellRange
          // eslint-disable-next-line no-else-return
        } else {
          // If cellRange is single like B6, return the concatenated value
          return `${cellValue} ${cellRange}`
        }
      }
      if (this.captureOption) {
        return `${sheetNumber || ''} ${sheetName} ${cellValue}`
      }

      if (this.getCellRangePermission === 'Capture 1st Sheet Only') {
        return cellRange
      }

      if (!sheetName || !this.showSheetName) {
        return this.showSheetNumber ? `${sheetNumber || ''} ${cellRange}` : `${cellRange}`
      }
      if (!sheetNumber || !this.showSheetNumber) {
        return `${sheetName} ${cellRange}`
      }

      return `${sheetNumber || ''} ${sheetName} ${cellRange}`
    },
    selectedCellDetails() {
      return this.$store.getters['batch/selectedCellDetails']
    },
    tooltipText() {
      return this.captureOption ? 'Capture Cell Range' : 'Capture Value'
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
    captureOption(val) {
      if (val) {
        // Modify return model value when `Capture Value` is selected
        this.inputItem = {
          ...this.inputItem,
          sheetNumber: this.inputItem.sheetNumber || null, // Retain `sheetNumber`
          sheetName: this.inputItem.sheetName || null, // Retain `sheetName`
          cellRange: null,
          cellValue: this.inputItem.cellValue || null, // Retain `cellValue`
        }
      }
      let captureType = 'Capture Value'
      if (!val) {
        captureType = 'Capture Cell Range'
      }
      this.$emit('captureOption', { id: this.id, value: captureType })
    },
    getCellRangePermission(newValue, oldValue) {
      if (oldValue !== newValue) {
        // this.inputItem = {} // Reset inputItem when the value changes
        this.inputItem = {
          sheetNumber: null,
          cellRange: null,
          sheetName: null,
          cellValue: null,
        }
      }
    },
  },
  created() {
    this.setInternalState()
  },
  beforeDestroy() {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  methods: {
    setInternalState() {
      this.inputItem = cloneDeep(this.value)
      if (this.toggleOption === 'Capture Value') {
        this.captureOption = true
      }
    },
    capture() {
      this.inputItem = this.selectedCellDetails
      this.captured = true

      setTimeout(() => {
        this.captured = false
      }, 1000)
    },
    onDelete() {
      this.inputItem = {
        sheetNumber: null,
        cellRange: null,
        sheetName: null,
        cellValue: null,
      }
    },
  },
}
</script>

<style scoped>
  .scaled-checkbox {
    transform: scale(.9); /* Adjust scale to resize */
    transform-origin: left center; /* Keeps the checkbox aligned */
  }
</style>
