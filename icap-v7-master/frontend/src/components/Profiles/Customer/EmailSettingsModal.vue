<template>
  <b-modal
    :visible="value"
    :title="`Email Settings - ${title || 'Customer'}`"
    size="xl"
    centered
    no-close-on-backdrop
    ok-title="Save"
    @ok="handleSave"
    @hidden="close"
  >
    <b-row>
      <b-col cols="12">
        <hr>
        <h5>Email Notification Settings</h5>
        <p>Note: Email notifications will be always sent, following additional settings will be respected if provided.</p>
      </b-col>

      <b-col cols="6">
        <b-card border-variant="success">
          <h6>Success Notification Settings</h6>

          <b-col cols="12">
            <b-form-group
              label="Notify With Source Email Subject"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.success_notification_with_same_subject"
                switch
                class="mt-50"
                @input="onSuccessNotificationWithSameSubjectInput"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <validation-provider
              #default="{ errors }"
              name="Notification Email Subject"
              vid="success_notification_subject"
              mode="eager"
              :rules="formData.success_notification_with_same_subject ? '' : 'required'"
            >
              <b-form-group
                label="Notification Email Subject"
                label-cols-md="3"
                label-cols-lg="3"
              >
                <b-form-input
                  v-model="formData.success_notification_subject"
                  :disabled="formData.success_notification_with_same_subject"
                  :state="errors.length > 0 ? false:null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>

          <b-col cols="12">
            <b-form-group
              label="Notify Email Sender"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.success_notify_email_sender"
                switch
                class="mt-50"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <b-form-group
              label="Notify Email Recipients"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.success_notify_email_recipients"
                switch
                class="mt-50"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <b-form-group
              label="Notify CC Users"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.success_notify_cc_users"
                switch
                class="mt-50"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <validation-provider
              #default="{ errors }"
              name="Notify Additional Emails"
              vid="success_notify_additional_emails"
              mode="eager"
            >
              <b-form-group
                label="Notify Additional Emails"
                label-cols-md="3"
                label-cols-lg="3"
              >
                <b-form-input
                  v-model="formData.success_notify_additional_emails"
                  :state="errors.length > 0 ? false:null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>
        </b-card>
      </b-col>

      <b-col cols="6">
        <b-card border-variant="danger">
          <h6>Failure Notification Settings</h6>

          <b-col cols="12">
            <b-form-group
              label="Notify With Source Email Subject"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.failure_notification_with_same_subject"
                switch
                class="mt-50"
                @input="onFailureNotificationWithSameSubjectInput"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <validation-provider
              #default="{ errors }"
              name="Notification Email Subject"
              vid="failure_notification_subject"
              mode="eager"
              :rules="formData.failure_notification_with_same_subject ? '' : 'required'"
            >
              <b-form-group
                label="Notification Email Subject"
                label-cols-md="3"
                label-cols-lg="3"
              >
                <b-form-input
                  v-model="formData.failure_notification_subject"
                  :disabled="formData.failure_notification_with_same_subject"
                  :state="errors.length > 0 ? false:null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>

          <b-col cols="12">
            <b-form-group
              label="Notify Email Sender"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.failure_notify_email_sender"
                switch
                class="mt-50"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <b-form-group
              label="Notify Email Recipients"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.failure_notify_email_recipients"
                switch
                class="mt-50"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <b-form-group
              label="Notify CC Users"
              label-cols-md="3"
              label-cols-lg="3"
            >
              <b-form-checkbox
                v-model="formData.failure_notify_cc_users"
                switch
                class="mt-50"
              />
            </b-form-group>
          </b-col>

          <b-col cols="12">
            <validation-provider
              #default="{ errors }"
              name="Notify Additional Emails"
              vid="failure_notify_additional_emails"
              mode="eager"
            >
              <b-form-group
                label="Notify Additional Emails"
                label-cols-md="3"
                label-cols-lg="3"
              >
                <b-form-input
                  v-model="formData.failure_notify_additional_emails"
                  :state="errors.length > 0 ? false:null"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
            </validation-provider>
          </b-col>
        </b-card>
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
import { ValidationProvider } from 'vee-validate'
import {
  BCol, BRow, BFormGroup, BFormInput, BCard,
  BFormCheckbox,
} from 'bootstrap-vue'

export default {
  components: {
    ValidationProvider,
    BRow,
    BCol,
    BFormGroup,
    BFormInput,
    BCard,
    BFormCheckbox,
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    currentCustomer: {
      type: Object,
      required: true,
      default: () => ({
        name: '',
        success_notification_with_same_subject: false,
        success_notification_subject: '',
        success_notify_email_sender: false,
        success_notify_email_recipients: false,
        success_notify_cc_users: false,
        success_notify_additional_emails: '',
        failure_notification_with_same_subject: false,
        failure_notification_subject: '',
        failure_notify_email_sender: false,
        failure_notify_email_recipients: false,
        failure_notify_cc_users: false,
        failure_notify_additional_emails: '',
      }),
    },
    errorMessage: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      formData: { ...this.getInitialFormData() },
    }
  },
  computed: {
    title() {
      return this.currentCustomer?.name
    },
  },
  watch: {
    currentCustomer: {
      handler(newVal) {
        this.formData = { ...this.getInitialFormData(newVal) }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    getInitialFormData(customer = null) {
      const source = customer || this.currentCustomer
      return {
        success_notification_with_same_subject: source?.success_notification_with_same_subject || false,
        success_notification_subject: source?.success_notification_subject || '',
        success_notify_email_sender: source?.success_notify_email_sender || false,
        success_notify_email_recipients: source?.success_notify_email_recipients || false,
        success_notify_cc_users: source?.success_notify_cc_users || false,
        success_notify_additional_emails: source?.success_notify_additional_emails || '',
        failure_notification_with_same_subject: source?.failure_notification_with_same_subject || false,
        failure_notification_subject: source?.failure_notification_subject || '',
        failure_notify_email_sender: source?.failure_notify_email_sender || false,
        failure_notify_email_recipients: source?.failure_notify_email_recipients || false,
        failure_notify_cc_users: source?.failure_notify_cc_users || false,
        failure_notify_additional_emails: source?.failure_notify_additional_emails || '',
      }
    },
    handleSave() {
      this.$emit('submit', this.formData)
    },
    close() {
      this.$emit('close')
      this.resetForm()
    },
    resetForm() {
      this.formData = { ...this.getInitialFormData() }
    },
    onSuccessNotificationWithSameSubjectInput(value) {
      if (value) {
        this.formData.success_notification_subject = ''
      }
    },
    onFailureNotificationWithSameSubjectInput(value) {
      if (value) {
        this.formData.failure_notification_subject = ''
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
