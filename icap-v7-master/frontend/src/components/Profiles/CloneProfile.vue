<template>
  <b-modal
    v-model="showModal"
    title="Clone Process"
    centered
    size="lg"
    @hidden="handleModalHidden"
    @hide="preventClose"
  >
    <div v-if="!loading">
      <validation-observer
        ref="profileForm"
      >
        <b-form @submit.prevent="onSubmit">
          <b-row>
            <b-col
              md="12"
            >
              <b-form-group
                label="Process Name"
                label-for="profile-name"
                label-cols-md="3"
              >
                <b-form-input
                  id="profile-name"
                  :value="profileName"
                  readonly
                />
              </b-form-group>
            </b-col>

            <b-col
              md="12"
            >
              <validation-provider
                #default="{ errors }"
                name="Name"
                vid="free-name"
                mode="eager"
                rules="required"
              >
                <b-form-group
                  label="Name"
                  label-for="free-name"
                  label-cols-md="3"
                >
                  <b-form-input
                    id="free-name"
                    v-model="freeName"
                    @input="errorMessage = null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col
              cols="12"
            >
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
                  label-cols-md="3"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="project"
                    ref="selectedProject"
                    :clearable="false"
                    v-model="project"
                    :options="projectOptions"
                    disabled
                    @input="onChangeProject"
                    @open="scrollToSelected(projectOptions, project)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col
              md="12"
            >
              <validation-provider
                #default="{ errors }"
                name="Country Code"
                vid="countryCode"
                mode="eager"
                rules="required"
              >
                <b-form-group
                  label="Country Code"
                  label-for="country-code"
                  label-cols-md="3"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="country-code"
                    ref="countryCode"
                    v-model="countryCode"
                    :options="countryOptions"
                    label="label"
                    :reduce="option => option.value"
                    @input="errorMessage = null"
                    @open="scrollToSelected(countryOptions, countryCode)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col
              md="12"
            >
              <validation-provider
                #default="{ errors }"
                name="Email Domain(s)"
                vid="emailDomains"
                mode="eager"
                :rules="{'required': !emailFrom}"
              >
                <b-form-group
                  label="Email Domain(s)"
                  label-for="email-domains"
                  label-cols-md="3"
                >
                  <b-form-input
                    id="email-domains"
                    v-model="emailDomains"
                    @input="errorMessage = null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col
              md="12"
            >
              <validation-provider
                #default="{ errors }"
                name="Source"
                vid="emailFrom"
                mode="eager"
                :rules="{'required': !emailDomains}"
              >
                <b-form-group
                  label="Source"
                  label-for="email-from"
                  label-cols-md="3"
                >
                  <b-form-input
                    id="email-from"
                    v-model="emailFrom"
                    @input="errorMessage = null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col
              md="12"
            >
              <b-form-group
                label="Description"
                label-for="email-subject"
                label-cols-md="3"
              >
                <div class="d-flex">
                  <validation-provider
                    #default="{ errors }"
                    name="Match Option"
                    vid="emailSubjectMatchOption"
                    mode="eager"
                    rules="required"
                    style="flex-basis: 160px;"
                  >
                    <b-form-group
                      :state="errors.length > 0 ? false:null"
                    >
                      <v-select
                        v-model="emailSubjectMatchOption"
                        :options="['ProcessId', 'StartsWith', 'EndsWith', 'Contains', 'Regex']"
                        @input="onEmailSubjectMatchOptionChange"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                  <validation-provider
                    #default="{ errors }"
                    name="Description Match Text"
                    vid="emailSubjectMatchText"
                    mode="eager"
                    rules="required"
                    class="flex-grow-1"
                  >
                    <b-form-group>
                      <b-form-input
                        id="email-subject"
                        v-model="emailSubjectMatchText"
                        :readonly="emailSubjectMatchOption === 'ProcessId'"
                        @input="errorMessage = null"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                </div>
              </b-form-group>
            </b-col>

            <!-- <b-col
              md="12"
            >
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Mode of Transport"
                vid="modeOfTransport"
                mode="eager"
              >
                <b-form-group
                  label="Mode of Transport"
                  label-for="mode-of-transport"
                  label-cols-md="3"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="mode-of-transport"
                    v-model="modeOfTransport"
                    :options="modeOfTransportOptions"
                    @input="errorMessage = null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col> -->

            <b-col
              md="12"
            >
              <b-form-group
                label="Include Keys"
                label-for="include-keys"
                label-cols-md="3"
                label-class="pt-0"
              >
                <b-form-checkbox
                  id="include-keys"
                  v-model="includeKeys"
                  @change="errorMessage = null"
                />
              </b-form-group>
            </b-col>

            <!-- <b-col
              md="12"
            >
              <b-form-group
                label="Include Document Issuer"
                label-for="include-vendors"
                label-cols-md="3"
                label-class="pt-0"
              >
                <b-form-checkbox
                  id="include-vendors"
                  v-model="includeVendors"
                  @change="errorMessage = null"
                />
              </b-form-group>
            </b-col> -->

            <!-- <b-col
              md="12"
            >
              <b-form-group
                label="Include Parties"
                label-for="include-customers"
                label-cols-md="3"
                label-class="pt-0"
              >
                <b-form-checkbox
                  id="include-customers"
                  v-model="includeCustomers"
                  @change="errorMessage = null"
                />
              </b-form-group>
            </b-col> -->
            <b-col
              md="12"
            >
              <b-form-group
                label="Include Documents"
                label-for="include-documents"
                label-cols-md="3"
                label-class="pt-0"
              >
                <b-form-checkbox
                  id="documents"
                  v-model="includeDocumets"
                  @change="errorMessage = null"
                />
              </b-form-group>
            </b-col>

            <!-- <b-col
              cols="12"
            >
              <b-form-group
                label="You can select documents to copy or it will be empty."
                label-for="documents"
                label-class="font-1rem"
              >
                <div
                  v-if="loadingDocuments"
                  class="text-center py-3"
                >
                  <b-spinner
                    variant="primary"
                    label="Loading documents..."
                  />
                  <p class="mt-2 text-muted">
                    Loading documents...
                  </p>
                </div>
                <div
                  v-else
                >
                  <div
                    v-for="(document, index) in documents"
                    :key="index"
                    class="my-1"
                  >
                    <b-form-checkbox
                      v-if="documentTypes.includes(document.doc_type)"
                      v-model="documents[index].checked"
                      @change="errorMessage = null"
                    >
                      {{ document.label }}
                    </b-form-checkbox>
                  </div>
                </div>
              </b-form-group>
            </b-col> -->
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
        :disabled="submitting || loading || loadingDocuments"
        @click="onSubmit"
      >
        Clone
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
      <b-spinner
        variant="primary"
      />
    </div>
  </b-modal>
</template>

<script>
import {
  BRow, BCol, BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormInput, BFormCheckbox,
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
    BFormCheckbox,
  },
  props: {
    profile: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      submitting: false,
      errorMessage: null,
      options: null,
      showModal: true,
      countryCode: null,
      freeName: null,
      // modeOfTransport: null,
      project: null,
      documents: [],
      emailDomains: null,
      emailFrom: null,
      emailSubjectMatchOption: null,
      emailSubjectMatchText: null,
      emailSubject: null,
      includeKeys: true,
      // includeVendors: false,
      // includeCustomers: false,
      includeDocumets: false,
      processId: null,
      loadingDocuments: false,
    }
  },
  computed: {
    userProjects() {
      return this.$store.getters['auth/projectCountries'].map(e => e.project)
    },
    countryOptions() {
      const countryCodeOptions = this.options?.country_code || []
      return countryCodeOptions.map(item => ({ label: `${item.name} - ${item.code}`, value: item.code }))
    },
    modeOfTransportOptions() {
      return this.options?.mode_of_transport || []
    },
    projectOptions() {
      return this.options?.project || []
    },
    profileName() {
      if (this.countryCode && this.freeName && this.project) {
        return `${this.countryCode}_${this.freeName.toUpperCase()}_${this.project}`
      }
      return ''
    },
    documentTypes() {
      if (!this.project) {
        return []
      }

      const docTypeSettings = this.$store.getters['definitionSettings/options']['options-meta-root-type']

      if (!docTypeSettings) {
        return []
      }

      return docTypeSettings.items.map(item => item[docTypeSettings.valueKey])
    },
  },
  watch: {
    // Watch for profile changes to reinitialize if needed
    'profile.id': {
      handler() {
        if (this.profile?.id) {
          this.initializeForm()
        }
      },
      immediate: false,
    },
    // Watch for country or project changes to regenerate Process ID
    countryCode() {
      if (this.emailSubjectMatchOption === 'ProcessId') {
        this.generateProcessId()
      }
    },
    project() {
      if (this.emailSubjectMatchOption === 'ProcessId') {
        this.generateProcessId()
      }
    },
  },
  created() {
    // Set initial values from profile prop if available
    this.countryCode = this.profile.country || null
    this.freeName = this.profile.free_name || null
    this.project = this.profile.project || null
    this.initializeForm()
  },
  methods: {
    async initializeForm() {
      this.loading = true

      if (!this.profile?.id) {
        this.loading = false
        return
      }

      // Fetch full profile data FIRST to get all fields
      let profileData = null
      try {
        const profileDataResponse = await axios.get(`/dashboard/profiles/${this.profile.id}/`)
        profileData = profileDataResponse.data

        // Populate all fields from the full profile data
        this.countryCode = profileData.country || this.profile.country || null
        this.freeName = profileData.free_name || this.profile.free_name || null
        this.project = profileData.project || this.profile.project || null
        this.emailDomains = profileData.email_domains || null
        this.emailFrom = profileData.email_from || null
        this.emailSubjectMatchOption = profileData.email_subject_match_option || null

        // If ProcessId option is selected, generate new Process ID instead of using the old one
        if (this.emailSubjectMatchOption === 'ProcessId') {
          // Generate new Process ID after country and project are set
          await this.generateProcessId()
        } else {
          this.emailSubjectMatchText = profileData.email_subject_match_text || null
        }

        this.includeKeys = true
        // this.includeVendors = false
        // this.includeCustomers = false
        this.includeDocumets = false

        // Initialize documents list from profile data
        this.documents = profileData.documents ? this.getDocumentList(profileData.documents) : []
      } catch (error) {
        this.errorMessage = error?.response?.data?.detail || 'Error fetching process'
        this.loading = false
        return
      }

      // Get Field Options
      try {
        const profileFieldsResponse = await axios.get('/dashboard/profile_fields_options/')
        this.options = profileFieldsResponse.data
        const res = await axios.get('/dashboard/projects/', {
          params: {
            no_pagination: true,
            sort_by: 'name',
          },
        })

        const projectOptions = res.data.map(e => e.name)

        this.options.project = projectOptions.filter(e => this.userProjects.includes(e))

        // Call onChangeProject AFTER documents are loaded
        await this.onChangeProject(this.project, false)

        this.loading = false
      } catch (error) {
        this.errorMessage = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
      }
    },
    getDocumentList(documents) {
      if (!documents || !Array.isArray(documents) || documents.length === 0) {
        return []
      }

      documents.sort((a, b) => a.id - b.id)

      const documentOptionsDict = {}

      documents.forEach(e => {
        if (documentOptionsDict[e.doc_type]) {
          documentOptionsDict[e.doc_type].push(e)
        } else {
          documentOptionsDict[e.doc_type] = [e]
        }
      })

      const profileDocuments = []

      Object.keys(documentOptionsDict).forEach(key => {
        // eslint-disable-next-line no-plusplus
        for (let i = 0; i < documentOptionsDict[key].length; i++) {
          let item = {
            label: documentOptionsDict[key][i].doc_type,
            value: `${documentOptionsDict[key][i].doc_type}_${documentOptionsDict[key][i].name_matching_text}`,
            doc_type: documentOptionsDict[key][i].doc_type,
            checked: false,
          }

          if (documentOptionsDict[key].length !== 1) {
            item = {
              ...item,
              label: `${documentOptionsDict[key][i].doc_type} ${i + 1}`,
            }
          }

          profileDocuments.push(item)
        }
      })

      return profileDocuments
    },
    onSubmit(event) {
      event.preventDefault()
      this.errorMessage = null
      this.submitting = true

      this.$refs.profileForm.validate().then(async success => {
        if (!success) {
          this.submitting = false

          return
        }

        try {
          await axios.post('/dashboard/clone_profile/', {
            source_profile_id: this.profile.id,
            email_domains: this.emailDomains,
            email_from: this.emailFrom,
            country: this.countryCode,
            email_subject_match_option: this.emailSubjectMatchOption,
            email_subject_match_text: this.emailSubjectMatchText,
            free_name: this.freeName,
            project: this.project,
            // mode_of_transport: this.modeOfTransport,
            // fill_documents: this.documents.filter(e => e.checked).map(e => e.value),
            include_keys: this.includeKeys,
            // include_vendors: this.includeVendors,
            // include_customers: this.includeCustomers,
            fill_documents: this.includeDocumets === true ? this.documents.map(e => e.value) : [],
          })

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Process cloned successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.submitting = false
          this.errorMessage = null
          // Emit cloned event first, then close modal
          this.$emit('cloned')
          this.showModal = false
        } catch (error) {
          // Extract error message from response
          let errorDetail = 'Something went wrong'

          if (error?.response?.data) {
            // Check for field-specific errors first
            if (error.response.data.email_from) {
              errorDetail = Array.isArray(error.response.data.email_from)
                ? error.response.data.email_from[0]
                : error.response.data.email_from
            } else if (error.response.data.email_domains) {
              errorDetail = Array.isArray(error.response.data.email_domains)
                ? error.response.data.email_domains[0]
                : error.response.data.email_domains
            } else if (error.response.data.detail) {
              errorDetail = error.response.data.detail
            } else if (typeof error.response.data === 'string') {
              errorDetail = error.response.data
            }
          }

          // Replace common terms for better UX
          this.errorMessage = typeof errorDetail === 'string'
            ? errorDetail.replace(/Profile/g, 'Process').replace(/email_from/gi, 'Source').replace(/email_domains/gi, 'Email Domain(s)')
            : 'Something went wrong'
          this.submitting = false
        }
      })
    },
    async onChangeProject(project, resetDocType = true) {
      this.errorMessage = null
      this.loadingDocuments = true

      try {
        if (resetDocType || !project) {
          if (this.documents && Array.isArray(this.documents)) {
            this.documents = this.documents.map(document => ({
              ...document,
              docType: null,
            }))
          }
        }

        if (!project) {
          this.loadingDocuments = false
          return
        }

        this.$store.commit('definitionSettings/SET_PROJECT', project)
        await this.$store.dispatch('definitionSettings/fetchData')

        // Only update documents if they exist
        if (this.documents && Array.isArray(this.documents)) {
          this.documents.forEach(item => {
            const currentItem = item
            currentItem.checked = false
          })
        }
      } catch (error) {
        this.errorMessage = error?.response?.data?.detail || 'Error fetching definition settings'
      } finally {
        // Always reset loading state, even if API fails
        this.loadingDocuments = false
      }
    },
    preventClose(bvModalEvt) {
      // Prevent modal from closing if we're submitting
      if (this.submitting) {
        bvModalEvt.preventDefault()
      }
    },
    handleModalHidden() {
      // Reset form and emit modal-closed event
      this.resetForm()
      this.$emit('modal-closed')
    },
    resetForm() {
      // Reset form state when modal is closed
      this.errorMessage = null
      this.submitting = false
      this.loading = false
      this.loadingDocuments = false
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
        const dropdownMenuItems = this.$refs.selectedProject?.$refs.dropdownMenu
        const countryCodeItems = this.$refs.countryCode?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options.indexOf(selectedValue)
        const findSelectedIndex = options.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
        scrollDropdownToSelected(countryCodeItems, findSelectedIndex)
      })
    },
    async generateProcessId() {
      // Only generate if both country and project are set
      if (!this.countryCode || !this.project) {
        return
      }

      try {
        const params = {
          country: this.countryCode,
          project: this.project,
        }

        const response = await axios.get('/dashboard/profiles/next_sequence/', { params })

        if (response.data?.next_process_id) {
          const newProcessId = response.data.next_process_id
          this.processId = newProcessId

          // Update emailSubjectMatchText if ProcessId option is selected
          if (this.emailSubjectMatchOption === 'ProcessId') {
            this.emailSubjectMatchText = newProcessId
          }
        }
      } catch (error) {
        // Silently fail - process ID will be generated on backend anyway
        // console.error('Error generating Process ID:', error)
      }
    },
    onEmailSubjectMatchOptionChange(newOption) {
      // When ProcessId option is selected, generate and set the Process ID
      if (newOption === 'ProcessId') {
        this.generateProcessId()
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
