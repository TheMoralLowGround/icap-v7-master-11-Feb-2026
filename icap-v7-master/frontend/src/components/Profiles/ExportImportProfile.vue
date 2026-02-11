<template>
  <b-modal
    v-model="showModal"
    title="Document Vendors Import / Export"
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <div>
      <validation-observer ref="profileForm">

        <b-alert
          variant="primary"
          show
        >
          <div
            class="alert-body"
          >{{ profile.name }}
          </div>
        </b-alert>
        <b-tabs
          v-model="tabIndex"
          content-class="mt-3"
          justified
          pills
        >
          <b-tab
            v-for="option of tabOptions"
            :key="option"
            :title="option"
            :active="option === tabOptions[tabIndex]"
          >
            <div v-show="tabIndex == 1">
              <div
                v-if="loading"
                class="text-center"
              >
                <b-spinner variant="primary" />
              </div>
              <b-form
                v-else
                @submit.prevent="onSubmit"
              >
                <b-form-group
                  v-if="profile.definitions && profile.definitions.length"
                  label="Select vendors to export"
                  label-for="documents"
                  label-class="font-1rem"
                >
                  <div
                    v-for="(definition, index) in profile.definitions"
                    :key="index + 'export'"
                    class="my-1"
                  >
                    <b-form-checkbox
                      v-model="selectedVendorsToExport"
                      :value="definition.vendor"
                      @change="errorMessage = null"
                    >
                      {{ definition.vendor }}
                    </b-form-checkbox>
                  </div>
                </b-form-group>
                <p v-else>
                  No vendor found to export
                </p>
              </b-form>
            </div>
            <div v-show="tabIndex == 0">
              <b-form @submit.prevent="onSubmit">
                <b-form-group
                  label="Process JSON File"
                >
                  <b-form-file
                    v-model="definitionsFile"
                    accept=".json"
                    :disabled="loadingFile"
                    @input="loadFile"
                  />
                </b-form-group>

                <div
                  v-if="loadingFile"
                  class="text-center"
                >
                  <b-spinner
                    variant="primary"
                    label="Spinner"
                  />
                </div>

                <b-alert
                  variant="danger"
                  :show="fileLoadError !== null ? true : false"
                >
                  <div class="alert-body">
                    <p>
                      {{ fileLoadError }}
                    </p>
                  </div>
                </b-alert>
                <template v-if="profileDefinitions.vendor_data">
                  <p class="mb-25">
                    Definition Data (Select at least one version):
                  </p>

                  <div
                    v-for="(updateSetting,updateSettingIndex) of updateSettings"
                    :key="updateSettingIndex"
                    class="mb-1"
                  >
                    <div>
                      {{ updateSetting.version.toUpperCase() }}
                    </div>
                    <div>
                      <b-form-checkbox v-model="updateSettings[updateSettingIndex].key">
                        Update Key Settings
                      </b-form-checkbox>
                      <b-form-checkbox v-model="updateSettings[updateSettingIndex].table">
                        Update Table Settings
                      </b-form-checkbox>
                    </div>
                  </div>
                  <validation-provider
                    #default="{ errors }"
                    rules="required"
                    name="import-documents"
                    vid="import-documents"
                    mode="eager"
                  >
                    <b-form-group
                      label="Select vendors to export"
                      label-for="documents"
                      label-class="font-1rem"
                    >
                      <div
                        v-for="(document, index) in vendorsToImport"
                        :key="index + 'import'"
                        class="my-1"
                      >
                        <b-form-checkbox
                          v-model="selectedVendorsToImport"
                          :value="document"
                          @change="errorMessage = null"
                        >
                          {{ document.vendor }}
                        </b-form-checkbox>
                      </div>
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                    <template v-if="profileDefinitions.profile_name !== profile.name">
                      <small class="text-danger">Process mismatched.</small>
                      <b-form-checkbox
                        v-model="acceptDeffrentProfile"
                        @change="errorMessage = null"
                      >
                        Import with different process.
                      </b-form-checkbox>
                    </template>
                    <b-alert
                      v-if="errorMessage"
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
                  </validation-provider>
                </template>
              </b-form>
            </div>
          </b-tab>
        </b-tabs>

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
        :disabled="submitting || loading || !isEligibleSubmitting"
        @click="ok()"
      >
        {{ tabOptions[tabIndex] }}
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
  BFormGroup, BButton, BForm, BSpinner, BTabs, BTab, BAlert, BModal, BFormCheckbox, BFormFile,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import exportFromJSON from 'export-from-json'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import axios from 'axios'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BTabs,
    BTab,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    BModal,
    BFormCheckbox,
    BFormFile,
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
      // modeOfTransport: null,
      updateSettings: [],
      project: null,
      vendorsToExport: null,
      selectedVendorsToExport: [],
      vendorsToImport: null,
      selectedVendorsToImport: [],
      documentsImport: null,
      //
      tabOptions: ['Import', 'Export'],
      tabIndex: 0,
      fileLoadError: null,
      definitionsFile: null,
      loadingFile: false,
      profileDefinitions: {},
      acceptDeffrentProfile: false,
    }
  },
  computed: {
    definitionVersions() {
      return this.$store.getters['applicationSettings/definitionVersions']
    },
    isEligibleSubmitting() {
      if (this.tabIndex === 0) {
        if (!this.profileDefinitions?.vendor_data) return false
        if (this.profileDefinitions?.profile_name === this.profile.name) {
          const hanyAnyVersionSelected = this.updateSettings.some(item => item.key || item.table)
          if (!this.selectedVendorsToImport.length || !hanyAnyVersionSelected) return false
        }
        if (this.profileDefinitions?.profile_name !== this.profile.name) {
          if (!this.acceptDeffrentProfile) return false
          const hanyAnyVersionSelected = this.updateSettings.some(item => item.key || item.table)
          if (!this.selectedVendorsToImport.length || !hanyAnyVersionSelected) return false
        }
      } else if (!this.selectedVendorsToExport.length) {
        return false
      }
      return true
    },
  },
  watch: {
  },
  async created() {
    await this.$store.dispatch('applicationSettings/fetchApplicationSettings')
    this.fetchProfile()
    this.resetUpdateSettings()
  },
  methods: {
    async fetchProfile() {
      this.loading = true
      axios.get(`/dashboard/profiles/${this.profile.id}/`)
        .then(res => {
          const profile = res.data
          this.profile.documents = profile.documents
          this.profile.definitions = profile.definitions
          this.loadingError = null
          this.loading = false
        }).catch(error => {
          this.loadingError = error?.response?.data?.detail || 'Error fetching process'
          this.loading = false
        })
    },
    getDocumentList(documents) {
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
      if (this.tabIndex < 1) {
        this.importDefinition()
      } else {
        this.exportDefinition()
      }
    },
    exportDefinition() {
      const fileName = `Process-vendor-${this.profile.name}`
      axios.post('/pipeline/export_definitions/', {
        profile_name: this.profile.name,
        vendors: this.selectedVendorsToExport,
      })
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
          this.showModal = null
          this.submitting = true
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error importing definitions',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.submitting = false
        })
    },
    importDefinition() {
      const vendorsToUpdate = this.selectedVendorsToImport.map(item => item.vendor)

      if (this.acceptDeffrentProfile) {
        this.profileDefinitions.vendor_data.forEach((item, i) => {
          this.profileDefinitions.vendor_data[i].definition_id = this.profile.name
        })
      }

      axios.post('/pipeline/import_definitions/', {
        profile_name: this.profile.name,
        vendors_to_update: vendorsToUpdate,
        update_settings: this.updateSettings,
        vendor_data: this.profileDefinitions.vendor_data,
      })
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.submitting = false
          this.$emit('imported')
          this.showModal = null
        })
        .catch(error => {
          this.errorMessage = error?.response?.data?.detail || 'Something went wrong'
          this.submitting = false
        })
    },
    resetUpdateSettings() {
      this.updateSettings = this.definitionVersions.map(definitionVersion => ({
        version: definitionVersion,
        key: false,
        table: false,
      }))
    },
    async loadFile() {
      this.fileLoaded = false

      if (!this.definitionsFile) {
        this.profileDefinitions = {}
        this.fileLoadError = null
        return
      }

      this.loadingFile = true

      this.parseDefinitions()
        .then(definitions => {
          this.profileDefinitions = definitions
          this.fileLoadError = null
          this.fileLoaded = true
          this.loadingFile = false
          this.acceptDeffrentProfile = false
          this.vendorsToImport = this.profileDefinitions.vendor_data
        })
        .catch(error => {
          this.profileDefinitions = []
          this.fileLoadError = error.message
          this.loadingFile = false
        })
    },
    parseDefinitions() {
      // eslint-disable-next-line consistent-return
      return new Promise((resolve, reject) => {
        if (!this.definitionsFile) {
          return reject(new Error('No file provided'))
        }
        const reader = new FileReader()
        // eslint-disable-next-line consistent-return
        reader.onload = () => resolve(JSON.parse(reader.result))
        reader.onerror = () => reject(reader.error)
        reader.readAsText(this.definitionsFile)
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
