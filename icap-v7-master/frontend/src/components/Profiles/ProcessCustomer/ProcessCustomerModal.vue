<template>
  <b-modal
    :visible="value"
    :title="modalTitle"
    centered
    size="md"
    no-close-on-backdrop
    ok-title="Save"
    @ok="handleSubmit"
    @hidden="close"
  >
    <b-row>
      <b-col cols="12">
        <validation-observer ref="formObserver">
          <b-form @submit.stop.prevent="handleSubmit">
            <b-row>
              <b-col cols="12">
                <b-form-group
                  label="Name"
                  label-for="customerName"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Name"
                    rules="required"
                  >
                    <b-form-input
                      id="customerName"
                      v-model="form.name"
                      placeholder="Enter customer name"
                      :state="errors.length > 0 ? false : null"
                    />
                    <small class="text-danger">
                      {{ errors[0] }}
                    </small>
                  </validation-provider>
                </b-form-group>
              </b-col>
            </b-row>
          </b-form>
        </validation-observer>
      </b-col>
    </b-row>

    <div
      v-if="errorMessage"
      class="my-4 px-4 py-2 bg-light-danger text-danger rounded"
    >
      {{ errorMessage }}
    </div>
  </b-modal>
</template>

<script>
import {
  BCol, BRow, BForm, BFormGroup, BFormInput,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    BRow,
    BCol,
    BForm,
    BFormGroup,
    BFormInput,
    ValidationProvider,
    ValidationObserver,
  },
  props: {
    value: { type: Boolean, default: false },
    errorMessage: { type: String, default: '' },
    editingItem: { type: Object, default: null },
    editingId: { type: [String, Number], default: null },
  },
  data() {
    return {
      form: {
        name: '',
      },
    }
  },
  computed: {
    modalTitle() {
      return this.editingItem ? 'Edit Customer' : 'Add Customer'
    },
  },
  watch: {
    editingItem: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.form = {
            name: newVal.name || '',
          }
        } else {
          this.resetForm()
        }
      },
    },
  },
  methods: {
    close() {
      this.$emit('close')
      this.resetForm()
    },
    async handleSubmit(bvModalEvt) {
      // Prevent modal from closing
      bvModalEvt.preventDefault()

      // Validate all fields using vee-validate
      const isValid = await this.$refs.formObserver.validate()

      if (!isValid) {
        return
      }

      // Prepare data before resetting
      const customerData = {
        name: this.form.name.trim(),
        ...(this.editingItem && { id: this.editingItem.id }),
      }

      // Reset form if adding new
      if (!this.editingItem) this.resetForm()

      // Clear validation errors
      this.$refs.formObserver.reset()

      // Emit submit event
      this.$emit('submit', customerData)
    },
    resetForm() {
      this.form = {
        name: '',
      }
    },
  },
}
</script>

<style scoped>
.bg-light-danger {
  background-color: rgba(220, 53, 69, 0.1);
}
</style>
