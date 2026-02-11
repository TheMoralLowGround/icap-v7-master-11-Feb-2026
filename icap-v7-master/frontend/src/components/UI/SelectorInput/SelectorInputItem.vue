<template>
  <validation-provider
    #default="{ errors }"
    :name="label"
    rules="required"
    :vid="validationKey"
  >
    <b-input-group
      class="input-group-merge bg-transparent"
      :class="[errors.length > 0 ? 'is-invalid':null]"
    >
      <template #append>
        <b-input-group-text
          class="py-0 my-0 bg-transparent"
        >
          <span>
            <feather-icon
              v-if="selectorPosition === null"
              v-b-tooltip.hover
              icon="InfoIcon"
              size="15"
              title="Select area over image to capture value"
            />

            <feather-icon
              v-if="selectorPosition !== null"
              v-b-tooltip.hover
              icon="CrosshairIcon"
              size="15"
              class="cursor-pointer"
              :title="captured ? 'Captured!' : 'Capture'"
              @click="capture()"
            />
          </span>
        </b-input-group-text>
      </template>
      <b-form-input
        v-model="displayValue"
        :state="errors.length > 0 ? false:null"
        disabled
      />
    </b-input-group>
    <small class="text-danger">{{ errors[0] }}</small>
  </validation-provider>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import {
  VBTooltip, BFormInput, BInputGroup, BInputGroupText,
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
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    validationKey: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      inputItem: {},
      captured: false,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.inputItem)
    },
    displayValue() {
      if (!this.inputItem.startPos) {
        return null
      }

      // const startPos = Number(this.inputItem.startPos).toFixed(0)
      // const topPos = Number(this.inputItem.topPos).toFixed(0)
      // const endPos = Number(this.inputItem.endPos).toFixed(0)
      // const bottomPos = Number(this.inputItem.bottomPos).toFixed(0)
      // const { pageId, pageIndex  } = this.inputItem
      const { selectedText } = this.inputItem
      return selectedText || ''
    },
    selectorPosition() {
      return this.$store.getters['batch/selectorPosition']
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
    setInternalState() {
      this.inputItem = cloneDeep(this.value)
    },
    capture() {
      this.inputItem = this.selectorPosition
      this.captured = true

      setTimeout(() => {
        this.captured = false
      }, 1000)
    },
  },
}
</script>
