<template>
  <div>
    <h5 class="mb-1">
      Basic Authentication
    </h5>
    <BRow>
      <BCol md="6">
        <validation-provider
          #default="{ errors }"
          name="Username"
          vid="username"
          mode="eager"
          :rules="getFieldRules('username')"
        >
          <BFormGroup
            label="Username"
            label-for="username"
            :state="getFieldState(errors)"
          >
            <BFormInput
              id="username"
              :value="formData.username"
              type="text"
              placeholder="Enter username"
              :state="getFieldState(errors)"
              :disabled="disabled"
              @input="updateField('username', $event)"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </BFormGroup>
        </validation-provider>
      </BCol>
      <BCol md="6">
        <validation-provider
          #default="{ errors }"
          name="Password"
          vid="password"
          mode="eager"
          :rules="getFieldRules('password')"
        >
          <BFormGroup
            label="Password"
            label-for="password"
            :state="getFieldState(errors)"
          >
            <BInputGroup class="input-group-merge">
              <BFormInput
                id="password"
                :value="formData.password"
                :type="fieldType"
                placeholder="Enter password"
                :state="getFieldState(errors)"
                :disabled="disabled"
                @input="updateField('password', $event)"
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
  name: 'BasicAuthForm',
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
