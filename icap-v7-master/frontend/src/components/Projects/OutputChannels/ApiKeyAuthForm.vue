<template>
  <div>
    <h5 class="mb-1">
      API Key Authentication
    </h5>
    <BRow>
      <BCol md="6">
        <validation-provider
          #default="{ errors }"
          name="API Key Name"
          vid="api_key_name"
          mode="eager"
          :rules="getFieldRules('api_key_name')"
        >
          <BFormGroup
            label="API Key Name"
            label-for="api-key-name"
            :state="getFieldState(errors)"
          >
            <BFormInput
              id="api-key-name"
              :value="formData.api_key_name"
              type="text"
              placeholder="X-API-Key"
              :state="getFieldState(errors)"
              :disabled="disabled"
              @input="updateField('api_key_name', $event)"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </BFormGroup>
        </validation-provider>
      </BCol>
      <BCol md="6">
        <validation-provider
          #default="{ errors }"
          name="API Key Value"
          vid="api_key_value"
          mode="eager"
          :rules="getFieldRules('api_key_value')"
        >
          <BFormGroup
            label="API Key Value"
            label-for="api-key-value"
            :state="getFieldState(errors)"
          >
            <BInputGroup class="input-group-merge">
              <BFormInput
                id="api-key-value"
                :value="formData.api_key_value"
                :type="fieldType"
                placeholder="Enter API key value"
                :state="getFieldState(errors)"
                :disabled="disabled"
                @input="updateField('api_key_value', $event)"
              />
              <BInputGroupAppend is-text>
                <feather-icon
                  class="cursor-pointer"
                  :class="disabled ? 'text-muted' : ''"
                  :icon="fieldType === 'password' ? 'EyeIcon' : 'EyeOffIcon'"
                  :style="disabled ? 'pointer-events: none;' : ''"
                  @click="!disabled && toggleVisibility()"
                />
              </BInputGroupAppend>
            </BInputGroup>
            <small class="text-danger">{{ errors[0] }}</small>
          </BFormGroup>
        </validation-provider>
      </BCol>
    </BRow>
  </div>
</template>

<script>
import {
  BCol,
  BFormGroup,
  BFormInput,
  BInputGroup,
  BInputGroupAppend,
  BRow,
} from 'bootstrap-vue'
import { ValidationProvider } from 'vee-validate'

export default {
  name: 'ApiKeyAuthForm',
  components: {
    BCol,
    BFormGroup,
    BFormInput,
    BInputGroup,
    BInputGroupAppend,
    BRow,
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
  data() {
    return {
      fieldType: 'password',
    }
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
    toggleVisibility() {
      this.fieldType = this.fieldType === 'password' ? 'text' : 'password'
    },
  },
}
</script>
