<template>
  <b-input-group style="flex-wrap: nowrap;">
    <b-input-group-append style="flex-basis:110px;">
      <v-select
        v-model="inputData.type"
        label="label"
        :options="types"
        :reduce="option => option.value"
        :clearable="false"
        class="flex-grow-1"
        @open="$emit('dropdownOpen')"
      />
    </b-input-group-append>
    <validation-provider
      #default="{ errors }"
      :name="placeholder"
      :rules="validationRules"
      :vid="validationId"
      class="flex-grow-1"
    >
      <form-input
        v-model="inputData.value"
        type="text"
        :placeholder="placeholder"
        :state="errors.length > 0 ? false:null"
      />
      <small class="text-danger">{{ errors[0] }}</small>
    </validation-provider>
  </b-input-group>
</template>

<script>
import { BInputGroup, BInputGroupAppend } from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'

import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import FormInput from './FormInput.vue'

const defalutValue = {
  type: 'string',
  value: null,
}

export default {
  components: {
    FormInput,
    BInputGroup,
    BInputGroupAppend,
    vSelect,
    ValidationProvider,
  },
  props: {
    value: {
      type: Object,
      required: false,
      default() {
        return null
      },
    },
    placeholder: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    validationId: {
      type: String,
      required: true,
    },
    validationRules: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      inputData: defalutValue,
      types: [
        {
          value: 'string',
          label: 'String',
        },
        {
          value: 'shape',
          label: 'Shape',
        },
        {
          value: 'regex',
          label: 'Regex',
        },
      ],
    }
  },
  computed: {
    out() {
      return cloneDeep(this.inputData)
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
      if (this.value !== null) {
        this.inputData = cloneDeep(this.value)
      } else {
        this.inputData = cloneDeep(defalutValue)
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
