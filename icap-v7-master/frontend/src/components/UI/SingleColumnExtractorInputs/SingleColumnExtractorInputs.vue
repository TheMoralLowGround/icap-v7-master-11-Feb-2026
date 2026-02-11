<template>
  <div>
    <div
      class="d-flex align-items-center"
    >
      <div class="flex-grow-1">
        <validation-provider
          #default="{ errors }"
          name="tableStart"
          rules="required"
          :vid="`${validationKey}-tableStart`"
        >
          <form-input
            v-model="item.tableStart"
            :state="errors.length > 0 ? false:null"
            placeholder="tableStart"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>
      </div>

      <div>
        <feather-icon
          v-if="!expanded"
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
    <div
      v-show="expanded"
    >
      <div
        class="d-flex flex-column"
        style="row-gap:0.25rem;margin-top:0.25rem;"
      >
        <validation-provider
          #default="{ errors }"
          name="tableEnd"
          rules="required"
          :vid="`${validationKey}-tableEnd`"
        >
          <form-input
            v-model="item.tableEnd"
            :state="errors.length > 0 ? false:null"
            placeholder="tableEnd"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>

        <capture-text-input-item
          v-model="item.startPos"
          :validation-key="`${validationKey}-startPos`"
          label="startPos"
          type="startPos"
          placeholder="startPos"
        />

        <capture-text-input-item
          v-model="item.endPos"
          :validation-key="`${validationKey}-endPos`"
          label="endPos"
          type="endPos"
          placeholder="endPos"
        />

        <validation-provider
          #default="{ errors }"
          name="shape"
          rules=""
          :vid="`${validationKey}-shape`"
        >
          <form-input
            v-model="item.shape"
            :state="errors.length > 0 ? false:null"
            placeholder="shape"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>
      </div>
    </div>
  </div>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'

import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'
import FormInput from '../FormInput.vue'
import CaptureTextInputItem from '../CaptureTextInput/CaptureTextInputItem.vue'

export default {
  components: {
    FormInput,
    ValidationProvider,
    CaptureTextInputItem,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    validationKey: {
      type: String,
      required: true,
    },
    initializeExpanded: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
  },
  data() {
    return {
      item: {
        tableStart: null,
        tableEnd: null,
        startPos: null,
        endPos: null,
        shape: null,
      },
      expanded: false,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.item)
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
    this.expanded = this.initializeExpanded
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.item = cloneDeep(this.value)
    },
  },
}
</script>
