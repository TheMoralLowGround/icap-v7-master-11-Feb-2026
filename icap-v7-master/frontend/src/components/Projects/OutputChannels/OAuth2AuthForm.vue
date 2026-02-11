<template>
  <div>
    <h5 class="mb-1">
      OAuth2 Authentication
    </h5>
    <BRow>
      <BCol md="6">
        <validation-provider
          #default="{ errors }"
          name="Client ID"
          vid="client_id"
          mode="eager"
          :rules="getFieldRules('client_id')"
        >
          <BFormGroup
            label="Client ID"
            label-for="client-id"
            :state="getFieldState(errors)"
          >
            <BFormInput
              id="client-id"
              :value="formData.client_id"
              type="text"
              placeholder="Enter client ID"
              :state="getFieldState(errors)"
              :disabled="disabled"
              @input="updateField('client_id', $event)"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </BFormGroup>
        </validation-provider>
      </BCol>
      <BCol md="6">
        <validation-provider
          #default="{ errors }"
          name="Client Secret"
          vid="client_secret"
          mode="eager"
          :rules="getFieldRules('client_secret')"
        >
          <BFormGroup
            label="Client Secret"
            label-for="client-secret"
            :state="getFieldState(errors)"
          >
            <BInputGroup class="input-group-merge">
              <BFormInput
                id="client-secret"
                :value="formData.client_secret"
                :type="fieldType"
                placeholder="Enter client secret"
                :state="getFieldState(errors)"
                :disabled="disabled"
                @input="updateField('client_secret', $event)"
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
    <TokenUrlField
      :form-data="formData"
      :disabled="disabled"
      :validation-rules="validationRules"
      @update-field="updateField"
    />
    <!-- Advanced Settings Accordion -->
    <div class="mt-3">
      <h5
        class="cursor-pointer mb-1"
        @click="showAdvancedSettings = !showAdvancedSettings"
      >
        Advanced Settings
        <feather-icon
          :icon="showAdvancedSettings ? 'ChevronDownIcon' : 'ChevronUpIcon'"
          size="16"
          class="ms-1"
        />
      </h5>
      <BCollapse
        v-model="showAdvancedSettings"
        class="mt-2"
      >
        <BRow>
          <BCol md="6">
            <BFormGroup
              label="Scope"
              label-for="scope"
            >
              <BFormInput
                id="scope"
                :value="formData.scope"
                type="text"
                placeholder="Enter scope"
                :disabled="disabled"
                @input="updateField('scope', $event)"
              />
            </BFormGroup>
          </BCol>
          <BCol md="6">
            <BFormGroup
              label="Grant Type"
              label-for="grant_type"
            >
              <v-select
                id="grant_type"
                v-model="grantTypeValue"
                :options="grantTypeOptions"
                label="label"
                :reduce="option => option.value"
                :disabled="disabled"
              />
            </BFormGroup>
          </BCol>
        </BRow>
        <!-- Username and Password fields for password grant type -->
        <BRow v-if="formData.grant_type === 'password'">
          <BCol md="6">
            <BFormGroup
              label="Username"
              label-for="username"
            >
              <BFormInput
                id="username"
                :value="formData.username"
                type="text"
                placeholder="Enter username"
                :disabled="disabled"
                @input="updateField('username', $event)"
              />
            </BFormGroup>
          </BCol>
          <BCol md="6">
            <BFormGroup
              label="Password"
              label-for="password"
            >
              <BInputGroup class="input-group-merge">
                <BFormInput
                  id="password"
                  :value="formData.password"
                  :type="grantPasswordFieldType"
                  placeholder="Enter password"
                  :disabled="disabled"
                  @input="updateField('password', $event)"
                />
                <BInputGroupAppend is-text>
                  <feather-icon
                    class="cursor-pointer"
                    :class="disabled ? 'text-muted' : ''"
                    :icon="grantPasswordFieldType === 'password' ? 'EyeIcon' : 'EyeOffIcon'"
                    :style="disabled ? 'pointer-events: none;' : ''"
                    @click="!disabled && toggleGrantPasswordVisibility()"
                  />
                </BInputGroupAppend>
              </BInputGroup>
            </BFormGroup>
          </BCol>
        </BRow>
      </BCollapse>
    </div>
  </div>
</template>

<script>
import {
  BCol,
  BCollapse,
  BFormGroup,
  BFormInput,
  BInputGroup,
  BInputGroupAppend,
  BRow,
} from 'bootstrap-vue'
import { ValidationProvider } from 'vee-validate'
import vSelect from 'vue-select'
import TokenUrlField from './TokenUrlField.vue'

export default {
  name: 'OAuth2AuthForm',
  components: {
    BCol,
    BCollapse,
    BFormGroup,
    BFormInput,
    BInputGroup,
    BInputGroupAppend,
    BRow,
    ValidationProvider,
    vSelect,
    TokenUrlField,
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
      grantPasswordFieldType: 'password',
      showAdvancedSettings: false,
      grantTypeOptions: [
        { label: 'Client Credentials', value: 'client_credentials' },
        { label: 'Password', value: 'password' },
      ],
    }
  },
  computed: {
    grantTypeValue: {
      get() {
        return this.formData.grant_type || 'client_credentials'
      },
      set(value) {
        this.updateField('grant_type', value)
        // Clear username and password when switching away from 'password' grant type
        if (value !== 'password') {
          this.updateField('username', '')
          this.updateField('password', '')
        }
      },
    },
  },
  mounted() {
    // Set default grant_type if not already set
    if (!this.formData.grant_type) {
      this.updateField('grant_type', 'client_credentials')
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
    toggleGrantPasswordVisibility() {
      this.grantPasswordFieldType = this.grantPasswordFieldType === 'password' ? 'text' : 'password'
    },
  },
}
</script>
