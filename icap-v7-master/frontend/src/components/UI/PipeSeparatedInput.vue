<template>
  <div class="d-flex">
    <div :class="`w-${width}`">
      <b-form-group
        :label="!hideFormGroupLabel ? label : null"
        class="mb-0"
      >
        <validation-provider
          #default="{ errors }"
          :name="label"
          :rules="mainFieldValidationRules"
          :vid="`${validationKey}`"
        >
          <div class="d-flex align-items-center">
            <component
              :is="listenableInput ? 'form-input' : 'b-form-input' "
              v-model="inputText"
              type="text"
              class="bg-transparent"
              :readonly="readonly"
              :placeholder="label"
              :selection-value-attr="selectionValueAttr"
              :state="errors.length > 0 ? false:null"
              @selection-input="selectionInputHandler(-1, $event)"
              @focus="$emit('focus', -1)"
              @click="$emit('click', -1)"
            />

            <div>
              <feather-icon
                v-if="expanded === false"
                icon="ChevronUpIcon"
                class="cursor-pointer mx-50"
                size="20"
                @click="expanded = true"
              />
              <feather-icon
                v-if="expanded === true"
                icon="ChevronDownIcon"
                class="cursor-pointer mx-50"
                size="20"
                @click="expanded = false"
              />
            </div>
          </div>
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>

      </b-form-group>

      <div
        v-show="expanded"
        class="scrollable-content"
      >
        <validation-provider
          v-for="(item, index) of items"
          #default="{ errors }"
          :key="index"
          tag="div"
          :name="label"
          :rules="additionalFieldValidationRules[index]"
          :vid="`${validationKey}_${index}`"
          class="mb-50"
        >
          <div class="d-flex align-items-center">
            <component
              :is="listenableInput ? 'form-input' : 'b-form-input' "
              v-model="items[index]"
              type="text"
              :readonly="readonly"
              :state="errors.length > 0 ? false:null"
              :selection-value-attr="selectionValueAttr"
              class="bg-transparent"
              @selection-input="selectionInputHandler(index, $event)"
              @focus="$emit('focus', index)"
              @click="$emit('click', index)"
            />
            <div>
              <feather-icon
                icon="Trash2Icon"
                class="cursor-pointer mx-50"
                size="20"
                @click="deleteItem(index)"
              />
            </div>
          </div>
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>

        <div
          v-if="!inlineAddButton"
          class="mr-50"
        >
          <add-item
            :label="label"
            @add="additems"
          />
        </div>
      </div>
    </div>

    <div
      v-if="inlineAddButton"
      :style="{
        'padding-bottom': expanded ? items.length ? '0.7rem' : '0.35rem' : '0'
      }"
      class="w-25 align-self-end ml-1"
    >
      <add-item
        :label="label"
        no-input-box
        @add="additems"
      />
    </div>
  </div>
</template>

<script>
import {
  BFormGroup, BFormInput,
} from 'bootstrap-vue'
import { ValidationProvider } from 'vee-validate'
import AddItem from './AddItem.vue'
import FormInput from './FormInput.vue'

export default {
  components: {
    BFormGroup,
    AddItem,
    FormInput,
    BFormInput,
    ValidationProvider,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    isKeyMissing: {
      type: Boolean,
      default: () => false,
    },
    value: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    width: {
      type: Number,
      required: false,
      default() {
        return 0
      },
    },
    hideFormGroupLabel: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    selectionValueAttr: {
      type: String,
      required: false,
      default() {
        return 'text'
      },
    },
    listenableInput: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    validationKey: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    initializeExpanded: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    readonly: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    inlineAddButton: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
  },
  data() {
    return {
      items: [],
      selectionStatus: [],
      expanded: false,
    }
  },
  computed: {
    inputText: {
      get() {
        return this.items.join('|')
      },
      set(value) {
        this.items = value ? value.split('|') : []
      },
    },
    out() {
      return this.inputText
    },
    mainFieldValidationRules() {
      let { validationRules } = this

      if (validationRules.includes('selectTextFromImage')) {
        let updatedRule
        if (this.items.length <= 1) {
          updatedRule = `selectTextFromImage:${this.selectionStatus[0]}`
        } else {
          updatedRule = ''
        }
        validationRules = validationRules.replace('selectTextFromImage', updatedRule)
      }

      return validationRules
    },
    additionalFieldValidationRules() {
      const { validationRules } = this
      const items = this.items.map((item, index) => {
        let newValidationRules = validationRules
        if (validationRules.includes('selectTextFromImage')) {
          const rule = `selectTextFromImage:${this.selectionStatus[index]}`
          newValidationRules = newValidationRules.replace('selectTextFromImage', rule)
        }
        return newValidationRules
      })
      return items
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
    this.expanded = this.initializeExpanded
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.items = this.value ? this.value.split('|') : []
      this.selectionStatus = this.items.map(() => true)
    },
    additems(count) {
      if (this.inlineAddButton && !this.expanded) {
        this.expanded = true
      }

      const items = []
      for (let i = 0; i < count; i += 1) {
        const item = null
        items.push(item)
      }
      this.items = this.items.concat(items)
    },
    deleteItem(index) {
      this.items.splice(index, 1)
      this.selectionStatus.splice(index, 1)

      this.$emit('item-deleted', index)
    },
    selectionInputHandler(index, data) {
      this.selectionStatus[index === -1 ? 0 : index] = true

      this.$emit('selection-input', {
        index,
        selectionData: data,
        totalItems: this.items.length,
      })
    },
  },
}
</script>

<style scoped>
.scrollable-content {
    max-height: 300px;
    overflow-y: auto;
    padding: 3px;
}

</style>
