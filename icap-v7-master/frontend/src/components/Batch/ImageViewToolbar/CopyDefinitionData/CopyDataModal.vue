<template>
  <!-- Modal for copying definition data -->
  <b-modal
    v-model="showModal"
    title="Copy Definition Data"
    @ok="onSubmit"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
      <!-- Checkbox options to select data to copy -->
      <b-form-group label="Copy:">
        <b-form-checkbox v-model="copyKeySettings">
          Key Settings <!-- Option to copy key settings -->
        </b-form-checkbox>

        <b-form-checkbox v-model="copyTableSettings">
          Table Settings <!-- Option to copy table settings -->
        </b-form-checkbox>
      </b-form-group>

      <!-- Dropdown for selecting the "from" version -->
      <b-form-group label="From Version:">
        <v-select
          v-model="fromVersion"
          transition=""
          :clearable="true"
          :options="fromDefinitionVersionOptions"
          :reduce="option => option.value"
        />
      </b-form-group>

      <!-- Dropdown for selecting the "to" version -->
      <b-form-group label="To Version:">
        <v-select
          v-model="toVersion"
          transition=""
          :clearable="true"
          :options="toDefinitionVersionOptions"
          :reduce="option => option.value"
        />
      </b-form-group>
    </b-card-text>

    <!-- Modal footer with Cancel and Copy Data buttons -->
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="submitting || !enableSubmit"
        @click="ok()"
      >
        Copy Data
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BButton, BModal, BSpinner, BCardText, BFormCheckbox, BFormGroup,
} from 'bootstrap-vue'
import axios from 'axios'
import vSelect from 'vue-select'
import bus from '@/bus'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BButton,
    BModal,
    BSpinner,
    BCardText,
    BFormCheckbox,
    vSelect,
    BFormGroup,
  },
  data() {
    return {
      showModal: true, // Controls the visibility of the modal
      submitting: false, // Indicates whether the form submission is in progress
      copyKeySettings: false, // Tracks if the user wants to copy key settings
      copyTableSettings: false, // Tracks if the user wants to copy table settings
      fromVersion: null, // Selected version to copy data from
      toVersion: null, // Selected version to copy data to
    }
  },
  computed: {
    templatesRoute() {
      // Determines if the current route is for template batch
      return this.$route.name === 'template-batch'
    },
    definitionVersions() {
      // Retrieves available definition versions from the Vuex store
      return this.$store.getters['applicationSettings/definitionVersions']
    },
    definitionVersionOptions() {
      // Formats definition versions for dropdown options
      return this.definitionVersions.map(definitionVersion => ({
        label: definitionVersion.toUpperCase(),
        value: definitionVersion,
      }))
    },
    fromDefinitionVersionOptions() {
      // Filters out the "to" version from the "from" version dropdown options
      return this.definitionVersionOptions.filter(option => option.value !== this.toVersion)
    },
    toDefinitionVersionOptions() {
      // Filters out the "from" version from the "to" version dropdown options
      return this.definitionVersionOptions.filter(option => option.value !== this.fromVersion)
    },
    enableSubmit() {
      // Determines if the form can be submitted (checkboxes and versions must be selected)
      return (this.copyKeySettings || this.copyTableSettings) && this.fromVersion && this.toVersion
    },
  },
  methods: {
    onSubmit(event) {
      // Handles the form submission
      event.preventDefault()
      this.submitting = true // Sets the submitting state to true

      // Retrieve necessary data from the Vuex store
      const definition = this.$store.getters['dataView/selectedDefinition']
      const { definitionId } = this.$store.getters['batch/batch']
      let tamplateName = null
      if (this.templatesRoute) {
        tamplateName = definitionId // Use template name if on the template batch route
      }

      // Make an API call to copy definition data
      axios.post('/copy_definition_data/', null, {
        params: {
          id: definition.id,
          key: this.copyKeySettings,
          table: this.copyTableSettings,
          from_version: this.fromVersion,
          to_version: this.toVersion,
          template: tamplateName,
        },
      }).then(res => {
        // Show a success toast on successful API call
        this.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        // Refresh data if the "to" version is the currently selected version
        const selectedDefinitionVersion = this.$store.getters['dataView/selectedDefinitionVersion']
        if (this.toVersion === selectedDefinitionVersion) {
          bus.$emit('dataView/refreshData')
        }

        this.submitting = false // Reset submitting state
        this.showModal = false // Close the modal
      }).catch(error => {
        // Handle API call errors
        const message = error?.response?.data?.detail || 'Error copying definition data'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        this.submitting = false // Reset submitting state
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
