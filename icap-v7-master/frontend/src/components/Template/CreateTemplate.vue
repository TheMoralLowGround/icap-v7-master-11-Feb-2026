<!-- eslint-disable vue/html-indent vue/max-attributes-per-line vue/html-closing-bracket-newline indent-->
<template>
  <div class="d-flex justify-content-center">
    <b-card style="max-width: 95rem;">
      <div
        v-if="loading"
        class="text-center"
      >
        <b-spinner variant="primary" />
      </div>

      <b-alert
        variant="danger"
        :show="!loading && loadingError ? true : false"
      >
        <div class="alert-body">
          <p>{{ loadingError }}</p>
        </div>
      </b-alert>

      <validation-observer
        v-if="!loading && !loadingError"
        ref="profileForm"
      >
        <b-form @submit.prevent="submitForm">
          <b-alert
            variant="danger"
            :show="errorMessage !== null ? true : false"
          >
            <div class="alert-body">
              <p>{{ errorMessage }}</p>
            </div>
          </b-alert>

          <b-row>
            <b-col cols="12">
              <b-form-group
                label="Template Name"
                label-for="template-name"
                label-cols-md="3"
                label-cols-lg="2"
              >
                <b-form-input
                  id="template-name"
                  :value="templateName"
                  readonly
                />
              </b-form-group>
            </b-col>

            <b-col cols="4">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Name"
                vid="name"
                mode="eager"
              >
                <b-form-group
                  label="Name"
                  label-for="name"
                  label-class="font-1rem"
                >
                  <b-form-input
                    id="name"
                    v-model="name"
                    :state="errors.length > 0 ? false:null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col cols="4">
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
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="project"
                    ref="vSelect"
                    v-model="project"
                    :options="options.projects"
                    @input="onChangeProject(project)"
                    @open="scrollToSelected(options.projects, project)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="4">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Document Type"
                vid="document-docType"
                mode="eager"
              >
                <b-form-group
                  label="Document Type"
                  label-for="document-docType"
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                <v-select
                  id="document-docType"
                  ref="documentDocType"
                  v-model="documents.docType"
                  :options="documentTypes"
                  :no-drop="!project"
                  :disabled="!options.projects.length"
                  @search:focus="documentTypeFocused = true"
                  @search:blur="documentTypeFocused = false"
                  @open="scrollToSelected(documentTypes, documents.docType)"
                />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col
              cols="4"
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
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="country-code"
                    ref="countryCode"
                    v-model="countryCode"
                    :options="countryOptions"
                    label="label"
                    :reduce="option => option.value"
                    @open="scrollToSelected(countryOptions, countryCode)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="4">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="File Type"
                vid="document-FileType"
                mode="eager"
              >
                <b-form-group
                  label="File Type"
                  label-for="document-FileType"
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                <v-select
                  id="document-FileType"
                  v-model="documents.FileType"
                  :options="['.xlsx', '.xls']"
                />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="4">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Language"
                vid="document-language"
                mode="eager"
              >
                <b-form-group
                  label="Language"
                  label-for="document-language"
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                <v-select
                  id="document-language"
                  ref="documentLanguage"
                  v-model="documents.language"
                  :options="options.language"
                  @open="scrollToSelected(options.language, documents.language)"
                />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="4">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="OCR Engine"
                vid="document-OCREngine"
                mode="eager"
              >
                <b-form-group
                  label="OCR Engine"
                  label-for="document-OCREngine"
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                <v-select
                  id="document-OCREngine"
                  v-model="documents.OCREngine"
                  :options="['S', 'P', 'A']"
                />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="2">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Page Rotage"
                vid="document-pageRotage"
                mode="eager"
              >
              <b-form-group label="Page Rotage"
                  label-for="document-pageRotage"
                  label-class="font-1rem"
                  class="align-checkbox"
                  >
                  <b-form-checkbox id="document-pageRotage"
                    v-model="documents.pageRotage"
                    switch
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="2">
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Barcode"
                vid="document-barcode"
                mode="eager"
              >
              <b-form-group label="Barcode"
                  label-for="document-barcode"
                  label-class="font-1rem"
                  class="align-checkbox"
                  >
                  <b-form-checkbox id="document-barcode"
                    v-model="documents.barcode"
                    switch
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
              </validation-provider>
            </b-col>
            <b-col cols="4">
              <validation-provider
                #default="{ errors }"
                name="ExDefinition"
                vid="document-definition"
                mode="eager"
              >
              <b-form-group label="Use Existing Definition"
                  label-for="document-definition"
                  label-class="font-1rem"
                  class="align-checkbox"
                  >
                  <b-form-checkbox id="document-definition"
                    v-model="documents.useExistingDefinition"
                    switch
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
              </b-form-group>
              </validation-provider>
            </b-col>
            <b-col v-if="documents.useExistingDefinition"
              cols="8"
            >
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Existing Processes"
                vid="existing-profile-name"
                mode="eager"
              >
                <b-form-group
                  label="Select Existing Process"
                  label-for="existing-profile-name"
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="existing-profile-name"
                    ref="existingProfile"
                    v-model="documents.existingProfileName"
                    :options="allDefinitions"
                    label="label"
                    :disabled="!allDefinitions.length"
                    @input="onChangeDefinitions(true)"
                    @open="scrollToSelected(allDefinitions, documents.existingProfileName)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
            <b-col v-if="documents.useExistingDefinition"
              cols="4"
            >
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Existing Document Type"
                vid="existing-document-type"
                mode="eager"
              >
                <b-form-group
                  label="Select Existing Document"
                  label-for="existing-document-type"
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="existing-document-type"
                    v-model="documents.existingDocument"
                    :options="typesByDefinition"
                    label="label"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col cols="12" class="mt-4 mb-2">
              <b-button type="submit" variant="primary" class="mr-1" :disabled="submitting || !templateName">
                                Submit
                <b-spinner v-if="submitting" small label="Small Spinner" />
              </b-button>
              <b-button type="button" variant="outline-secondary" :to="{ name: 'templates' }">
                                Cancel
              </b-button>
            </b-col>
          </b-row>
        </b-form>

      </validation-observer>
   </b-card>
   <b-modal
      v-model="showWarningModal"
      centered
      title="Warning to lose current defination"
      @ok="changeUseExistingDefinition"
    >
      <b-card-text>
        <div>
          Are you sure you want to upadate or remove existing defination?
        </div>
      </b-card-text>

      <template #modal-footer="{ ok, cancel }">
        <b-button
          variant="secondary"
          @click="cancel()"
        >
          Cancel
        </b-button>
        <b-button
          variant="primary"
          @click="ok()"
        >
          Confirm
        </b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>
import {
  BForm, BCol, BRow, BFormGroup, BFormInput, BButton, BCard, VBTooltip,
  BFormCheckbox, BSpinner, BAlert, BCardText,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import axios from 'axios'
import vSelect from 'vue-select'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import { cloneDeep } from 'lodash'

// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

const defaultDocument = {
  id: null,
  docType: null,
  language: 'English',
  OCREngine: 'S',
  pageRotage: false,
  barcode: false,
  useExistingDefinition: false,
  existingProfileName: null,
  existingDocument: null,
  fileType: '.xlsx',
}

export default {
  name: 'CreateTemplate',
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BForm,
    BRow,
    BCol,
    BFormGroup,
    BFormInput,
    BButton,
    vSelect,
    BCard,
    BFormCheckbox,
    BSpinner,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    BCardText,
  },
  props: {
    templateId: {
      type: [Number, String],
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      loading: true,
      loadingError: null,
      submitting: false,
      errorMessage: null,
      options: {},
      countryCode: null,
      name: null,
      modeOfTransport: null,
      project: null,
      manualValidation: true,
      emailFrom: null,
      emailSubjectMatchOption: 'StartsWith',
      emailSubjectMatchText: null,
      documents: cloneDeep(defaultDocument),
      documentTypeFocused: false,
      responseData: {},
      showWarningModal: false,
      confirmUpdateDefiniton: false,
    }
  },
  computed: {
    componentMode() {
      return this.$route.meta.title === 'Edit Template'
    },
    allDefinitions() {
      // Access the data from the Vuex store
      const definitions = this.$store.getters['dataView/allDefinitions']

      // Return Sorted the data
      return definitions.sort()
    },
    typesByDefinition() {
      return this.$store.getters['dataView/typesByDefinition']
    },
    userProjects() {
      return this.$store.getters['auth/projectCountries'].map(e => e.project)
    },
    userCountries() {
      return this.$store.getters['auth/projectCountries'].filter(e => this.project === e.project).map(e => e.countryCode)
    },
    countryOptions() {
      const countryCodeOptions = this.options?.country_code || []
      return countryCodeOptions.map(item => ({ label: `${item.name} - ${item.code}`, value: item.code }))
    },
    templateName() {
      if (this.countryCode && this.name && this.project && this.documents.docType) {
        return `${this.countryCode}_${this.name.toUpperCase()}_${this.project}_${this.documents.docType}`
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

      const arr = docTypeSettings.items.map(item => item[docTypeSettings.valueKey])
      return [...new Set(arr)]
    },
  },
  watch: {
    documents: {
      handler(val) {
        if (val.useExistingDefinition) {
          this.fetchAllDefinitions()
        } else {
          this.documents.existingDocument = null
          this.documents.existingProfileName = null
          this.$store.commit('dataView/SET_TYPES_BY_DEFINITION', [])
        }
      },
      deep: true,
    },
  },
  created() {
    this.initializeForm()
  },
  destroyed() {
    this.$store.dispatch('applicationSettings/reset')
  },
  methods: {
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
        const languageItems = this.$refs.documentLanguage?.$refs.dropdownMenu
        const existingProfileItems = this.$refs.existingProfile?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options.indexOf(selectedValue)
        const findSelectedIndex = options.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
        scrollDropdownToSelected(documentDocTypeItems, selectedIndex)
        scrollDropdownToSelected(countryCodeItems, findSelectedIndex)
        scrollDropdownToSelected(languageItems, selectedIndex)
        scrollDropdownToSelected(existingProfileItems, selectedIndex)
      })
    },
    changeUseExistingDefinition() {
      this.showWarningModal = false
      this.confirmUpdateDefiniton = true
      this.submitForm()
    },
    clickUseExistingDefinition() {
      if (this.templateId && this.componentMode) {
        if (this.responseData.use_existing_definition !== this.documents.useExistingDefinition) {
          this.showWarningModal = true
        } else if (this.documents.useExistingDefinition && this.responseData.existing_profile_name !== this.documents.existingProfileName) {
          this.showWarningModal = true
        } else if (this.documents.useExistingDefinition && this.responseData.existing_profile_name
        && this.responseData.existing_document !== this.documents.existingDocument) {
          this.showWarningModal = true
        }
      }
    },
    onChangeDefinitions(isChanged = false) {
      if (isChanged) {
        this.documents.existingDocument = null
        if (this.documents.existingProfileName) {
          this.fetchTypesByDefinition()
        } else {
          this.$store.commit('dataView/SET_TYPES_BY_DEFINITION', [])
        }
      }
    },
    truncate(str, length) {
      if (str && str.length > length) {
        return `${str.slice(0, length)}...`
      }
      return str
    },

    async fetchTypesByDefinition() {
      await this.$store.dispatch('dataView/fetchTypesByDefinition', this.documents.existingProfileName)
    },

    // Fetch All Definitions
    async fetchAllDefinitions() {
      try {
        // Fetch Batch
        await this.$store.dispatch('dataView/fetchAllDefinitions')

        if (!this.allDefinitions.length) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'No batch available',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        }
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
      }
    },

    async initializeForm() {
      this.loading = true

      // Get Field Options
      try {
        const profileFieldsResponse = await axios.get('/dashboard/profile_fields_options/')
        this.options = profileFieldsResponse.data
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
        return
      }

      // Get Project Options
      try {
        const res = await axios.get('/dashboard/projects/')

        const projectOptions = res.data.results.map(e => e.name).sort()

        this.options.projects = projectOptions.filter(e => this.userProjects.includes(e))
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
        return
      }

      // Get Template (if Edit)
      if (this.templateId) {
        try {
          const response = await axios.get(`/dashboard/template/${this.templateId}`)
          this.responseData = response.data

          this.countryCode = this.responseData.country
          this.name = this.responseData.name
          this.project = this.responseData.project
          this.documents.language = this.responseData.language
          this.documents.OCREngine = this.responseData.ocr_engine
          this.documents.pageRotage = this.responseData.page_rotate
          this.documents.barcode = this.responseData.barcode
          this.documents.FileType = this.responseData.file_type
          this.documents.useExistingDefinition = this.responseData.use_existing_definition
          this.documents.existingProfileName = this.responseData.existing_profile_name
          this.documents.existingDocument = this.responseData.existing_document
          if (this.documents.existingProfileName) {
            this.fetchTypesByDefinition()
          }
          await this.onChangeProject(this.project)
          this.documents.docType = this.responseData.doc_type
        } catch (error) {
          this.loadingError = error?.response?.data?.detail || 'Error fetching template'
          this.loading = false
          return
        }
      }

      this.loading = false
    },
    async onChangeProject(project) {
      if (!project) return
      try {
        this.$store.commit('definitionSettings/SET_PROJECT', project)
        await this.$store.dispatch('definitionSettings/fetchData')
        this.documents.docType = ''
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching definition settings'
      }
    },
    submitForm() {
      // event.preventDefault()
      this.$refs.profileForm.validate().then(success => {
        if (!success) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Please correct the form errors',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          return
        }

        this.submitting = true

        const requestData = {
          country: this.countryCode,
          name: this.name,
          project: this.project,
          doc_type: this.documents.docType,
          language: this.documents.language,
          ocr_engine: this.documents.OCREngine,
          page_rotate: this.documents.pageRotage,
          barcode: this.documents.barcode,
          file_type: this.documents.FileType,
        }

        if (this.templateId && !this.confirmUpdateDefiniton) {
          this.clickUseExistingDefinition()
          if (this.showWarningModal) {
            this.submitting = false
            return
          }
        }

        let request
        let message
        if (this.templateId) {
          if (this.responseData.use_existing_definition !== this.documents.useExistingDefinition) {
            requestData.use_existing_definition = this.documents.useExistingDefinition
            requestData.existing_profile_name = this.documents.existingProfileName
            requestData.existing_document = this.documents.existingDocument
          } else if (this.documents.useExistingDefinition && this.responseData.existing_profile_name !== this.documents.existingProfileName) {
            requestData.use_existing_definition = this.documents.useExistingDefinition
            requestData.existing_profile_name = this.documents.existingProfileName
            requestData.existing_document = this.documents.existingDocument
          } else if (this.documents.useExistingDefinition && this.responseData.existing_profile_name
          && this.responseData.existing_document !== this.documents.existingDocument) {
            requestData.use_existing_definition = this.documents.useExistingDefinition
            requestData.existing_profile_name = this.documents.existingProfileName
            requestData.existing_document = this.documents.existingDocument
          }

          request = axios.patch(`/dashboard/template/${this.templateId}/`, requestData)
          message = 'Template updated successfully'
        } else {
          requestData.use_existing_definition = this.documents.useExistingDefinition
          requestData.existing_profile_name = this.documents.existingProfileName
          requestData.existing_document = this.documents.existingDocument
          request = axios.post('/dashboard/template/', requestData)
          message = 'Template created successfully'
        }

        request.then(() => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.$router.push({ name: 'templates' })
          this.submitting = false
        }).catch(error => {
          const serverErrors = error?.response?.data
          if (serverErrors) {
            if (serverErrors.non_field_errors) {
              // eslint-disable-next-line prefer-destructuring
              this.errorMessage = serverErrors.non_field_errors[0]
            } else {
              this.errorMessage = null
            }

            const documentErrors = {}
            const serverDocumentErrors = serverErrors.documents
            if (serverDocumentErrors) {
              serverDocumentErrors.forEach((document, index) => {
                documentErrors[`document${index}-docType`] = document.doc_type
                documentErrors[`document${index}-contentLocation`] = document.content_location
                documentErrors[`document${index}-nameMatchingOption`] = document.name_matching_option
                documentErrors[`document${index}-language`] = document.language
                documentErrors[`document${index}-OCREngine`] = document.ocr_engine
                documentErrors[`document${index}-FileType`] = document.file_type
              })
            }

            this.$refs.profileForm.setErrors({
              countryCode: serverErrors.country,
              name: serverErrors.name,
              project: serverErrors.project,
              emailFrom: serverErrors.email_from,
              emailSubjectMatchOption: serverErrors.email_subject_match_option,
              emailSubjectMatchText: serverErrors.email_subject_match_text,
              ...documentErrors,
            })
            this.$toast({
              component: ToastificationContent,
              props: {
                title: 'Please correct the form errors',
                icon: 'AlertTriangleIcon',
                variant: 'danger',
              },
            })
          } else {
            this.errorMessage = null
            this.$toast({
              component: ToastificationContent,
              props: {
                title: error?.response?.data?.detail || 'Error submitting template',
                icon: 'AlertTriangleIcon',
                variant: 'danger',
              },
            })
          }

          this.submitting = false
        })
      })
    },
  },
}
</script>

<style lang="scss">
  @import '@core/scss/vue/libs/vue-select.scss';
</style>

<style lang="scss" scoped>
  .align-checkbox {
    // display: flex;
    // align-items: center;
    padding-top: 1rem;
    margin-bottom: 1rem;
  }

  .align-select {
    display: flex;
    align-items: center;
  }
</style>
