<template>
  <b-modal
    :visible="value"
    :title="isEdit ? 'Edit Party' : 'Add New Party'"
    size="lg"
    centered
    no-close-on-backdrop
    ok-title="Save"
    @ok="handleSubmit"
    @hidden="close"
  >
    <b-form @submit.stop.prevent="handleSubmit">
      <!-- Customer Name -->
      <b-form-group
        label="Name"
        label-for="name"
        :invalid-feedback="nameFeedback"
        :state="nameState"
      >
        <b-form-input
          id="name"
          v-model="form.name"
          :state="nameState"
          required
          @input="submitted = false"
        />
      </b-form-group>
      <b-form-group
        label="Organization Name"
        label-for="org_name"
      >
        <b-form-input
          id="org_name"
          v-model="form.org_name"
        />
      </b-form-group>

      <!-- Account Number -->
      <b-form-group
        label="Account Number"
        label-for="account-number"
        :invalid-feedback="accountNumberFeedback"
        :state="accountNumberState"
      >
        <b-form-input
          id="account-number"
          v-model="form.account_number"
          :state="accountNumberState"
          required
        />
      </b-form-group>

      <!-- Address -->
      <b-form-group
        label="Address Line1"
        label-for="address"
        :invalid-feedback="addressFeedback"
        :state="addressState"
      >
        <b-form-input
          id="address_line1"
          v-model="form.address_line1"
          :state="addressState"
          required
        />
      </b-form-group>
      <b-form-group
        label="Address Line2"
        label-for="address"
      >
        <b-form-input
          id="address_line2"
          v-model="form.address_line2"
        />
      </b-form-group>
      <b-form-group
        label="City"
        label-for="city"
      >
        <b-form-input
          id="city"
          v-model="form.city"
        />
      </b-form-group>
      <b-form-group
        label="Postal Code"
        label-for="postal_code"
      >
        <b-form-input
          id="postal_code"
          v-model="form.postal_code"
        />
      </b-form-group>
      <!-- <b-form-group
        label="Email"
        label-for="email"
      >
        <b-form-input
          id="email"
          v-model="form.email"
        />
      </b-form-group> -->
      <b-form-group
        label="Phone"
        label-for="phone"
      >
        <b-form-input
          id="phone"
          v-model="form.phone"
        />
      </b-form-group>
    </b-form>
  </b-modal>
</template>

<script>
import { cloneDeep } from 'lodash'
import {
  BForm,
  BFormGroup,
  BFormInput,
  BModal,
} from 'bootstrap-vue'

export default {
  components: {
    BForm,
    BFormGroup,
    BFormInput,
    BModal,
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    isEdit: {
      type: Boolean,
      default: false,
    },
    party: {
      type: Object,
      default: () => ({}),
    },
    items: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      form: {},
      submitted: false,
    }
  },
  computed: {
    nameState() {
      if (!this.submitted) return null

      if (!this.form.name) return false

      const isDuplicate = this.items.some(item => {
        if (this.isEdit && item.address_id === this.form.address_id) return false
        return item.name?.trim().toLowerCase() === this.form.name?.trim().toLowerCase()
      })

      return !isDuplicate
    },
    nameFeedback() {
      if (!this.submitted) return ''

      if (!this.form.name?.trim()) {
        return 'Party name is required'
      }

      if (this.nameState === false) {
        return 'This party name already exists'
      }

      return ''
    },
    accountNumberState() {
      return this.submitted ? !!this.form.account_number : null
    },
    accountNumberFeedback() {
      return this.submitted && !this.form.account_number ? 'Account number is required' : ''
    },
    addressState() {
      return this.submitted ? !!this.form.address_line1 : null
    },
    addressFeedback() {
      return this.submitted && !this.form.address_line1 ? 'Address is required' : ''
    },
  },
  watch: {
    party: {
      handler(newParty) {
        this.form = cloneDeep(newParty || {
          name: '',
          org_name: '',
          account_number: '',
          address_line1: '',
          address_line2: '',
          city: '',
          postal_code: '',
          // email: '',
          phone: '',
          address_id: '', // Expect address_id to be provided
        })
      },
      immediate: true,
      deep: true,
    },
  },
  methods: {
    handleSubmit(bvModalEvt) {
      bvModalEvt.preventDefault()
      this.submitted = true

      if (!this.form.name || !this.form.account_number || !this.form.address_line1 || !this.form.address_id) {
        return
      }

      if (this.nameState === false || this.accountNumberState === false || this.addressState === false) {
        return
      }

      const customerData = {
        ...this.form,
        success_notification_with_same_subject: this.form.success_notification_with_same_subject || false,
        success_notification_subject: this.form.success_notification_subject || '',
        success_notify_email_sender: this.form.success_notify_email_sender || false,
        success_notify_email_recipients: this.form.success_notify_email_recipients || false,
        success_notify_cc_users: this.form.success_notify_cc_users || false,
        success_notify_additional_emails: this.form.success_notify_additional_emails || '',
        failure_notification_with_same_subject: this.form.failure_notification_with_same_subject || false,
        failure_notification_subject: this.form.failure_notification_subject || '',
        failure_notify_email_sender: this.form.failure_notify_email_sender || false,
        failure_notify_email_recipients: this.form.failure_notify_email_recipients || false,
        failure_notify_cc_users: this.form.failure_notify_cc_users || false,
        failure_notify_additional_emails: this.form.failure_notify_additional_emails || '',
      }
      this.$emit('submit', customerData)
      this.$emit('input', false)
    },
    close() {
      this.$emit('input', false)
      this.$emit('close')
      this.resetForm()
    },
    resetForm() {
      this.submitted = false
      this.form = {
        name: '',
        org_name: '',
        account_number: '',
        address_line1: '',
        address_line2: '',
        city: '',
        postal_code: '',
        phone: '',
        address_id: '',
      }
    },
  },
}
</script>
