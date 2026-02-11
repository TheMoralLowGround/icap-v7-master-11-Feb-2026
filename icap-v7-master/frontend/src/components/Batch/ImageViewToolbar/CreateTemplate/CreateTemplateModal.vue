<template>
  <b-modal
    v-model="showModal"
    title="Create Template"
    no-close-on-backdrop
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <div v-if="!loading">
      <validation-observer ref="profileForm">
        <b-form @submit.prevent="onSubmit">
          <b-row>
            <b-col md="12">
              <b-form-group
                label="Template Name"
                label-for="template-name"
                label-cols-md="4"
              >
                <b-form-input
                  id="template-name"
                  :value="profileName"
                  readonly
                />
              </b-form-group>
            </b-col>

            <b-col md="12">
              <b-form-group
                label="Name"
                label-for="name"
                label-cols-md="4"
              >
                <b-form-input
                  id="name"
                  v-model="formData.vendor"
                  @input="errorMessage = null"
                />
              </b-form-group>
            </b-col>

            <b-col cols="12">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Project"
                vid="project"
                mode="eager"
              >
                <b-form-group
                  label="Project"
                  label-for="project"
                  label-cols-md="4"
                  :state="errors.length > 0 ? false : null"
                >
                  <v-select
                    id="project"
                    ref="vSelect"
                    v-model="formData.project"
                    :options="options.project"
                    @input="onChangeProject(true)"
                    @open="scrollToSelected(options.projects, formData.project)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="12">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Country"
                vid="country"
                mode="eager"
              >
                <b-form-group
                  label="Country"
                  label-for="country"
                  label-cols-md="4"
                  :state="errors.length > 0 ? false : null"
                >
                  <v-select
                    id="country"
                    ref="countryCode"
                    v-model="formData.country"
                    :options="options.country_code"
                    :reduce="option => option.value"
                    @open="scrollToSelected(options.country_code, formData.country)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="12">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="doc_type"
                vid="doc_type"
                mode="eager"
              >
                <b-form-group
                  label="Document Type"
                  label-for="doc_type"
                  label-cols-md="4"
                  :state="errors.length > 0 ? false : null"
                >
                  <v-select
                    id="doc_type"
                    ref="documentDocType"
                    v-model="formData.docType"
                    :options="documentTypes"
                    @input="errorMessage = null"
                    @open="scrollToSelected(documentTypes, formData.docType)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

          </b-row>

          <b-alert
            variant="danger"
            :show="errorMessage !== null ? true : false"
            class="my-1"
          >
            <div class="alert-body">
              <p>
                {{ errorMessage }}
              </p>
            </div>
          </b-alert>
        </b-form>
      </validation-observer>
    </div>
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        variant="primary"
        type="submit"
        :disabled="submitting || loading"
        @click="ok()"
      >
        Create
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>

    <div
      v-if="loading"
      class="text-center"
    >
      <b-spinner variant="primary" />
    </div>
  </b-modal>
</template>

<script>
import {
  BRow, BCol, BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormInput,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import vSelect from 'vue-select'
import axios from 'axios'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    vSelect,
    BRow,
    BCol,
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    BFormInput,
    BModal,
  },
  data() {
    return {
      loading: false, // Tracks the loading state for asynchronous operations
      submitting: false, // Tracks the form submission state
      errorMessage: null, // Stores error messages to display to the user
      formData: {}, // Holds form data input by the user
      options: {
        project: [], // Options for project dropdown
        country_code: [], // Options for country code dropdown
      },
      showModal: true, // Controls the visibility of the modal
    }
  },
  computed: {
    // Retrieves the current batch data from the Vuex store
    batch() {
      return this.$store.getters['batch/batch']
    },
    // Dynamically generates the profile name based on form data
    profileName() {
      if (this.formData.country && this.formData.vendor && this.formData.docType && this.formData.project) {
        return `${this.formData.country}_${this.formData.vendor.toUpperCase()}_${this.formData.project}_${this.formData.docType}`
      }
      return '' // Returns an empty string if any required field is missing
    },
    // Retrieves document types based on the selected project
    documentTypes() {
      if (!this.formData.project) {
        return [] // Returns an empty array if no project is selected
      }

      const docTypeSettings = this.$store.getters['definitionSettings/options']['options-meta-root-type']

      if (!docTypeSettings) {
        return [] // Returns an empty array if no document type settings are available
      }

      // Maps the document type settings to an array of values
      const arr = docTypeSettings.items.map(item => item[docTypeSettings.valueKey])
      return [...new Set(arr)]
    },
  },
  created() {
    // Initializes the component by calling init() and onChangeProject()
    this.init()
    this.onChangeProject()
  },
  methods: {
    // Initializes the component's data and fetches options for dropdowns
    async init() {
      try {
        // Copies the batch data to formData and extracts country code
        this.formData = { ...this.batch }
        this.formData.docType = this.batch.type
        this.formData.country = this.batch.definitionId.slice(0, 2)

        // Fetches and sets project options
        const res = await axios.get('/dashboard/projects/')
        this.options.project = res.data.results.map(e => e.name).sort()
      } catch (error) {
        // Handles errors when fetching project options
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
      }
      try {
        // Fetches and sets country code options
        const res = await axios.get('/dashboard/profile_fields_options/')
        const countryCodeOptions = res.data.country_code || []
        this.options.country_code = countryCodeOptions.map(item => ({ label: `${item.name} - ${item.code}`, value: item.code }))
        // this.options.project = res.data.results.map(e => e.name).sort()
      } catch (error) {
        // Handles errors when fetching country code options
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
      }
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected(options, selectedValue) {
      this.$nextTick(() => {
        // Helper function to scroll a dropdown menu to the selected item
        const scrollDropdownToSelected = (dropdownMenu, selectedIndex) => {
          if (dropdownMenu && selectedIndex >= 0) {
            // Calculate scroll position by assuming each item has a uniform height
            const itemHeight = dropdownMenu.scrollHeight / options.length

            // Adjust scrollTop to bring the selected item closer to the top
            const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
            // eslint-disable-next-line no-param-reassign
            dropdownMenu.scrollTop = scrollPosition
          }
        }

        // Get references to dropdown menus
        const dropdownMenuItems = this.$refs.vSelect?.$refs.dropdownMenu
        const documentDocTypeItems = this.$refs.documentDocType?.$refs.dropdownMenu
        const countryCodeItems = this.$refs.countryCode?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options?.indexOf(selectedValue)
        const findSelectedIndex = options?.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
        scrollDropdownToSelected(documentDocTypeItems, selectedIndex)
        scrollDropdownToSelected(countryCodeItems, findSelectedIndex)
      })
    },
    // Handles form submission
    onSubmit(event) {
      event.preventDefault() // Prevents default form submission
      this.errorMessage = null // Resets error message
      this.submitting = true // Sets submitting to true

      this.$refs.profileForm.validate().then(async success => {
        if (!success) {
          this.submitting = false // Stops submission if validation fails
          return
        }

        // Prepares request data for template creation
        const requestData = {
          country: this.formData.country,
          name: this.formData.vendor,
          project: this.formData.project,
          doc_type: this.formData.docType,
          language: 'English',
          ocr_engine: 'S',
          page_rotate: false,
          barcode: false,
          use_existing_definition: true,
          existing_profile_name: this.formData.definitionId,
          existing_document: this.formData.type,
          file_type: '.xlsx',
        }

        try {
          // Sends a POST request to create a new template
          await axios.post('/dashboard/template/', requestData)
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Template created successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          // Resets state and closes the modal on success
          this.submitting = false
          this.errorMessage = null
          this.showModal = false
        } catch (error) {
          // Handles errors during template creation
          this.errorMessage = error?.response?.data?.non_field_errors[0] || 'Something went wrong'
          this.submitting = false
        }
      })
    },
    // Handles changes to the selected project
    async onChangeProject(isChanged = false) {
      try {
        if (isChanged) {
          this.formData.docType = '' // Resets the document type if the project is changed
        }
        // Updates the project in the Vuex store and fetches related data
        this.$store.commit('definitionSettings/SET_PROJECT', this.formData.project)
        await this.$store.dispatch('definitionSettings/fetchData')
      } catch (error) {
        // Handles errors when updating the project
        this.loadingError = error?.response?.data?.detail || 'Error fetching definition settings'
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
