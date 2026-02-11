<template>
  <b-tr>
    <b-td>
      <validation-provider
        #default="{ errors }"
        name="Type"
        rules="required"
        :vid="`type_${ruleIndex}`"
      >
        <b-form-group
          class="mb-0"
          :state="errors.length > 0 ? false:null"
        >
          <v-select
            ref="vSelect"
            v-model="rule.type"
            label="label"
            :options="ruleTypeOptions"
            :reduce="option => option.value"
            :clearable="false"
            @input="onRuleTypeChange"
            @open="handleDropdownOpen"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </b-form-group>
      </validation-provider>
    </b-td>
    <b-td>
      <div
        v-if="selectedRuleType"
        class="d-flex"
        style="column-gap: 0.5rem;"
      >
        <div
          v-for="inputField of displayFields"
          :key="inputField.key"
          class="w-100"
        >
          <key-rule-value-input
            v-if="inputField.type === 'key-rule-value-input'"
            v-model="rule.inputs[inputField.key]"
            :placeholder="inputField.placeholder"
            :validation-id="`${inputField.placeholder}_${ruleIndex}`"
            :validation-rules="inputField.validationRules"
            @dropdownOpen="onDropdownOpen"
          />

          <validation-provider
            v-if="inputField.type === 'text-input'"
            #default="{ errors }"
            :name="inputField.placeholder"
            :rules="inputField.validationRules"
            :vid="`${inputField.placeholder}_${ruleIndex}`"
          >
            <form-input
              v-if="isTextInputTypeNunber"
              id="rule-text-input"
              v-model="rule.inputs[inputField.key]"
              type="tel"
              :placeholder="inputField.placeholder"
              :state="errors.length > 0 ? false:null"
              @input="filterIntegers(inputField.key, $event)"
            />
            <form-input
              v-else
              v-model="rule.inputs[inputField.key]"
              type="text"
              :placeholder="inputField.placeholder"
              :state="errors.length > 0 ? false:null"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </validation-provider>

          <validation-provider
            v-if="inputField.type === 'number-input'"
            #default="{ errors }"
            :name="inputField.placeholder"
            :rules="inputField.validationRules"
            :vid="`${inputField.placeholder}_${ruleIndex}`"
          >
            <form-input
              v-model.number="rule.inputs[inputField.key]"
              type="number"
              :placeholder="inputField.placeholder"
              :state="errors.length > 0 ? false:null"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </validation-provider>

          <validation-provider
            v-if="inputField.type === 'select'"
            #default="{ errors }"
            :name="inputField.placeholder"
            :rules="inputField.validationRules"
            :vid="`${inputField.placeholder}_${ruleIndex}`"
          >
            <b-form-group
              class="mb-0"
              :state="errors.length > 0 ? false:null"
            >
              <v-select
                v-model="rule.inputs[inputField.key]"
                :options="inputField.options"
                :reduce="option => option.value"
                :placeholder="inputField.placeholder"
              />
              <small class="text-danger">{{ errors[0] }}</small>
            </b-form-group>
          </validation-provider>
          <Key-field-drop-down
            v-if="['key-field-drop-down', 'multiple-key-field-drop-down'].includes(inputField.type)"
            v-model="rule.inputs[inputField.key]"
            :label="inputField.placeholder"
            :multiple-drop-down="inputField.type === 'multiple-key-field-drop-down'"
            :validation-rules="inputField.validationRules"
            :validation-key="`${inputField.placeholder}_${ruleIndex}`"
            :rule-inputs="rule.inputs"
            :input-field-key="inputField.key"
          />

          <pipe-separated-input
            v-if="inputField.type === 'pipe-separated-input'"
            v-model="rule.inputs[inputField.key]"
            :label="inputField.placeholder"
            selection-value-attr="text"
            listenable-input
            :hide-form-group-label="true"
            :validation-rules="inputField.validationRules"
            :validation-key="`${inputField.placeholder}_${ruleIndex}`"
          />
        </div>
      </div>
    </b-td>
    <b-td>
      <div class="d-flex">
        <feather-icon
          icon="AlignJustifyIcon"
          class="cursor-move handle mr-1"
          size="20"
        />
        <feather-icon
          v-b-tooltip.hover
          title="Delete Rule"
          icon="Trash2Icon"
          class="cursor-pointer mx-auto"
          size="20"
          @click.stop="$emit('deleteItem')"
        />
      </div>
    </b-td>
  </b-tr>
</template>

<script>

import {
  VBTooltip, BTr, BTd, BFormGroup,
} from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import vSelect from 'vue-select'
import { ValidationProvider } from 'vee-validate'

// eslint-disable-next-line no-unused-vars
import { required, integer } from '@validations'

import FormInput from '@/components/UI/FormInput.vue'
import KeyRuleValueInput from '@/components/UI/KeyRuleValueInput.vue'
import PipeSeparatedInput from '@/components/UI/PipeSeparatedInput.vue'
import KeyFieldDropDown from '@/components/UI/KeyFieldDropDown.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
    FormInput,
    BTr,
    BTd,
    KeyRuleValueInput,
    ValidationProvider,
    BFormGroup,
    PipeSeparatedInput,
    KeyFieldDropDown,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    ruleIndex: {
      type: Number,
      required: true,
    },
    ruleTypes: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      rule: null,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.rule)
    },
    ruleTypeOptions() {
      return this.ruleTypes.map(ruleType => ({
        value: ruleType.key,
        label: ruleType.label,
      }))
    },
    selectedRuleType() {
      return this.ruleTypes.find(ruleType => ruleType.key === this.rule?.type)
    },
    displayFields() {
      if (!this.selectedRuleType) {
        return []
      }
      const { fields } = this.selectedRuleType
      const filteredFields = fields.filter(field => this.matchesCondition(field.displayCondition, this.rule.inputs))
      return filteredFields
    },
    isTextInputTypeNunber() {
      if (this.rule.type === 'deductDays' || this.rule.type === 'addDays') {
        return true
      }
      return false
    },
    keyOptionsForRules() {
      return this.$store.getters['definitionSettings/keyOptionsForRules']
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
    displayFields: {
      handler(newValue, oldValue) {
        if (!isEqual(newValue, oldValue)) {
          const defaultRuleInputs = {}
          this.displayFields.forEach(displayField => {
            const fieldKey = displayField.key
            defaultRuleInputs[fieldKey] = this.rule.inputs[fieldKey] || this.selectedRuleType.defaultValue[fieldKey]
          })
          this.rule.inputs = defaultRuleInputs
        }
      },
      deep: true,
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.rule = cloneDeep(this.value)
    },
    onRuleTypeChange() {
      this.rule.inputs = cloneDeep(this.selectedRuleType.defaultValue)
    },
    onDropdownOpen() {
      this.$nextTick(() => {
        this.$emit('dropdownOpen')
      })
    },

    // Scrolls the dropdown menu to bring the selected item into view.
    handleDropdownOpen() {
      this.$nextTick(() => {
        this.$emit('dropdownOpen')
        const dropdownMenu = this.$refs.vSelect.$el.querySelector('.vs__dropdown-menu')
        if (!dropdownMenu) return // Ensure the dropdown exists before proceeding

        const selectedIndex = this.ruleTypeOptions.findIndex(option => option.value === this.rule.type)

        if (selectedIndex >= 0) {
          const itemHeight = dropdownMenu.scrollHeight / this.ruleTypeOptions.length
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenu.scrollTop = scrollPosition
        }
      })
    },
    matchesCondition(condition, data) {
      if (!condition) {
        // Display field if no condition set
        return true
      }

      const fieldValue = data[condition.field] || null
      const givenValue = condition.value

      let result
      if (condition.operator === 'equalTo') {
        result = fieldValue === givenValue
      } else if (condition.operator === 'notEqualTo') {
        result = fieldValue !== givenValue
      } else if (condition.operator === 'inList') {
        result = givenValue.includes(fieldValue)
      } else if (condition.operator === 'notInList') {
        result = !givenValue.includes(fieldValue)
      } else {
        // Do not display field for un-supported operators
        result = false
      }
      return result
    },
    filterIntegers(key, event) {
      this.rule.inputs[key] = event
      setTimeout(() => {
        // eslint-disable-next-line no-useless-escape
        this.rule.inputs[key] = event.replace(/[^0-9]+/g, '')
        // eslint-disable-next-line no-floating-decimal
      }, .00001)
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
