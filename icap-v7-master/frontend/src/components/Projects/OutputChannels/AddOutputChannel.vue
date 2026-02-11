<template>
  <BModal
    :visible="modelValue"
    :title="mode === 'edit' ? 'Edit Output Channel' : 'Add New Output Channel'"
    size="lg"
    centered
    no-close-on-backdrop
    @hide="close"
  >
    <validation-observer ref="channelForm">
      <BForm @submit.prevent="handleSubmit">
        <BRow>
          <!-- Channel Title -->
          <BCol cols="12">
            <validation-provider
              #default="{ errors }"
              name="Channel Title"
              vid="title"
              mode="eager"
              rules="required"
            >
              <BFormGroup
                label="Channel Title"
                label-for="channel-title"
                :state="getFieldState(errors)"
              >
                <BFormInput
                  id="channel-title"
                  v-model="form.title"
                  type="text"
                  placeholder="Enter channel title"
                  :state="getFieldState(errors)"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </BFormGroup>
            </validation-provider>
          </BCol>

          <!-- Channel Description -->
          <BCol cols="12">
            <validation-provider
              #default="{ errors }"
              name="Description"
              vid="description"
              mode="eager"
              rules="required"
            >
              <BFormGroup
                label="Description"
                label-for="channel-description"
                :state="getFieldState(errors)"
              >
                <BFormTextarea
                  id="channel-description"
                  v-model="form.description"
                  placeholder="Enter channel description"
                  rows="3"
                  :state="getFieldState(errors)"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </BFormGroup>
            </validation-provider>
          </BCol>

          <!-- Output Type -->
          <BCol
            cols="12"
            md="6"
          >
            <validation-provider
              #default="{ errors }"
              name="Output Type"
              vid="output_type"
              mode="eager"
              rules="required"
            >
              <BFormGroup
                label="Output Type"
                label-for="output-type"
                :state="getFieldState(errors)"
              >
                <v-select
                  id="output-type"
                  v-model="form.output_type"
                  :reduce="op => op.value"
                  :options="outputTypes"
                  placeholder="Select output type"
                  :state="getFieldState(errors)"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </BFormGroup>
            </validation-provider>
          </BCol>

          <!-- Icon Selection -->
          <BCol
            cols="12"
            md="6"
          >
            <validation-provider
              #default="{ errors }"
              name="Icon"
              vid="icon"
              mode="eager"
              rules="required"
            >
              <BFormGroup
                label="Icon"
                label-for="icon"
                :state="getFieldState(errors)"
              >
                <v-select
                  id="icon"
                  v-model="form.icon"
                  :options="iconOptions"
                  placeholder="Select an icon"
                  :state="getFieldState(errors)"
                >
                  <template #option="{ label }">
                    <div class="d-flex align-items-center">
                      <feather-icon
                        :icon="label"
                        size="16"
                        class="mr-1"
                      />
                      <span>{{ label }}</span>
                    </div>
                  </template>
                  <template #selected-option="{ label }">
                    <div class="d-flex align-items-center">
                      <feather-icon
                        :icon="label"
                        size="16"
                        class="mr-1"
                      />
                      <span>{{ label }}</span>
                    </div>
                  </template>
                </v-select>
                <small class="text-danger">{{ errors[0] }}</small>
              </BFormGroup>
            </validation-provider>
          </BCol>

          <!-- Variant/Color -->
          <BCol
            cols="12"
            md="6"
          >
            <validation-provider
              #default="{ errors }"
              name="Variant"
              vid="variant"
              mode="eager"
              rules="required"
            >
              <BFormGroup
                label="Button Variant"
                label-for="variant"
                :state="getFieldState(errors)"
              >
                <v-select
                  id="variant"
                  v-model="form.variant"
                  :options="variantOptions"
                  :reduce="variantOptions => variantOptions.value"
                  placeholder="Select variant"
                  :state="getFieldState(errors)"
                >
                  <template #option="option">
                    <BBadge :variant="option.value.replace('outline-', '')">
                      {{ option.label }}
                    </BBadge>
                  </template>
                </v-select>
                <small class="text-danger">{{ errors[0] }}</small>
              </BFormGroup>
            </validation-provider>
          </BCol>
        </BRow>
      </BForm>
    </validation-observer>

    <template #modal-footer="{ ok, cancel }">
      <BButton
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </BButton>

      <BButton
        variant="primary"
        :disabled="submitting"
        @click="handleSubmit"
      >
        <span v-if="submitting">{{ mode === 'edit' ? 'Updating...' : 'Adding...' }}</span>
        <span v-else>{{ mode === 'edit' ? 'Update Channel' : 'Add Channel' }}</span>
      </BButton>
    </template>
  </BModal>
</template>

<script>
import {
  BModal,
  BForm,
  BFormGroup,
  BFormInput,
  BFormTextarea,
  BButton,
  BRow,
  BCol,
  BBadge,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import vSelect from 'vue-select'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  name: 'AddOutputChannel',
  components: {
    BModal,
    BForm,
    BFormGroup,
    BFormInput,
    BFormTextarea,
    BButton,
    BRow,
    BCol,
    BBadge,
    ValidationProvider,
    ValidationObserver,
    vSelect,
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    mode: {
      type: String,
      default: 'add',
      validator: value => ['add', 'edit'].includes(value),
    },
    channelData: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      submitting: false,
      defaultFormData: {
        title: '',
        description: '',
        output_type: 'json',
        icon: 'LayersIcon',
        variant: 'outline-primary',
      },
      form: {
        title: '',
        description: '',
        output_type: 'json',
        icon: 'LayersIcon',
        variant: 'outline-primary',
      },
      outputTypes: [
        { label: 'JSON', value: 'json' },
        { label: 'Document', value: 'document' },
        // { label: 'XML', value: 'xml' },
        // { label: 'CSV', value: 'csv' },
        // { label: 'Custom', value: 'custom' },
      ],
      iconOptions: [
        'ServerIcon',
        'FileIcon',
        'DatabaseIcon',
        'CloudIcon',
        'GlobeIcon',
        'LayersIcon',
        'PackageIcon',
        'ShareIcon',
        'SendIcon',
        'UploadCloudIcon',
        'ActivityIcon',
        'ZapIcon',
      ],
      variantOptions: [
        { label: 'Primary', value: 'outline-primary' },
        { label: 'Success', value: 'outline-success' },
        { label: 'Info', value: 'outline-info' },
        { label: 'Warning', value: 'outline-warning' },
        { label: 'Danger', value: 'outline-danger' },
        { label: 'Secondary', value: 'outline-secondary' },
      ],
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal && this.mode === 'edit' && this.channelData) {
        this.loadChannelData()
      } else if (!newVal) {
        this.resetForm()
      }
    },
    channelData: {
      handler(newVal) {
        if (newVal && this.mode === 'edit' && this.modelValue) {
          this.loadChannelData()
        }
      },
      immediate: true,
    },
  },
  methods: {
    getFieldState(errors) {
      return errors.length > 0 ? false : null
    },

    async handleSubmit() {
      try {
        const success = await this.$refs.channelForm.validate()
        if (!success) return

        this.submitting = true

        if (this.mode === 'edit') {
          // Update existing channel
          const updatedChannel = {
            ...this.channelData,
            title: this.form.title,
            description: this.form.description,
            icon: this.form.icon,
            variant: this.form.variant,
            output_type: this.form.output_type || 'json',
          }

          // Emit the updated channel data to parent
          this.$emit('channel-updated', updatedChannel)
        } else {
          // Create new channel (parent will generate ID)
          const newChannel = {
            title: this.form.title,
            description: this.form.description,
            icon: this.form.icon,
            variant: this.form.variant,
            output_type: this.form.output_type || 'json',
          }

          // Emit the new channel data to parent
          this.$emit('channel-added', newChannel)
        }

        // Reset form and close modal
        this.resetForm()
        this.$emit('update:modelValue', false)
      } catch (error) {
        // console.error('Error saving channel:', error)
      } finally {
        this.submitting = false
      }
    },

    loadChannelData() {
      if (!this.channelData) return

      this.form = {
        title: this.channelData.title || '',
        description: this.channelData.description || '',
        output_type: this.channelData.output_type || 'json',
        icon: this.channelData.icon || null,
        variant: this.channelData.variant || null,
      }
    },

    close() {
      this.resetForm()
      this.$emit('update:modelValue', false)
    },

    resetForm() {
      this.form = { ...this.defaultFormData }
      this.submitting = false
      this.$nextTick(() => {
        if (this.$refs.channelForm) {
          this.$refs.channelForm.reset()
        }
      })
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@core/scss/vue/libs/vue-select.scss';

.gap-2 {
  gap: 0.5rem;
}
</style>
