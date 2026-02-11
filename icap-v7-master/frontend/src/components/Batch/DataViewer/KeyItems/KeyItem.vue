<!--
 Organization: AIDocbuilder Inc.
 File: KeyItem.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component represents an individual key item in a list and allows users to select a key from a dropdown list.

 Main Features:
   - Key selection through a dynamic dropdown (`v-select`).
   - Validation for required fields using `validation-provider`.
   - Dynamic binding of key options based on the provided data.

 Dependencies:
   - `v-select` component from Vuetify
   - `validation-provider` from VeeValidate

 Notes:
   - Ensure that the `keySelectOptions` and `sortedOptions` props are provided correctly from the parent component.
-->
<template>
  <div>
    <!-- <pre>{{ keyItem }}</pre> -->
    <!-- <pre>{{ selectedBatch.definitionId }}</pre> -->
    <div
      :id="`key-item-${keyItem.id}`"
      :class="['key-item', 'd-flex', 'my-50', 'pt-key']"
    >
      <validation-provider
        #default="{ errors }"
        name="Key Field Name"
        rules="required"
        :vid="`keyLabel_${keyItem.id}`"
        class="regular-column flex-grow-1"
      >
        <b-form-group
          class="mb-0"
          :state="errors.length > 0 ? false:null"
        >
          <v-select
            v-if="mainMode==='tableSettings'"
            ref="vSelect"
            v-model="keyItem['keyLabel']"
            label="label"
            :options="profileTableKeys"
            :reduce="profileTableKeys => profileTableKeys.keyValue"
            @input="onKeyFieldNameChange"
          />
          <v-select
            v-else-if="mainMode==='keySettings'"
            ref="vSelect"
            v-model="keyItem['keyLabel']"
            label="label"
            :options="profileKeysForSelect"
            :reduce="profileKey => profileKey.keyValue"
            :disabled="isExtractedMatchedProfileKey && keyItem.type === 'auto'"
            @input="onKeyFieldNameChange"
            @open="handleDropdownOpen"
          />
          <!-- <b-form-input
            v-else
            v-model="displayKeyLabel"
            disabled
            @input="onKeyFieldNameChange"
            @open="handleDropdownOpen"
          />
          <small class="text-danger">{{ errors[0] }}</small> -->
        </b-form-group>
      </validation-provider>

      <div
        v-if="keyItem.isCompoundKey"
        class="dummy-column flex-grow-1 bg-transparent"
      >
        <div class="my-50">
          Compound Items
          <feather-icon
            :icon="displayCompoundItems ? 'ChevronDownIcon' : 'ChevronUpIcon'"
            class="cursor-pointer"
            style="margin-right: 20px;"
            size="20"
            @click="displayCompoundItems = !displayCompoundItems"
          />
          <b-button
            variant="outline-primary"
            @click="add"
          >
            Add +1
          </b-button>
        </div>
      </div>

      <div
        v-if="!keyItem.isCompoundKey"
        class="regular-column flex-grow-1"
      >
        <qualifier-select
          v-model="keyItem['qualifierValue']"
          :key-value="keyItem['keyLabel']"
          :key-options="keySelectOptions"
          label="Qualifier"
          validation-rules="required"
          :validation-key="`qualifierValue_${keyItem.id}`"
          :is-qualifier-value-empty="keyItem['qualifierValue'] === ''"
          @dropdownOpen="onDropdownOpen"
          @input="onQualifierChange"
        />
      </div>

      <validation-provider
        v-if="!keyItem.isCompoundKey"
        #default="{ errors }"
        name="Type"
        rules="required"
        :vid="`type_${keyItem.id}`"
        class="regular-column flex-grow-1"
      >
        <b-form-group
          class="mb-0"
          :state="errors.length > 0 ? false:null"
        >
          <v-select
            v-model="keyItem['type']"
            :label="applicationOptions['options-key-items-type'].lableKey"
            :options="inputTypeOptions('options-key-items-type')"
            :reduce="option => option[applicationOptions['options-key-items-type'].valueKey]"
            :clearable="false"
            @input="onTypeChange"
            @open="onDropdownOpen"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </b-form-group>
      </validation-provider>

      <div
        v-if="!keyItem.isCompoundKey"
        :class="['flex-grow-1', keyItem.type === 'prompt' ? 'prompt-expanded-column' : 'regular-column']"
      >
        <pipe-separated-input
          v-if="keyItem.type === 'keys'"
          v-model="keyItem['shape']"
          label="Label"
          selection-value-attr="text"
          listenable-input
          :hide-form-group-label="true"
          validation-rules="required|selectTextFromImage"
          :validation-key="`shape_${keyItem.id}`"
          :initialize-expanded="autoExpandInputSectionFields"
          @selection-input="shapeSelectionInputHandler($event)"
          @item-deleted="shapeSelectionItemDeleteHandler($event)"
        />

        <selector-input
          v-if="keyItem.type === 'selector'"
          v-model="selectorItems"
          :pos-fields="posFields"
          label="Label"
          :validation-key="`shape_${keyItem.id}`"
          :initialize-expanded="autoExpandInputSectionFields"
        />

        <cell-range-selector
          v-if="keyItem.type === 'cellRange'"
          v-model="cellRangeItems"
          label="Label"
          :validation-key="`shape_${keyItem.id}`"
          validation-rules="required"
          :initialize-expanded="autoExpandInputSectionFields"
          multiple
        />

        <validation-provider
          v-if="keyItem.type === 'anchors'"
          #default="{ failedRules }"
          name="Label"
          rules="requireAtleastOneAnchorShape:root"
          :vid="`shape_${keyItem.id}`"
        >
          <anchor-shapes
            v-model="anchorShapes"
            :validation-key="`shape_${keyItem.id}`"
            :failed-rules="failedRules"
            :initialize-expanded="autoExpandInputSectionFields"
            @focus="$emit('highlightAnchors', $event)"
          />
        </validation-provider>

        <validation-provider
          v-if="keyItem.type === 'barcode'"
          #default="{ errors }"
          name="Barcode Index"
          rules="required"
          :vid="`shape_${keyItem.id}`"
        >
          <b-form-input
            v-model="barcodeIndex"
            type="number"
            placeholder="Barcode Index"
            :state="errors.length > 0 ? false:null"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>

        <validation-provider
          v-if="keyItem.type === 'static'"
          #default="{ errors }"
          name="Label"
          rules="required"
          :vid="`shape_${keyItem.id}`"
        >
          <form-input
            v-model="keyItem['shape']"
            type="text"
            placeholder="Label"
            :state="errors.length > 0 ? false:null"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>
        <div
          v-if="keyItem.type === 'prompt'"
          class="prompt-wrapper"
        >
          <!-- Toggle Button -->
          <div
            class="prompt-toggle-header"
            @click="displayPromptFields = !displayPromptFields"
          >
            <span class="font-weight-bold">Prompt Details</span>
            <feather-icon
              :icon="displayPromptFields ? 'ChevronUpIcon' : 'ChevronDownIcon'"
              class="cursor-pointer"
              size="20"
            />
          </div>

          <!-- Collapsible Prompt Fields -->
          <b-collapse
            :id="`prompt-collapse-${keyItem.id}`"
            v-model="displayPromptFields"
            class="mt-1"
          >
            <div class="prompt-fields-container">
              <!-- DocClass Field -->
              <validation-provider
                #default="{ errors }"
                name="DocClass"
                :vid="`prompt_docclass_${keyItem.id}`"
              >
                <b-form-group
                  label="DocClass (Optional - Select one or multiple)"
                  label-for="docclass-select"
                  class="mb-1"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    v-model="docClassSelected"
                    :options="docClassOptions"
                    placeholder="Select or type document class..."
                    multiple
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>

              <!-- Field Description -->
              <validation-provider
                #default="{ errors }"
                name="Field Description"
                :vid="`prompt_field_desc_${keyItem.id}`"
              >
                <b-form-group
                  label="Field Description"
                  label-for="field-description"
                  class="mb-1"
                  :state="errors.length > 0 ? false:null"
                >
                  <b-form-textarea
                    v-model="keyItem.definition_prompt.Field_Description"
                    rows="2"
                    max-rows="6"
                    placeholder="Enter Description of the Field. Leaving empty will inherit from project"
                    :state="errors.length > 0 ? false:null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>

              <!-- Rules Description -->
              <validation-provider
                #default="{ errors }"
                name="Rules Description"
                :vid="`prompt_rules_desc_${keyItem.id}`"
              >
                <b-form-group
                  label="Rules Description"
                  label-for="rules-description"
                  class="mb-1"
                  :state="errors.length > 0 ? false:null"
                >
                  <b-form-textarea
                    v-model="keyItem.definition_prompt.Rules_Description"
                    rows="2"
                    max-rows="6"
                    placeholder="Enter rules description (optional)..."
                    :state="errors.length > 0 ? false:null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </div>
          </b-collapse>
        </div>
        <single-column-extractor-inputs
          v-if="keyItem.type === 'singleColumn'"
          v-model="singleColumnExtractor"
          :validation-key="`shape_${keyItem.id}`"
          :initialize-expanded="autoExpandInputSectionFields"
        />

        <single-column-extractor-excel-inputs
          v-if="keyItem.type === 'singleColumnExcel'"
          v-model="singleColumnExtractorExcel"
          :validation-key="`shape_${keyItem.id}`"
          validation-rules="required"
        />

        <excel-regex-extractor
          v-if="keyItem.type === 'excelRegexExtractor' && isExcelBatch"
          v-model="excelRegexExtractor"
          :validation-key="`shape_${keyItem.id}`"
          :initialize-expanded="autoExpandInputSectionFields"
        />
        <regex-extractor
          v-if="keyItem.type === 'regexExtractor' && !isExcelBatch"
          v-model="regexExtractor"
          :validation-key="`shape_${keyItem.id}`"
          :initialize-expanded="autoExpandInputSectionFields"
          @focus="$emit('highlightAnchors', $event)"
        />
      </div>
      <div
        v-if="!keyItem.isCompoundKey && keyItem.type !== 'prompt'"
        name="Value"
        rules="required"
        class="regular-column flex-grow-1"
      >
        <b-form-group
          class="mb-0"
        >
          <selector-input
            v-if="keyItem.type === 'selector'"
            v-model="selectorItemsValue"
            :pos-fields="posFields"
            label="Value"
            :validation-key="`shape_${keyItem.id}`"
            :initialize-expanded="autoExpandInputSectionFields"
          />
        </b-form-group>
      </div>
      <div class="action-column">
        <div class="action-column-content d-flex">
          <b-dropdown
            :disabled="!(displayAdditionalOptions || displayDateFormatOption || displayGrabMultiLinesOption)"
            right
            variant="link"
            no-caret
            toggle-class="p-0"
          >
            <template #button-content>
              <feather-icon
                icon="MoreVerticalIcon"
                size="20"
                class="align-middle text-body"
              />
            </template>
            <b-dropdown-form
              class="advance-settings-dropdown-form"
            >
              <p class="font-weight-bold">
                Advanced Settings
              </p>
              <template v-if="displayAdditionalOptions">
                <b-form-group>
                  <b-form-checkbox
                    v-model="keyItem.extractMultiple"
                  >
                    {{ isSysFieldRegexExtractor ? 'Multiple Match' : 'Extract Multiple' }}
                  </b-form-checkbox>
                </b-form-group>
                <b-form-group
                  v-if="!isSysFieldRegexExtractor"
                >
                  <b-form-checkbox
                    v-model="keyItem.removeDuplicates"
                  >
                    Remove Duplicates
                  </b-form-checkbox>
                </b-form-group>
                <b-form-group
                  v-if="!isSysFieldRegexExtractor"
                >
                  <b-form-checkbox
                    v-model="advanceSettings.groupMultiple"
                  >
                    Group Multiple
                  </b-form-checkbox>
                </b-form-group>
                <b-form-group
                  v-if="advanceSettings.groupMultiple"
                  label="Group Multiple Separator"
                >
                  <b-form-input
                    v-model="advanceSettings.groupMultipleSeparator"
                    @keydown.enter.prevent
                  />
                </b-form-group>
                <b-form-group
                  v-if="!isSysFieldRegexExtractor"
                >
                  <b-form-checkbox
                    v-model="advanceSettings.mergeValue"
                  >
                    Merge Value
                  </b-form-checkbox>
                </b-form-group>
                <b-form-group
                  v-if="advanceSettings.mergeValue"
                  label="Merge Value Separator"
                >
                  <b-form-input
                    v-model="advanceSettings.mergeValueSeparator"
                    @keydown.enter.prevent
                  />
                </b-form-group>
              </template>
              <template v-if="displayGrabMultiLinesOption">
                <b-form-group>
                  <b-form-checkbox
                    v-model="advanceSettings.grabMultiLines"
                  >
                    Grab Multi Lines
                  </b-form-checkbox>
                </b-form-group>
                <b-form-group
                  v-if="advanceSettings.grabMultiLines"
                >
                  <b-form-input
                    v-model="advanceSettings.grabMultiLinesNumber"
                    type="number"
                    @keydown.enter.prevent
                  />
                </b-form-group>
              </template>
              <template v-if="displayDateFormatOption">
                <b-form-group>
                  <b-form-checkbox
                    v-model="advanceSettings.dateFormat"
                    value="European"
                    unchecked-value=""
                  >
                    European Date
                  </b-form-checkbox>
                </b-form-group>
              </template>
            </b-dropdown-form>
          </b-dropdown>

          <feather-icon
            v-if="!keyItem.isCompoundItem"
            icon="AlignJustifyIcon"
            class="cursor-move handle"
            size="20"
          />
          <feather-icon
            v-if="!(isExtractedMatchedProfileKey && keyItem.type === 'auto')"
            v-b-tooltip.hover
            title="Delete Key"
            icon="Trash2Icon"
            class="cursor-pointer mx-auto"
            size="20"
            @click.stop="$emit('deleteItem')"
          />
        </div>
      </div>
    </div>
    <div
      v-if="keyItem.isCompoundKey"
      v-show="displayCompoundItems"
    >
      <compound-keys
        v-model="keyItem.compoundItems"
        :auto-expand-input-section-fields="autoExpandCompoundItemInputSectionFields"
        :compound-key-setting-name="compoundKeySettingName"
        @dropdownOpen="$emit('dropdownOpenCompoundItem', $event)"
        @highlightAnchors="$emit('highlightAnchorsCompoundItem', $event)"
      />
    </div>
    <hr
      v-if="!keyItem.isCompoundItem"
      class="key-item-separator my-50"
    >
  </div>
</template>

<script>

import {
  VBTooltip, BFormGroup, BDropdown, BDropdownForm, BFormCheckbox, BFormInput, BFormTextarea, BButton, BCollapse,
} from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import vSelect from 'vue-select'
import PipeSeparatedInput from '@/components/UI/PipeSeparatedInput.vue'
import FormInput from '@/components/UI/FormInput.vue'
import SelectorInput from '@/components/UI/SelectorInput/SelectorInput.vue'
import QualifierSelect from '@/components/UI/QualifierSelect.vue'
import AnchorShapes from '@/components/UI/AnchorShapes/AnchorShapes.vue'
import SingleColumnExtractorInputs from '@/components/UI/SingleColumnExtractorInputs/SingleColumnExtractorInputs.vue'
import SingleColumnExtractorExcelInputs from '@/components/UI/SingleColumnExtractorExcelInputs/SingleColumnExtractorExcelInputs.vue'
import ExcelRegexExtractor from '@/components/UI/RegexExtractor/ExcelRegexExtractor.vue'
import RegexExtractor from '@/components/UI/RegexExtractor/RegexExtractor.vue'
import CellRangeSelector from '@/components/UI/CellRangeSelector/CellRangeSelector.vue'
import CompoundKeys from '@/components/Batch/DataViewer/KeyItems/CompoundKeys.vue'

import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import { getDefaultCompoundKeys, getDefaultKey } from './key-helper'
// Default configuration for anchor shapes
// Anchor shapes define the positional constraints or references in a document or layout
const defaultAnchorShapes = {
  top: {
    text: null, // Text content at the top anchor
    pos: null, // Positional data for the anchor
    pageIndex: null, // Index of the page containing the anchor
    documentIndex: null, // Index of the document containing the anchor
    threshold: null, // Threshold value for matching or proximity
  },
  bottom: {
    text: null, // Text content at the bottom anchor
    pos: null, // Positional data for the anchor
    pageIndex: null, // Index of the page containing the anchor
    documentIndex: null, // Index of the document containing the anchor
    threshold: null, // Threshold value for matching or proximity
  },
  left: {
    text: null, // Text content at the left anchor
    pos: null, // Positional data for the anchor
    pageIndex: null, // Index of the page containing the anchor
    documentIndex: null, // Index of the document containing the anchor
    threshold: null, // Threshold value for matching or proximity
  },
  right: {
    text: null, // Text content at the right anchor
    pos: null, // Positional data for the anchor
    pageIndex: null, // Index of the page containing the anchor
    documentIndex: null, // Index of the document containing the anchor
    threshold: null, // Threshold value for matching or proximity
  },
}

// Default configuration for single-column extraction
// Used for extracting data from a single column in a table or layout
const defaultSingleColumnExtractor = {
  tableStart: null, // Starting point of the table
  tableEnd: null, // Ending point of the table
  startPos: null, // Start position of the column
  endPos: null, // End position of the column
  shape: null, // Shape data associated with the column
}

// Default configuration for single-column extraction in Excel
// Specifies the start and end cells for a column
const defaultSingleColumnExtractorExcel = {
  columnStartCell: null, // Start cell of the column
  columnEndCell: null, // End cell of the column
}

// Default configuration for extracting data using regex in Excel
// Includes cell ranges, patterns, and capture options
const defaultExcelRegexExtractor = {
  cellRanges: [
    {
      sheetNumber: null,
      cellRange: null, // Range of cells to search
      cellValue: null, // Value of the cell to match
      sheetName: null, // Name of the sheet containing the range
    },
    {
      sheetNumber: null,
      cellRange: null, // Range of cells to search
      cellValue: null, // Value of the cell to match
      sheetName: null, // Name of the sheet containing the range
    },
  ],
  patterns: [null], // Array of regex patterns for matching
  captureOption: '', // Option for capturing matched data
}

// Default configuration for general regex extraction
// Includes anchors and patterns for data extraction
const defaultRegexExtractor = {
  anchors: {
    top: {
      text: null, // Text content at the top anchor
      pos: null, // Positional data for the anchor
      pageIndex: null, // Index of the page containing the anchor
      documentIndex: null, // Index of the document containing the anchor
      threshold: null, // Threshold value for matching or proximity
    },
    bottom: {
      text: null, // Text content at the bottom anchor
      pos: null, // Positional data for the anchor
      pageIndex: null, // Index of the page containing the anchor
      documentIndex: null, // Index of the document containing the anchor
      threshold: null, // Threshold value for matching or proximity
    },
  },
  patterns: [null], // Array of regex patterns for data extraction
}

// Default advanced settings configuration
// Provides options for formatting and grouping extracted data
const defaultAdvanceSettings = {
  dateFormat: '', // Format for date values
  groupMultiple: false, // Whether to group multiple matches
  groupMultipleSeparator: ',', // Separator for grouped matches
  mergeValue: false, // Whether to merge multiple values into one
  grabMultiLines: false, // Whether to grab Multi Lines values
  mergeValueSeparator: ',', // Separator for merged values
  grabMultiLinesNumber: '',
}

export default {
  name: 'KeyItem',
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
    PipeSeparatedInput,
    FormInput,
    QualifierSelect,
    SelectorInput,
    AnchorShapes,
    ValidationProvider,
    BFormGroup,
    BDropdown,
    BDropdownForm,
    BFormCheckbox,
    BFormInput,
    BFormTextarea,
    BCollapse,
    SingleColumnExtractorInputs,
    SingleColumnExtractorExcelInputs,
    RegexExtractor,
    CellRangeSelector,
    CompoundKeys,
    BButton,
    ExcelRegexExtractor,
  },
  props: {
    // Props define the external data passed into the component
    // Expecting an object to be passed
    value: {
      type: Object,
      required: true,
    },
    // A flag to auto-expand input sections
    autoExpandInputSectionFields: {
      type: Boolean,
      required: true,
    },
    // Optional string to represent a parent identifier
    parent: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    // Array of options for key labels
    keyLableOptions: {
      type: Array,
      required: false,
      default() {
        return []
      },
    },
  },
  data() {
    // Data defines the reactive state for the component
    return {
      keyItem: {}, // Stores the details of the current key item
      selectorItems: [], // Stores items used for selector type keys
      selectorItemsValue: [], // Stores items used for selector type keys value
      anchorShapes: cloneDeep(defaultAnchorShapes), // Deep copy of the default anchor shapes
      barcodeIndex: null, // Index for barcode type keys
      singleColumnExtractor: cloneDeep(defaultSingleColumnExtractor), // Deep copy of the default single-column extractor
      singleColumnExtractorExcel: cloneDeep(defaultSingleColumnExtractorExcel), // Deep copy for Excel-specific single-column extraction
      regexExtractor: cloneDeep(defaultRegexExtractor), // Deep copy of default regex extractor settings
      excelRegexExtractor: cloneDeep(defaultExcelRegexExtractor), // Deep copy of Excel regex extractor settings
      advanceSettings: {}, // Stores advanced settings for the key
      cellRangeItems: [], // Stores cell range configurations for Excel
      posFields: ['startPos', 'topPos', 'endPos', 'bottomPos', 'pageId', 'pageIndex', 'selectedText'], // Fields for positional data
      autoExpandCompoundItemInputSectionFields: false, // Flag to auto-expand compound input sections
      initialized: false, // Tracks if the component is initialized
      displayCompoundItems: false, // Controls display of compound items
      displayPromptFields: false, // Controls display of prompt fields
    }
  },
  computed: {
    // Computed properties for deriving data based on state and props
    applicationOptions() {
      return this.$store.getters['applicationSettings/options'] // Fetch application settings from Vuex store
    },
    sortedOptions() {
      return this.$store.getters['definitionSettings/sortedOptions'] // Fetch sorted options from Vuex store
    },
    selectedBatchId() {
      return this.$store.getters['batch/batch'].id // Fetch sorted options from Vuex store
    },
    // selectedBatch() {
    //   return this.$store.getters['batch/batch']
    // },
    batchView() {
      return this.$store.getters['batch/view'] // Current view of the batch
    },
    batchProject() {
      return this.$store.getters['batch/batch']?.project // Project details from the batch
    },
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition']
    },
    keySelectOptions() {
      // Determine key selection options based on the current key item and batch view
      if (this.keyItem.isCompoundItem) {
        return this.keyLableOptions
      }

      // Check if the type is 'multishipment'
      if (this.selectedDefinition?.table[0]?.table_definition_data?.models?.type === 'multishipment') {
        // Combine and deduplicate the key options
        const combinedOptions = [
          ...this.$store.getters['definitionSettings/keyOptionsApplicableForTable'],
          ...this.$store.getters['definitionSettings/keyOptionsApplicableForKeys'],
        ]
        // Remove duplicates based on the unique `keyValue`
        const uniqueOptions = Array.from(
          new Map(combinedOptions.map(item => [item.keyValue, item])).values(),
        )

        // Return the combined list of key options
        return uniqueOptions.filter(option => option.type !== 'compound')
      }

      if (this.batchView === 'table') {
        return this.$store.getters['definitionSettings/keyOptionsApplicableForTable']
      }
      return this.$store.getters['definitionSettings/keyOptionsApplicableForKeys']
    },
    out() {
      // Prepares the output data for the key item with various transformations
      const keyItem = cloneDeep(this.keyItem) // Clone the current key item
      if (keyItem.type === 'anchors') {
        keyItem.anchorShapes = this.anchorShapes // Assign anchor shapes if type is anchors
      } else {
        keyItem.anchorShapes = null // Clear anchor shapes for other types
      }
      // if (keyItem.keyLabel && keyItem.keyLabel.includes(' ')) {
      //   keyItem.keyLabel = this.toCamelCase(keyItem.keyLabel)
      // }
      if (keyItem.type === 'singleColumn') {
        keyItem.singleColumnExtractor = this.singleColumnExtractor // Assign single-column extractor
      } else {
        keyItem.singleColumnExtractor = null
      }

      if (keyItem.type === 'selector') {
        // Transform selector type data
        this.posFields.forEach(posField => {
          keyItem.keyItemLabels[posField] = this.selectorItems.map(posItem => posItem[posField]).join('|')
          keyItem.keyItemValues[posField] = this.selectorItemsValue.map(posItem => posItem[posField]).join('|')
        })
        keyItem.shape = this.selectorItems.map(() => 'Selector').join('|')
        keyItem.selector = true
      } else {
        keyItem.selector = false
        // For non-selector types: ensure shape is populated from selectedText if needed
        // The v-model on PipeSeparatedInput should set shape, but as a fallback, use selectedText
        if (keyItem.selectedText && keyItem.type !== 'static') {
          // Split both - DON'T filter empty values as they represent positions
          const shapeValues = (keyItem.shape || '').split('|')
          const selectedTextValues = keyItem.selectedText.split('|')

          // Copy selectedText to shape for positions where shape is empty but selectedText has a value
          const mergedShape = shapeValues.map((shapeVal, index) => {
            // If shape is empty at this position but selectedText has a value, use selectedText
            if (!shapeVal && selectedTextValues[index]) {
              return selectedTextValues[index]
            }
            return shapeVal
          })

          // Handle case where selectedText has more items than shape
          if (selectedTextValues.length > shapeValues.length) {
            for (let i = shapeValues.length; i < selectedTextValues.length; i += 1) {
              mergedShape.push(selectedTextValues[i] || '')
            }
          }

          keyItem.shape = mergedShape.join('|')
        }
      }

      if (keyItem.type === 'regexExtractor') {
        keyItem.regexExtractor = this.regexExtractor
      } else if (keyItem.type === 'excelRegexExtractor' && this.isExcelBatch) {
        keyItem.excelRegexExtractor = this.excelRegexExtractor
      } else {
        keyItem.regexExtractor = null
        keyItem.excelRegexExtractor = null
      }

      // Advanced settings processing
      const advanceSettings = {}
      if (this.displayDateFormatOption) {
        advanceSettings.dateFormat = this.advanceSettings.dateFormat
      }
      if (this.displayGrabMultiLinesOption) {
        advanceSettings.grabMultiLines = this.advanceSettings.grabMultiLines
        advanceSettings.grabMultiLinesNumber = this.advanceSettings.grabMultiLinesNumber
      }
      if (this.displayAdditionalOptions) {
        advanceSettings.groupMultiple = this.advanceSettings.groupMultiple
        advanceSettings.groupMultipleSeparator = this.advanceSettings.groupMultipleSeparator
        advanceSettings.mergeValue = this.advanceSettings.mergeValue
        advanceSettings.mergeValueSeparator = this.advanceSettings.mergeValueSeparator
      }
      keyItem.advanceSettings = advanceSettings

      // Type-specific data
      const typeData = {}
      if (keyItem.type === 'barcode') {
        typeData.barcodeIndex = parseInt(this.barcodeIndex, 10)
      }
      if (keyItem.type === 'cellRange') {
        typeData.cellRangeItems = this.cellRangeItems
      }
      if (keyItem.type === 'singleColumnExcel') {
        typeData.singleColumnExtractorExcel = this.singleColumnExtractorExcel
        keyItem.singleColumnExtractor = true
      }
      keyItem.typeData = typeData

      return keyItem
    },
    displayAdditionalOptions() {
      // Determine if additional options should be displayed based on key label and project
      const applicableForKeyLabel = ['references', 'filler', 'notes'].includes(this.keyItem.keyLabel)
      return this.isSysFieldRegexExtractor || applicableForKeyLabel || this.batchProject === 'CustomsEntryUpdate'
    },
    isSysFieldRegexExtractor() {
      // Check if the key is a system field using regex extractors
      return this.keyItem.keyLabel === 'sysField' && (this.keyItem.type === 'regexExtractor' || this.keyItem.type === 'excelRegexExtractor')
    },
    displayGrabMultiLinesOption() {
      return this.keyItem.type === 'regexExtractor' && this.batchProject === 'Freight'
    },
    displayDateFormatOption() {
      // Display date format option for key labels ending with 'date'
      const { keyLabel } = this.keyItem
      if (!keyLabel) {
        return false
      }
      return keyLabel.toLowerCase()?.endsWith('date')
    },
    isExcelBatch() {
      // Check if the current batch is Excel-based
      return this.$store.getters['batch/batch'].isExcel
    },
    compoundKeySettingName() {
      // Retrieve the compound key setting name for the current key label
      const { keyLabel } = this.keyItem
      if (!keyLabel) {
        return null
      }
      const keyOptions = this.sortedOptions['options-keys'].items
      const keyOption = keyOptions.find(item => item.keyValue === keyLabel)
      if (!keyOption) {
        return null
      }
      return keyOption.compoundKeys
    },
    isCompoundKey() {
      // Determine if the current key is a compound key
      return !!this.compoundKeySettingName
    },
    optionsKeyItems() {
      // Fetch options key items from the Vuex store
      return this.$store.getters['definitionSettings/options']['options-keys'].items
    },
    defaultBehaviour() {
      // Fetch default behaviour settings from the Vuex store
      return this.$store.getters['defaultSettings/defaultBehaviour']
    },

    // Fetch Profile Keys
    ProfileKeys() {
      return this.$store.getters['batch/profileDetails'].keys
    },
    docClassOptions() {
      const profileDetails = this.$store.getters['batch/profileDetails'] || {}
      const documents = profileDetails.documents || []
      const translatedDocuments = profileDetails.translated_documents || []

      // Get list of doc_types that have been translated (original doc_types to exclude)
      const translatedDocTypes = translatedDocuments.map(td => td.doc_type)

      // Filter documents where category is 'Processing' and extract doc_type
      // Exclude doc_types that have been translated to another type
      return documents
        .filter(doc => doc.category === 'Processing' && doc.doc_type)
        .filter(doc => !translatedDocTypes.includes(doc.doc_type)) // Exclude translated doc_types
        .map(doc => doc.doc_type)
        .filter((value, index, self) => self.indexOf(value) === index) // Remove duplicates
    },
    mainMode() {
      return this.$store.getters['dataView/mainMode'] // Returns the current main mode from the store
    },
    profileTableKeys() {
      const keys = this.$store.getters['batch/profileTableKeys']
      if (!Array.isArray(keys) || !keys.length) return []

      return keys.slice().sort((a, b) => {
        const labelA = (a.label || '').toLowerCase()
        const labelB = (b.label || '').toLowerCase()
        return labelA.localeCompare(labelB)
      })
    },
    profileKeysForSelect() {
      const keys = this.ProfileKeys || []

      // Filter only 'key' type (not 'table' type)
      return keys
        .filter(key => key.type !== 'table')
        .map(key => ({
          // label: this.toNormalLabel(key.label || key.keyValue || ''),
          label: key.label || key.keyValue || '',
          keyValue: key.keyValue || '',
        }))
    },
    displayKeyLabel: {
    // Getter: Convert camelCase to normal case for display
      get() {
        return this.toNormalLabel(this.keyItem.keyLabel)
      },
      // Setter: Convert normal case to camelCase for storage
      set(normalValue) {
        this.keyItem.keyLabel = `camelCase${normalValue}`
      },
    },
    // Computed property to handle DocClass multi-select
    // Converts between comma-separated string (backend) and array (frontend)
    docClassSelected: {
      get() {
        const docClass = this.keyItem?.definition_prompt?.DocClass
        if (!docClass) return []
        if (typeof docClass === 'string') {
          // Split comma-separated string into array, trim whitespace
          return docClass.split(',').map(item => item.trim()).filter(item => item)
        }
        if (Array.isArray(docClass)) {
          return docClass
        }
        return []
      },
      set(value) {
        // Convert array to comma-separated string for backend storage
        if (!this.keyItem.definition_prompt) {
          this.keyItem.definition_prompt = {
            DocClass: '',
            Field_Description: '',
            Rules_Description: '',
          }
        }
        if (Array.isArray(value)) {
          this.keyItem.definition_prompt.DocClass = value.join(', ')
        } else {
          this.keyItem.definition_prompt.DocClass = value || ''
        }
      },
    },
    flatNodes() {
      return this.$store.getters['batch/flatNodes']
    },
    transactionNodes() {
      return this.$store.getters['batch/transactionNodes']
    },
    // matchedProfileKeys() {
    //   return this.$store.getters['batch/matchedProfileKeys'] || []
    // },
    extractedMatchedProfileKeys() {
      return this.$store.getters['batch/extractedMatchedProfileKeys'] || []
    },
    // Check if current key is an extracted matched profile key (from backend with is_profile_key_found and is_pure_autoextraction)
    isExtractedMatchedProfileKey() {
      if (!this.keyItem?.keyLabel) return false
      const { keyLabel } = this.keyItem
      return this.extractedMatchedProfileKeys.includes(keyLabel)
    },
    // PROMPT KEYS - COMMENTED OUT (NOT NEEDED ANYMORE - ALL KEYS GO IN DEFINITION)
    // Check if current key is a duplicate prompt key
    // isDuplicateKey() {
    //   if (this.keyItem?.type !== 'prompt') return false
    //   const duplicates = this.$store.getters['dataView/duplicatePromptKeys'] || []
    //   return duplicates.some(dup => dup.key_value === this.keyItem.keyLabel)
    // },
  },
  watch: {
    // Watcher for `displayAdditionalOptions`
    displayAdditionalOptions() {
      if (!this.displayAdditionalOptions) {
        // Reset advanced settings when `displayAdditionalOptions` is false
        this.keyItem.extractMultiple = false // Disable multiple extraction
        this.keyItem.removeDuplicates = false // Disable duplicate removal
        this.advanceSettings.groupMultiple = defaultAdvanceSettings.groupMultiple // Reset to default grouping setting
        this.advanceSettings.groupMultipleSeparator = defaultAdvanceSettings.groupMultipleSeparator // Reset grouping separator
        this.advanceSettings.mergeValue = defaultAdvanceSettings.mergeValue // Reset merging setting
        this.advanceSettings.mergeValueSeparator = defaultAdvanceSettings.mergeValueSeparator // Reset merging separator
      }
    },

    // Watcher for `displayDateFormatOption`
    displayDateFormatOption() {
      if (!this.displayDateFormatOption) {
        // Reset date format when `displayDateFormatOption` is false
        this.advanceSettings.dateFormat = defaultAdvanceSettings.dateFormat
      }
    },
    // Watcher for `displayGrabMultiLinesOption`
    displayGrabMultiLinesOption() {
      if (!this.displayGrabMultiLinesOption) {
        this.advanceSettings.grabMultiLines = defaultAdvanceSettings.grabMultiLines // Reset grab Multi Lines setting
        this.advanceSettings.grabMultiLinesNumber = defaultAdvanceSettings.grabMultiLinesNumber // Reset grab Multi Lines Number
      }
    },

    // Watcher for `out` (computed property that represents the key item output)
    out: {
      handler(val) {
        // Compare new value of `out` with the `value` prop
        if (!isEqual(val, this.value)) {
          // Emit an 'input' event if `out` has changed
          this.$emit('input', val)
        }
      },
      deep: true, // Deep watch to track changes to nested properties
    },

    // Watcher for `value` prop
    value: {
      handler(val) {
        // Compare new `value` prop with `out` computed property
        if (!isEqual(val, this.out)) {
          // Update internal state if `value` has changed
          this.setInternalState()
        }
      },
      deep: true, // Deep watch to track changes to nested properties
    },

    // Watcher for `isCompoundKey`
    isCompoundKey() {
      if (this.initialized) {
        // Set compound key data only if the component is initialized
        this.setCompoundKeyData()
      }
    },
  },

  created() {
    // Lifecycle hook triggered when the component is created
    this.setInternalState() // Initialize the component's internal state

    // Delay initialization flag until the next DOM update cycle
    this.$nextTick(() => {
      this.initialized = true // Mark the component as initialized
    })
  },
  methods: {
    toNormalLabel(str) {
      if (!str) return ''
      if (str.includes(' ')) return str // Already normal case
      return str
        .replace(/([A-Z])/g, ' $1') // insert space before capital letters
        .replace(/^./, s => s.toUpperCase()) // capitalize first character
        .trim()
    },

    // Convert normal format back to camelCase
    toCamelCase(str) {
      if (!str) return ''
      const camel = str
        .replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) => (index === 0 ? word.toLowerCase() : word.toUpperCase()))
        .replace(/\s+/g, '')
      return camel.charAt(0).toLowerCase() + camel.slice(1)
    },
    findBatchNodeById(nodes, batchId) {
      const stack = [...nodes]
      while (stack.length) {
        const node = stack.pop()
        if (node?.id === batchId) return node
        if (node.children?.length) stack.push(...node.children)
      }
      return null
    },
    flattenLabelsWithNodes(rootNode) {
      const labelNodeMap = new Map()
      const stack = rootNode ? [rootNode] : []

      while (stack.length) {
        const node = stack.pop()
        if (node?.label) {
          const normalizedLabel = this.toCamelCase(node.label)
          labelNodeMap.set(normalizedLabel, node)
        }
        if (node.children?.length) {
          stack.push(...node.children)
        }
      }

      return labelNodeMap
    },

    // areAnyKeysMissing(keysWithValues, nodes) {
    //   const batchNode = this.findBatchNodeById(nodes, this.selectedBatchId)
    //   if (!batchNode) return true // consider missing if batch not found

    //   const labelNodeMap = this.flattenLabelsWithNodes(batchNode)

    //   return keysWithValues.some(({ keyLabel }) => {
    //     const normalizedKey = this.toCamelCase(keyLabel)
    //     const matchingNode = labelNodeMap.get(normalizedKey)

    //     return (
    //       !matchingNode
    //   || (!matchingNode.v && !matchingNode.value)
    //     )
    //   })
    // },
    // Method to set the internal state of the component based on the input `value` prop
    setInternalState() {
      const keyItem = cloneDeep(this.value) // Clone the `value` object to avoid direct mutation
      delete keyItem.advanceSettings // Remove advance settings from the cloned object
      delete keyItem.typeData // Remove type-specific data from the cloned object
      const advanceSettings = cloneDeep(this.value.advanceSettings) // Clone advance settings

      this.keyItem = keyItem // Update the internal `keyItem`

      // Initialize state based on the type of `keyItem`
      if (this.keyItem.type === 'anchors') {
        this.anchorShapes = this.value.anchorShapes
      }

      if (this.keyItem.type === 'singleColumn') {
        this.singleColumnExtractor = this.value.singleColumnExtractor
      }

      // Handle `selector` type by splitting fields into items
      const items = []
      const itemsValue = []
      if (this.keyItem.type === 'selector') {
        const noOfItems = this.keyItem[this.posFields[0]].split('|').length // Currently using number of items by taking label count only but if no. of values is more than no. of lebels then need to seperate for values logic
        for (let index = 0; index < noOfItems; index += 1) {
          const item = {}
          const valueItem = {}
          this.posFields.forEach(posField => {
            const fieldValue = this.keyItem.keyItemLabels[posField]
            const keyItemValue = this.keyItem.keyItemValues[posField]
            item[posField] = fieldValue !== '' ? fieldValue.split('|')[index] : ''
            valueItem[posField] = keyItemValue !== '' ? keyItemValue.split('|')[index] : ''
          })
          items[index] = item
          itemsValue[index] = valueItem
        }
      }
      this.selectorItems = items
      this.selectorItemsValue = itemsValue

      // Initialize state for other types
      if (this.keyItem.type === 'regexExtractor') {
        this.regexExtractor = this.value.regexExtractor
      }

      if (this.keyItem.type === 'excelRegexExtractor') {
        this.excelRegexExtractor = this.value.excelRegexExtractor
      }

      if (this.keyItem.type === 'barcode') {
        this.barcodeIndex = this.value.typeData.barcodeIndex
          ? parseInt(this.value.typeData.barcodeIndex, 10)
          : null
      }

      if (this.keyItem.type === 'cellRange') {
        this.cellRangeItems = this.value.typeData.cellRangeItems || []
      }

      if (this.keyItem.type === 'singleColumnExcel') {
        this.singleColumnExtractorExcel = this.value.typeData.singleColumnExtractorExcel
      }

      // Merge default and provided advance settings
      this.advanceSettings = {
        ...cloneDeep(defaultAdvanceSettings),
        ...advanceSettings,
      }
    },

    // Handles input changes for shape selection
    shapeSelectionInputHandler(data) {
      this.posFields.forEach(posField => {
        let newValue
        if (data.index === -1) { // If index is -1, update all fields
          // Map 'text' from selectionData to 'selectedText' field
          const fieldValue = posField === 'selectedText'
            ? (data.selectionData.text || '')
            : (data.selectionData[posField] || '')
          newValue = fieldValue
        } else {
          const currentValue = this.keyItem[posField] || '' // Handle undefined fields
          const newValueArray = currentValue ? currentValue.split('|') : []
          // Map 'text' from selectionData to 'selectedText' field
          const fieldValue = posField === 'selectedText'
            ? (data.selectionData.text || '')
            : (data.selectionData[posField] || '')
          newValueArray[data.index] = fieldValue
          newValue = newValueArray.join('|')
        }
        this.keyItem[posField] = newValue // Update the specific field
      })
    },

    // Handles deletion of a shape selection item
    shapeSelectionItemDeleteHandler(itemIndex) {
      this.posFields.forEach(posField => {
        const currentValue = this.keyItem[posField] || '' // Handle undefined fields
        const newValueArray = currentValue ? currentValue.split('|') : []
        newValueArray.splice(itemIndex, 1) // Remove the item at the specified index
        const newValue = newValueArray.join('|')
        this.keyItem[posField] = newValue // Update the field with the modified array
      })
    },

    // Handles changes to the key field name
    onKeyFieldNameChange(keyValue) {
    // keyValue will be in camelCase from the v-select :reduce function
    // No need to convert here since we're storing camelCase directly
      this.keyItem.keyLabel = keyValue

      if (this.defaultBehaviour.compoundKeys.includes(this.parent)) {
        this.keyItem.type = 'static'
        this.keyItem.shape = 'ERROR'
      }

      if (this.keyItem.isCompoundItem) {
        return
      }

      let optionsKeyItem
      if (this.mainMode === 'tableSettings') {
        optionsKeyItem = this.profileTableKeys?.find(e => e.keyValue === keyValue)
      } else if (this.mainMode === 'keySettings') {
        optionsKeyItem = this.ProfileKeys?.find(e => (e.keyValue || '') === keyValue)
      } else {
        optionsKeyItem = this.ProfileKeys?.find(e => e.keyValue === keyValue)
      }
      this.keyItem.export = optionsKeyItem?.export
    },

    // Resets state when the type of key item changes
    onTypeChange() {
      this.anchorShapes = cloneDeep(defaultAnchorShapes)
      this.barcodeIndex = null
      this.singleColumnExtractor = cloneDeep(defaultSingleColumnExtractor)
      this.singleColumnExtractorExcel = cloneDeep(defaultSingleColumnExtractorExcel)
      this.selectorItems = []
      this.selectorItemsValue = []
      this.keyItem.shape = ''
      this.shapeSelectionInputHandler({
        index: -1,
        selectionData: {
          startPos: '',
          endPos: '',
          topPos: '',
          bottomPos: '',
          pageId: '',
          pageIndex: '',
          selectedText: '',
        },
      })
      this.regexExtractor = cloneDeep(defaultRegexExtractor)
      this.excelRegexExtractor = cloneDeep(defaultExcelRegexExtractor)
      this.cellRangeItems = []

      // Clear anchor highlights if the current key item is highlighted
      if (this.keyItem.id === this.$store.getters['batch/highlightKeyAnchorsData'].keyItemId) {
        this.$store.dispatch('batch/clearAnchorHighlights')
      }
      if (this.keyItem.type === 'auto') {
        this.keyItem.qualifierValue = ''
      }
      // Initialize definition_prompt field with default object structure when type is changed to prompt
      if (this.keyItem.type === 'prompt') {
        if (!this.keyItem.definition_prompt || typeof this.keyItem.definition_prompt !== 'object') {
          this.keyItem.definition_prompt = {
            DocClass: '',
            Field_Description: '',
            Rules_Description: '',
          }
        }
        // Expand prompt fields by default when switching to prompt type
        this.displayPromptFields = true
      }
    },

    handleDropdownOpen() {
      this.onDropdownOpen()
      this.scrollToSelected()
    },

    // Emits an event when a dropdown is opened
    onDropdownOpen() {
      this.$nextTick(() => {
        this.$emit('dropdownOpen')
      })
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        // Try finding the dropdown menu
        const dropdownMenuItems = this.$refs.vSelect?.$el?.querySelector('.vs__dropdown-menu')
        if (!dropdownMenuItems) return // Ensure the dropdown exists before proceeding

        let selectedIndex = -1
        let optionsList = []

        // Determine which options list and how to find the selected index based on mode
        if (this.mainMode === 'keySettings') {
          optionsList = this.profileKeysForSelect
          selectedIndex = optionsList.findIndex(option => option.keyValue === this.keyItem.keyLabel)
        } else if (this.mainMode === 'tableSettings') {
          optionsList = this.profileTableKeys
          selectedIndex = optionsList.findIndex(option => option.keyValue === this.keyItem.keyLabel)
        } else {
          optionsList = this.keySelectOptions
          selectedIndex = optionsList.findIndex(option => option[this.sortedOptions['options-keys'].valueKey] === this.keyItem.keyLabel)
        }

        if (selectedIndex >= 0 && optionsList.length > 0) {
          const itemHeight = dropdownMenuItems.scrollHeight / optionsList.length
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },

    // Retrieves input type options based on batch file type
    inputTypeOptions(optionsId) {
      const options = this.applicationOptions[optionsId].items
      const batchFileType = this.isExcelBatch ? 'excel' : 'pdf'
      let applicableOptions = options.filter(option => option.applicableFor.includes(batchFileType))

      const keyOptionItem = this.keySelectOptions.find(item => item.keyValue === this.keyItem.keyLabel)
      if (!(this.keyItem.keyLabel?.toLowerCase()?.includes('date') || keyOptionItem?.qualifier?.toLowerCase() === 'milestone')) {
        applicableOptions = applicableOptions.filter(option => option.value !== 'today')
      }

      // Only show 'auto' type option if this key is an extracted matched profile key
      if (!this.isExtractedMatchedProfileKey) {
        applicableOptions = applicableOptions.filter(option => option.value !== 'auto')
      }

      return applicableOptions
    },

    // Sets data for compound keys
    setCompoundKeyData() {
      if (this.isCompoundKey) {
        this.keyItem.isCompoundKey = true
        this.autoExpandCompoundItemInputSectionFields = true
        this.keyItem.compoundItems = getDefaultCompoundKeys(this.isExcelBatch, this.compoundKeySettingName)
        this.keyItem.qualifierValue = ''
        this.keyItem.type = null
        this.displayCompoundItems = true
      } else {
        this.keyItem.isCompoundKey = false
        this.keyItem.compoundItems = []
        this.keyItem.type = getDefaultKey(this.isExcelBatch).type
        this.displayCompoundItems = false
      }

      // Trigger changes caused by type change
      this.onTypeChange()
    },

    // Adds a new compound item
    add() {
      const record = getDefaultKey(this.isExcelBatch)
      record.isCompoundItem = true

      const compoundItems = [...this.keyItem.compoundItems]
      compoundItems.push(record)
      this.keyItem.compoundItems = compoundItems

      this.displayCompoundItems = true
    },

    // Handles changes to the qualifier value
    onQualifierChange(qualifierValue) {
      if (!qualifierValue) {
        return // Do nothing if qualifier value is empty
      }

      if (['AWBPackWeight', 'AWBHouseBill', 'AWBMasterBill'].includes(qualifierValue)) {
        this.keyItem.type = 'regexExtractor' // Set type to regex extractor for specific qualifiers
        return
      }

      if (qualifierValue.split('AWB')[0] === '') {
        this.keyItem.type = 'auto'
        this.keyItem.shape = ''
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style  lang="scss" scoped>
.key-item {
  column-gap: 10px;
}

.duplicate-key-highlight {
  border: 2px solid #ea5455 !important;
  background-color: #fff5f5 !important;
  border-radius: 4px;
  padding: 8px !important;
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.pt-key{
  padding: 3px 3px 0 0;
}
.regular-column {
  flex-basis:300px;
}

.prompt-expanded-column {
  flex-basis:600px;
}

.dummy-column {
  flex-basis:900px;
}

.action-column {
  flex-basis:80px;
}

.action-column-content {
 column-gap: 10px;
}

.advance-settings-dropdown-form {
  width: 250px;

}

/* Optional: ensure consistent styling for v-select */
.vs__dropdown-toggle {
  background-color: transparent;
  border: 1px solid #a1a1a3;
  border-radius: 0.357rem;
  padding: 3px;
}

.dark-layout .vs__dropdown-toggle {
  background-color: transparent;
  border: 1px solid #a1a1a3;
  border-radius: 0.357rem;
  padding: 3px;
}

/* Clear input background if needed */
.vs__selected-options
.vs__search {
  background-color: transparent !important;
}

.prompt-wrapper {
  width: 100%;
}

.prompt-toggle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border: 1px solid #d8d6de;
  border-radius: 0.357rem;
  cursor: pointer;
  user-select: none;
}

.dark-layout .prompt-toggle-header {
  background-color: #283046;
  border-color: #3b4253;
}

</style>
