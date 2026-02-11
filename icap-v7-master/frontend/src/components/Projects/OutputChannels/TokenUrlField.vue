<template>
  <validation-provider
    #default="{ errors }"
    name="Token URL"
    vid="token_url"
    mode="eager"
    :rules="getFieldRules('token_url')"
  >
    <BFormGroup
      label="Token URL"
      label-for="token-url"
      :state="getFieldState(errors)"
    >
      <BFormInput
        id="token-url"
        :value="formData.token_url"
        type="text"
        placeholder="https://api.example.com/oauth2/token"
        :state="getFieldState(errors)"
        :disabled="disabled"
        @input="updateField('token_url', $event)"
      />
      <small class="text-danger">{{ errors[0] }}</small>
    </BFormGroup>
  </validation-provider>
</template>

<script>
import {
  BFormGroup,
  BFormInput,
} from 'bootstrap-vue'
import { ValidationProvider } from 'vee-validate'

export default {
  name: 'TokenUrlField',
  components: {
    BFormGroup,
    BFormInput,
    ValidationProvider,
  },
  props: {
    formData: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    validationRules: {
      type: Function,
      required: true,
    },
  },
  methods: {
    getFieldState(errors) {
      return errors.length > 0 ? false : null
    },
    getFieldRules(fieldName) {
      return this.validationRules(fieldName)
    },
    updateField(fieldName, value) {
      this.$emit('update-field', fieldName, value)
    },
  },
}
</script>
