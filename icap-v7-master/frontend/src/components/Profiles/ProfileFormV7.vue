<template>
  <b-card>
    <b-card-body>
      <div class="d-flex align-items-center">
        <div class="flex-grow-1">
          <app-stepper
            v-model="currentStep"
            :items="numberedSteps"
            direction="horizontal"
            @input="onStepperChange"
          />
        </div>
        <div class="customer-tab-wrapper ml-2">
          <b-button
            :variant="showCustomerTab ? 'primary' : 'outline-primary'"
            class="customer-tab-btn"
            @click="toggleCustomerTab"
          >
            <feather-icon
              icon="UserIcon"
              class="mr-50"
            />
            Customer
          </b-button>
        </div>
      </div>
    </b-card-body>
    <hr>
    <b-card-body>
      <!-- General -->
      <div
        v-show="currentStep === 0 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <validation-observer ref="refGeneralForm">
          <b-form @submit.prevent="onSubmitForm">
            <b-row>
              <h2 class="me-auto">
                General Information
              </h2>
            </b-row>
            <div
              v-if="(profileId && !generalInfo.name) || projectLoading"
              class="d-flex align-center justify-content-center"
            >
              <b-spinner />
            </div>
            <b-row v-else>
              <b-col
                cols="12"
              >
                <b-form-group
                  label="Process Name"
                  label-for="profile-name"
                  label-cols-md="3"
                  label-cols-lg="2"
                >
                  <b-form-input
                    id="profile-name"
                    :value="profileName"
                    readonly
                  />
                </b-form-group>
              </b-col>
              <b-col
                cols="12"
                md="4"
              >
                <validation-provider
                  #default="{ errors }"
                  name="Name"
                  rules="required"
                >
                  <b-form-group
                    label="Name"
                    label-for="name"
                    label-class="font-1rem"
                  >
                    <b-form-input
                      id="name"
                      v-model="generalInfo.freeName"
                      :state="errors.length > 0 ? false : null"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </b-form-group>
                </validation-provider>
              </b-col>

              <b-col
                cols="12"
                md="4"
              >
                <validation-provider
                  #default="{ errors }"
                  name="Project"
                  vid="project"
                  mode="eager"
                  rules="required"
                >
                  <b-form-group
                    label="Project"
                    label-for="project"
                    label-class="font-1rem"
                    :state="errors.length > 0 ? false:null"
                  >
                    <v-select
                      id="project"
                      ref="selectedProject"
                      v-model="generalInfo.project"
                      :options="projectOptions"
                      label="name"
                      :reduce="option => option.name"
                      :state="errors.length > 0 ? false : null"
                      @input="onChangeProject"
                      @open="scrollToSelected(projectOptions, generalInfo.project)"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </b-form-group>
                </validation-provider>
              </b-col>
              <b-col
                cols="12"
                md="4"
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
                      v-model="generalInfo.countryCode"
                      :options="countryOptions"
                      label="label"
                      :reduce="option => option.value"
                      @open="scrollToSelected(countryOptions, generalInfo.countryCode)"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </b-form-group>
                </validation-provider>
              </b-col>

              <!-- <b-col
                cols="12"
                md="3"
              > -->
              <!-- <validation-provider
                  #default="{ errors }"
                  rules="required"
                  name="Mode of Transport"
                  vid="modeOfTransport"
                  mode="eager"
                >
                  <b-form-group
                    label="Mode of Transport"
                    label-for="mode-of-transport"
                    label-class="font-1rem"
                    :state="errors.length > 0 ? false:null"
                  >
                    <v-select
                      id="mode-of-transport"
                      v-model="generalInfo.modeOfTransport"
                      :options="options.mode_of_transport"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </b-form-group>
                </validation-provider>
              </b-col> -->

              <b-col
                cols="12"
                md="3"
              >
                <b-form-group
                  label="Manual Validation"
                  label-cols="6"
                >
                  <b-form-checkbox
                    v-model="manualValidation"
                    switch
                    class="mt-50"
                  />
                </b-form-group>
              </b-col>

              <!-- <b-col
                cols="2"
              >
                <b-form-group
                  label="Multi Shipment"
                  label-cols="6"
                >
                  <b-form-checkbox
                    v-model="multiShipment"
                    switch
                    class="mt-50"
                  />
                </b-form-group>
              </b-col> -->

              <b-col
                cols="2"
              >
                <b-form-group
                  label="Send Time Stamp"
                  label-cols="6"
                >
                  <b-form-checkbox
                    v-model="sendTimeStamp"
                    switch
                    class="mt-50"
                  />
                </b-form-group>
              </b-col>

              <!-- <b-col
                cols="2"
              >
                <b-form-group
                  label="Parse Document"
                  label-cols="6"
                >
                  <b-form-checkbox
                    v-model="automaticSplitting"
                    switch
                    class="mt-50"
                  />
                </b-form-group>
              </b-col> -->

              <!-- <b-col
                class="px-0"
                cols="2"
              >
                <b-form-group
                  label="Ignore Dense Pages"
                  label-cols="6"
                >
                  <b-form-checkbox
                    v-model="ignoreDensePages"
                    switch
                    class="mt-50 pl-0 pr-0"
                  />
                </b-form-group>
              </b-col> -->

              <!-- <b-col
                cols="2"
              >
                <b-form-group
                  label="Exceptional Excel"
                  label-cols="6"
                >
                  <b-form-checkbox
                    v-model="exceptionalExcel"
                    switch
                    class="mt-50"
                  />
                </b-form-group>
              </b-col> -->

              <b-col cols="12">
                <hr>
                <h5>Email Settings</h5>
              </b-col>

              <b-col cols="12">
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
                    label-cols-lg="2"
                  >
                    <b-form-input
                      id="email-domains"
                      v-model="emailDomains"
                      :state="errors.length > 0 ? false:null"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </b-form-group>
                </validation-provider>
              </b-col>

              <b-col cols="12">
                <validation-provider
                  #default="{ errors }"
                  name="Source"
                  vid="emailFrom"
                  mode="eager"
                  :rules="{'required': !emailDomains}"
                >
                  <b-form-group
                    label-for="email-from"
                    label="Source"
                    label-cols-md="3"
                    label-cols-lg="2"
                  >
                    <b-form-input
                      id="email-from"
                      v-model="emailFrom"
                      :state="errors.length > 0 ? false:null"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </b-form-group>
                </validation-provider>
              </b-col>

              <b-col cols="12">
                <b-form-group
                  label="Description"
                  label-cols-md="3"
                  label-cols-lg="2"
                >
                  <div class="d-flex">
                    <validation-provider
                      #default="{ errors }"
                      name="Match Option"
                      vid="emailSubjectMatchOption"
                      mode="eager"
                      rules="required"
                      style="flex-basis: 200px;"
                    >
                      <b-form-group
                        :state="errors.length > 0 ? false:null"
                      >
                        <v-select
                          v-model="emailSubjectMatchOption"
                          :options="['ProcessId', 'StartsWith', 'EndsWith', 'Contains', 'Regex']"
                          @input="onChangeEmailSubjectMatchOption"
                        />
                        <small class="text-danger">{{ errors[0] }}</small>
                      </b-form-group>
                    </validation-provider>
                    <validation-provider
                      #default="{ errors }"
                      name="Email Subject Match Text"
                      vid="emailSubjectMatchText"
                      mode="eager"
                      rules="required"
                      class="flex-grow-1"
                    >
                      <b-form-group>
                        <b-form-input
                          v-model="emailSubjectMatchText"
                          :state="(errors.length > 0 || matchTextError) ? false : null"
                          :disabled="emailSubjectMatchOption === 'ProcessId'"
                        />
                        <template v-if="errors.length > 0">
                          <small class="text-danger">{{ errors[0] }}</small>
                        </template>
                        <template v-else-if="matchTextError">
                          <small class="text-danger">{{ matchTextError }}</small>
                        </template>
                      </b-form-group>
                    </validation-provider>
                  </div>
                </b-form-group>

                <b-row>
                  <b-col cols="12">
                    <hr>
                    <h5>Email Notification Settings</h5>
                    <p>Note: Email notifications will be always sent, following additional settings will be respected if provided.</p>
                  </b-col>
                  <b-col cols="6">
                    <h6>Success Notification Settings</h6>
                    <b-card border-variant="success">

                      <b-row>
                        <b-col
                          cols="6"
                        >
                          <b-form-group
                            label="Notify Email Sender"
                            label-cols-md="8"
                            label-cols-lg="8"
                          >
                            <b-form-checkbox
                              v-model="successNotifyEmailSender"
                              switch
                              class="mt-50"
                            />
                          </b-form-group>
                        </b-col>

                        <b-col
                          cols="6"
                        >
                          <b-form-group
                            label="Notify Email Recipients"
                            label-cols-md="8"
                            label-cols-lg="8"
                          >
                            <b-form-checkbox
                              v-model="successNotifyEmailRecipients"
                              switch
                              class="mt-50"
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>

                      <b-row>
                        <b-col cols="12">
                          <b-form-group
                            label="Additional Emails"
                            label-for="success-additional-emails"
                            label-cols-md="12"
                            label-cols-lg="12"
                          >
                            <b-form-tags
                              id="success-additional-emails"
                              v-model="localSuccessAdditionalEmails"
                              placeholder="Type email and press Enter"
                              :input-attrs="{ placeholder: 'user@example.com' }"
                              :tag-validator="validateEmailTag"
                              separator=", "
                              remove-on-delete
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>

                      <b-row>
                        <b-col cols="12">
                          <b-form-group
                            label="Exclude Emails"
                            label-for="success-exclude-emails"
                            label-cols-md="12"
                            label-cols-lg="12"
                          >
                            <b-form-tags
                              id="success-exclude-emails"
                              v-model="localSuccessExcludeEmails"
                              placeholder="Type email and press Enter"
                              :input-attrs="{ placeholder: 'user@example.com' }"
                              :tag-validator="validateEmailTag"
                              separator=", "
                              remove-on-delete
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>

                    </b-card>
                  </b-col>

                  <b-col
                    cols="6"
                  >
                    <h6>Failure Notification Settings</h6>
                    <b-card border-variant="danger">
                      <b-row>
                        <b-col
                          cols="6"
                        >
                          <b-form-group
                            label="Notify Email Sender"
                            label-cols-md="8"
                            label-cols-lg="8"
                          >
                            <b-form-checkbox
                              v-model="failureNotifyEmailSender"
                              switch
                              class="mt-50"
                            />
                          </b-form-group>
                        </b-col>

                        <b-col
                          cols="6"
                        >
                          <b-form-group
                            label="Notify Email Recipients"
                            label-cols-md="8"
                            label-cols-lg="8"
                          >
                            <b-form-checkbox
                              v-model="failureNotifyEmailRecipients"
                              switch
                              class="mt-50"
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>

                      <b-row>
                        <b-col cols="12">
                          <b-form-group
                            label="Additional Emails"
                            label-for="failure-additional-emails"
                            label-cols-md="12"
                            label-cols-lg="12"
                          >
                            <b-form-tags
                              id="failure-additional-emails"
                              v-model="localFailureAdditionalEmails"
                              placeholder="Type email and press Enter"
                              :input-attrs="{ placeholder: 'user@example.com' }"
                              :tag-validator="validateEmailTag"
                              separator=", "
                              remove-on-delete
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>

                      <b-row>
                        <b-col cols="12">
                          <b-form-group
                            label="Exclude Emails"
                            label-for="failure-exclude-emails"
                            label-cols-md="12"
                            label-cols-lg="12"
                          >
                            <b-form-tags
                              id="failure-exclude-emails"
                              v-model="localFailureExcludeEmails"
                              placeholder="Type email and press Enter"
                              :input-attrs="{ placeholder: 'user@example.com' }"
                              :tag-validator="validateEmailTag"
                              separator=", "
                              remove-on-delete
                            />
                          </b-form-group>
                        </b-col>
                      </b-row>

                    </b-card>
                  </b-col>
                </b-row>
              </b-col>

              <b-col
                cols="12"
                class="py-3"
              >
                <navigation-buttons
                  :total-steps="numberedSteps.length"
                  :current-step="currentStep"
                  :loading="loading"
                  @prev="currentStep--"
                  @next="currentStep++"
                />
              </b-col>
            </b-row>
          </b-form>
        </validation-observer>
      </div>

      <!-- Keys -->
      <div
        v-if="currentStep === 1 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <profile-key-table
              :items="profiles.keys"
              :project-key-items="projectKeyItems"
              :submitting="loading"
              @submit="onSubmitForm"
            />
          </b-col>
          <b-col cols="12">
            <navigation-buttons
              :total-steps="numberedSteps.length"
              :current-step="currentStep"
              :loading="loading"
              hide-save
              @submit="onSubmitForm"
              @prev="currentStep--"
              @next="currentStep++"
            />
          </b-col>
        </b-row>
      </div>

      <!-- Vendors -->
      <!-- <div
        v-if="currentStep === 2"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <profile-item-table
              v-model="profileVendors"
              :items="profileVendors"
              label="Name"
              title="Document Vendors"
              view-only
            />
          </b-col>
          <b-col cols="12">
            <navigation-buttons
              :total-steps="numberedSteps.length"
              :current-step="currentStep"
              :loading="loading"
              @submit="onSubmitForm"
              @prev="currentStep--"
              @next="currentStep++"
            />
          </b-col>
        </b-row>
      </div> -->

      <!-- Parties -->
      <div
        v-if="currentStep === 2 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <profile-customer
              v-model="profiles.customers"
              :items="profiles.customers"
            />
          </b-col>
          <b-col cols="12">
            <navigation-buttons
              :total-steps="numberedSteps.length"
              :current-step="currentStep"
              hide-save
              :loading="loading"
              @submit="onSubmitForm"
              @prev="currentStep--"
              @next="currentStep++"
            />
          </b-col>
        </b-row>
      </div>

      <!-- Documents -->
      <div
        v-if="currentStep === 3 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <profile-documents
              ref="ProfileDocuments"
              v-model="profiles.documents"
              :items="profiles.documents"
              :options="documentTypes"
              :language-options="languageOptions"
              :project="generalInfo.project"
              :profile-id="profileId"
              :document-errors="documentErrors"
              :submitting="loading"
              @update-errors="handleErrorsUpdate"
              @submit="onSubmitForm"
              @reload-profile="fetchProfileDetails"
            />
          </b-col>

          <b-col cols="12">
            <navigation-buttons
              :total-steps="numberedSteps.length"
              :current-step="currentStep"
              :loading="loading"
              hide-save
              @submit="onSubmitForm"
              @prev="currentStep--"
              @next="currentStep++"
            />
          </b-col>
        </b-row>
      </div>
      <!-- DICTIONARIES   -->
      <div
        v-if="currentStep === 4 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <DictionariesTable @save-dictionaries="onSubmitForm" />
          </b-col>

          <b-col cols="12">
            <navigation-buttons
              :total-steps="numberedSteps.length"
              :current-step="currentStep"
              :loading="loading"
              hide-save
              @submit="onSubmitForm"
              @prev="currentStep--"
              @next="currentStep++"
            />
          </b-col>
        </b-row>
      </div>

      <!-- Logs -->
      <div
        v-if="currentStep === 5 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <LogsTable />
          </b-col>
          <b-col cols="12">
            <navigation-buttons
              :total-steps="numberedSteps.length"
              :current-step="currentStep"
              :loading="loading"
              @prev="currentStep--"
              @next="currentStep++"
            />
          </b-col>
        </b-row>
      </div>
      <!-- AI AGENTS -->
      <div
        v-if="currentStep === 6 && !showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <ProcessAgentSelector
              :selected-agent-ids="selectedAgentIds"
              @agents-changed="handleAgentsChanged"
            />
          </b-col>

          <b-col cols="12">
            <div class="d-flex flex-wrap gap-4 justify-content-between justify-center mt-2">
              <b-button
                variant="outline-secondary"
                @click="currentStep--"
              >
                <feather-icon
                  icon="ArrowLeftIcon"
                  class="mr-50 flip-in-rtl"
                />
                Previous
              </b-button>
            </div>
          </b-col>
        </b-row>
      </div>

      <!-- CUSTOMER -->
      <div
        v-if="showCustomerTab"
        class="disable-tab-transition"
      >
        <b-row>
          <b-col cols="12">
            <ProcessCustomerTable
              v-model="processCustomers"
              :submitting="loading"
              @submit="onSubmitForm"
            />
          </b-col>
        </b-row>
      </div>
    </b-card-body>
  </b-card>
</template>

<script>
import {
  BCard,
  BCardBody,
  BRow,
  BCol,
  BForm,
  BFormGroup,
  BFormInput,
  BButton,
  BSpinner,
  BFormCheckbox,
  BFormTags,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import axios from 'axios'
import { PresenceManager } from '@/utils/presence'
import WS from '@/utils/ws'
import bus from '@/bus'
import LogsTable from './Logs/LogsTable.vue'
// import { cloneDeep } from 'lodash'

export default {
  name: 'ProfileFormV7',
  components: {
    BCard,
    BCardBody,
    BRow,
    BCol,
    BForm,
    BFormGroup,
    BFormInput,
    BButton,
    BSpinner,
    vSelect,
    BFormCheckbox,
    BFormTags,
    ValidationProvider,
    ValidationObserver,
    LogsTable,
    NavigationButtons: () => import('./NavigationButtons.vue'),
    ProfileKeyTable: () => import('./ProfileKeyTable.vue'),
    // ProfileItemTable: () => import('./ProfileItemTable.vue'),
    ProfileCustomer: () => import('./Customer/ProfileCustomer.vue'),
    ProfileDocuments: () => import('./Documents/ProfileDocuments.vue'),
    ProcessAgentSelector: () => import('./Agents/ProcessAgentSelector.vue'),
    DictionariesTable: () => import('./Dictionaries/DictionariesTable.vue'),
    ProcessCustomerTable: () => import('./ProcessCustomer/ProcessCustomerTable.vue'),
    AppStepper: () => import('@core/components/app-stepper/AppStepper.vue'),
  },
  props: {
    profileId: {
      type: [Number, String],
      default: null,
    },
  },
  data() {
    return {
      numberedSteps: [
        { title: 'General', icon: 'SettingsIcon' },
        { title: 'Keys', icon: 'KeyIcon' },
        // { title: 'Document Vendors' },
        { title: 'Parties', icon: 'UsersIcon' },
        { title: 'Documents', icon: 'FileTextIcon' },
        { title: 'Dictionaries', icon: 'BookOpenIcon' },
        { title: 'Logs', icon: 'ListIcon' },
        { title: 'AI Agents', icon: 'CpuIcon' },
      ],
      showCustomerTab: false,
      currentStep: 0,
      loading: false,
      projectLoading: true,
      projectOptions: [],
      options: {},
      projectDocTypeOptions: [],
      profileKeyOptions: [],
      // profileVendors: [],
      documentErrors: {},
      matchTextError: null,
      initialProject: '',
      initialKeys: [], // Store initial keys
      initialDocTypes: [], // Store initial DocTypes
      initialTranslatedDocuments: [], // Store initial translated documents
      isInitialProjectSet: false,
      selectedAgentIds: [], // Store selected AI agent IDs
      // Presence tracking
      presenceManager: null,
      activeEditors: [],
      initialActiveEditors: [], // Track who was here when you joined
      presenceToastId: null,
      currentUserId: null, // Store current user's ID
      currentTabId: null, // Store current tab ID

    }
  },
  computed: {
    isCreateMode() {
      return this.$route.name === 'create-process'
    },
    isEditMode() {
      return this.$route.name === 'edit-process'
    },
    projectKeyItems() {
      // Combine and deduplicate the key options
      const combinedOptions = [
        ...this.$store.getters['definitionSettings/keyOptionsApplicableForTable'],
        ...this.$store.getters['definitionSettings/keyOptionsApplicableForKeys'],
      ]

      combinedOptions.forEach((item, index) => {
        combinedOptions[index].keyValue = item.keyValue
      })

      // Remove duplicates based on the unique `keyValue`
      const uniqueOptions = Array.from(
        new Map(combinedOptions.map(item => [item.keyValue, item])).values(),
      )

      // Return the combined list of key options
      return uniqueOptions
    },
    projectCountries() {
      return this.$store.getters['auth/projectCountries']
    },
    countryOptions() {
      const countryCodeOptions = this.options?.country_code || []
      return countryCodeOptions.map(item => ({ label: `${item.name} - ${item.code}`, value: item.code }))
    },
    languageOptions() {
      return this.options.language
    },
    profileName() {
      const {
        countryCode, freeName, project,
      } = this.$store.state.profile.generalInfo
      if (countryCode && freeName && project) {
        return `${countryCode}_${freeName.toUpperCase()}_${project}`
      }
      return ''
    },
    projectDocTypes() {
      if (!this.$store.state.profile.generalInfo.project) return null
      return this.$store.getters['definitionSettings/options']['options-meta-root-type']
    },
    documentTypes() {
      if (!this.projectDocTypes) return []
      return this.projectDocTypes.items.map(item => item.docType)
    },
    defaultDocumentTypes() {
      if (!this.projectDocTypes) return []

      const docTypes = this.projectDocTypes.items
        .filter(item => item.addToProcess)
        .map(item => item.docType)

      return [...new Set(docTypes)]
    },
    generalInfo() {
      return this.$store.state.profile.generalInfo
    },
    getProcessId() {
      return this.$store.state.profile.processId
    },
    profileSettings() {
      return {
        manualValidation: this.$store.state.profile.manualValidation,
        multiShipment: this.$store.state.profile.multiShipment,
        sendTimeStamp: this.$store.state.profile.sendTimeStamp,
        automaticSplitting: this.$store.state.profile.automaticSplitting,
        ignoreDensePages: this.$store.state.profile.ignoreDensePages,
        exceptionalExcel: this.$store.state.profile.exceptionalExcel,
      }
    },
    profiles() {
      return {
        customers: this.$store.state.profile.customers,
        documents: this.$store.state.profile.documents,
        translated_documents: this.$store.state.profile.translated_documents,
        keys: this.$store.state.profile.keys || [],
        lookupItems: this.$store.state.profile.lookupItems || [],
      }
    },
    processCustomers: {
      get() {
        return this.$store.state.profile.process_customers
      },
      set(value) {
        this.$store.commit('profile/UPDATE_PROCESS_CUSTOMERS', value)
      },
    },
    manualValidation: {
      get() {
        return this.$store.state.profile.manualValidation
      },
      set(value) {
        this.$store.commit('profile/updateManualValidation', value)
      },
    },
    multiShipment: {
      get() {
        return this.$store.state.profile.multiShipment
      },
      set(value) {
        this.$store.commit('profile/updateMultiShipment', value)
      },
    },
    sendTimeStamp: {
      get() {
        return this.$store.state.profile.sendTimeStamp
      },
      set(value) {
        this.$store.commit('profile/updateSendTimeStamp', value)
      },
    },
    automaticSplitting: {
      get() {
        return this.$store.state.profile.automaticSplitting
      },
      set(value) {
        this.$store.commit('profile/updateAutomaticSplitting', value)
      },
    },
    ignoreDensePages: {
      get() {
        return this.$store.state.profile.ignoreDensePages
      },
      set(value) {
        this.$store.commit('profile/updateIgnoreDensePages', value)
      },
    },
    exceptionalExcel: {
      get() {
        return this.$store.state.profile.exceptionalExcel
      },
      set(value) {
        this.$store.commit('profile/updateExceptionalExcel', value)
      },
    },
    successNotifyEmailSender: {
      get() {
        return this.$store.state.profile.success_notify_email_sender
      },
      set(value) {
        this.$store.commit('profile/updateSuccessNotifyEmailSender', value)
      },
    },
    successNotifyEmailRecipients: {
      get() {
        return this.$store.state.profile.success_notify_email_recipients
      },
      set(value) {
        this.$store.commit('profile/updateSuccessNotifyEmailRecipients', value)
      },
    },
    failureNotifyEmailSender: {
      get() {
        return this.$store.state.profile.failure_notify_email_sender
      },
      set(value) {
        this.$store.commit('profile/updateFailureNotifyEmailSender', value)
      },
    },
    failureNotifyEmailRecipients: {
      get() {
        return this.$store.state.profile.failure_notify_email_recipients
      },
      set(value) {
        this.$store.commit('profile/updateFailureNotifyEmailRecipients', value)
      },
    },
    successNotifyAdditionalEmails: {
      get() {
        return this.$store.state.profile.success_notify_additional_emails
      },
      set(value) {
        this.$store.commit('profile/updateSuccessNotifyAdditionalEmails', value)
      },
    },
    successNotifyExcludeEmails: {
      get() {
        return this.$store.state.profile.success_notify_exclude_emails
      },
      set(value) {
        this.$store.commit('profile/updateSuccessNotifyExcludeEmails', value)
      },
    },
    failureNotifyAdditionalEmails: {
      get() {
        return this.$store.state.profile.failure_notify_additional_emails
      },
      set(value) {
        this.$store.commit('profile/updateFailureNotifyAdditionalEmails', value)
      },
    },
    failureNotifyExcludeEmails: {
      get() {
        return this.$store.state.profile.failure_notify_exclude_emails
      },
      set(value) {
        this.$store.commit('profile/updateFailureNotifyExcludeEmails', value)
      },
    },
    emailDomains: {
      get() {
        return this.$store.state.profile.emailDomains
      },
      set(value) {
        this.$store.commit('profile/updateEmailDomains', value)
      },
    },
    emailFrom: {
      get() {
        return this.$store.state.profile.emailFrom
      },
      set(value) {
        this.$store.commit('profile/updateEmailFrom', value)
      },
    },
    emailSubjectMatchOption: {
      get() {
        return this.$store.state.profile?.emailSubjectMatchOption
      },
      set(value) {
        this.$store.commit('profile/updateEmailSubjectMatchOption', value)
      },
    },
    emailSubjectMatchText: {
      get() {
        return this.$store.state.profile?.emailSubjectMatchText
      },
      set(value) {
        this.$store.commit('profile/updateEmailSubjectMatchText', value)
      },
    },
    selectDefaultKeys: {
      get() {
        return this.$store.state.profile?.selectDefaultKeys || false
      },
      set(value) {
        this.$store.commit('profile/updateSelectDefaultKeys', value)
      },
    },
    // Local computed properties for tag inputs (converts between array and comma-separated string)
    localSuccessAdditionalEmails: {
      get() {
        const value = this.$store.state.profile.success_notify_additional_emails
        return value ? value.split(',').map(email => email.trim()).filter(Boolean) : []
      },
      set(value) {
        const stringValue = Array.isArray(value) ? value.join(', ') : value
        this.$store.commit('profile/updateSuccessNotifyAdditionalEmails', stringValue)
      },
    },
    localSuccessExcludeEmails: {
      get() {
        const value = this.$store.state.profile.success_notify_exclude_emails
        return value ? value.split(',').map(email => email.trim()).filter(Boolean) : []
      },
      set(value) {
        const stringValue = Array.isArray(value) ? value.join(', ') : value
        this.$store.commit('profile/updateSuccessNotifyExcludeEmails', stringValue)
      },
    },
    localFailureAdditionalEmails: {
      get() {
        const value = this.$store.state.profile.failure_notify_additional_emails
        return value ? value.split(',').map(email => email.trim()).filter(Boolean) : []
      },
      set(value) {
        const stringValue = Array.isArray(value) ? value.join(', ') : value
        this.$store.commit('profile/updateFailureNotifyAdditionalEmails', stringValue)
      },
    },
    localFailureExcludeEmails: {
      get() {
        const value = this.$store.state.profile.failure_notify_exclude_emails
        return value ? value.split(',').map(email => email.trim()).filter(Boolean) : []
      },
      set(value) {
        const stringValue = Array.isArray(value) ? value.join(', ') : value
        this.$store.commit('profile/updateFailureNotifyExcludeEmails', stringValue)
      },
    },
  },
  watch: {
    'generalInfo.countryCode': {
      handler() {
        this.createProcessId()
      },
    },
    'generalInfo.project': {
      handler() {
        this.createProcessId()
      },
    },
  },
  async mounted() {
    this.initializeForm()

    // Search for the specific process (requires selecedProcessName to be set)
    // Silent fail handled - not critical if process name not set yet
    await this.$store.dispatch('profile/fetchDictionariesProcesses').catch(() => {})

    // Initialize presence tracking for edit mode
    if (this.isEditMode && this.profileId) {
      await this.initializePresence()
      // Subscribe to WebSocket events via bus
      bus.$on('wsData/editorJoined', this.handleEditorJoined)
      bus.$on('wsData/editorLeft', this.handleEditorLeft)
    }
  },
  async created() {
    // this.loadFromLocalStorage()
    if (this.isCreateMode) {
      this.$store.commit('profile/setProcessId', null)
    }
    // await this.$store.dispatch('profile/fetchPartiesDynamicColumn')
  },
  // Add in created() or mounted()
  beforeRouteLeave(to, from, next) {
    this.resetProfileState()
    next()
    // if (this.hasUnsavedChanges = true) {
    //   // Show confirmation dialog
    //   const answer = window.confirm('You have unsaved changes. Are you sure you want to leave?')
    //   if (answer) {
    //     this.resetProfileState()
    //     next()
    //   } else {
    //     next(false)
    //   }
    // } else {
    //   next()
    // }
  },
  beforeDestroy() {
    this.resetProfileState()

    // Cleanup presence tracking
    this.cleanupPresence()

    // Unsubscribe from WebSocket events
    bus.$off('wsData/editorJoined', this.handleEditorJoined)
    bus.$off('wsData/editorLeft', this.handleEditorLeft)
  },
  methods: {
    validateEmailTag(tag) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(tag.trim())
    },
    handleAgentsChanged(agentIds) {
      this.selectedAgentIds = agentIds
      // You can also emit this to parent or save to store if needed
      // this.$store.commit('profile/updateSelectedAgents', agentIds)
    },
    toggleCustomerTab() {
      this.showCustomerTab = !this.showCustomerTab
    },
    onStepperChange() {
      // When user clicks on stepper, hide Customer tab
      this.showCustomerTab = false
    },
    onChangeEmailSubjectMatchOption() {
      if (this.emailSubjectMatchOption === 'ProcessId') {
        this.emailSubjectMatchText = this.getProcessId
      } else {
        this.emailSubjectMatchText = ''
      }
    },
    toCamelCase(input) {
      try {
        return input.replace(/\s(.)/g, (_, group1) => group1.toUpperCase()).replace(/\s+/g, '').replace(/^./, first => first.toLowerCase())
      } catch (error) {
        return input
      }
    },
    resetProfileState() {
      this.$store.commit('profile/resetState')
      this.initialProject = ''
      this.initialKeys = []
      this.initialDocTypes = []
      this.initialTranslatedDocuments = []
      this.isInitialProjectSet = false
    },
    async validateGeneralForm() {
      if (!this.$refs.refGeneralForm) {
        // Form not rendered, check stored validity
        return this.$store.state.profile.generalFormValid
      }

      return this.$refs.refGeneralForm.validate().then(success => {
        this.$store.commit('profile/setGeneralFormValid', success)
        if (!success) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Please correct the form errors',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.currentStep = 0
        }
        return success
      })
    },
    async fetchProjects() {
      try {
        const res = await axios.get('/dashboard/projects/', {
          params: {
            no_pagination: true,
            sort_by: 'name',
          },
        })
        this.projectOptions = res.data
      } catch (error) {
        this.showErrorToast('Error fetching projects', error)
      }
    },
    async fetchProfileDetails() {
      try {
        const response = await axios.get(`/dashboard/profiles/${this.profileId}/`)
        this.$store.commit('profile/loadProfile', response.data)
      } catch (error) {
        this.showErrorToast('Error fetching process details', error)
      }
    },
    // async fetchProfileVendors() {
    //   try {
    //     const res = await axios.get('/get_vendors_by_profile/', {
    //       params: { profile: this.profileName },
    //     })
    //     if (res.data) {
    //       this.profileVendors = res.data.map(vendor => ({ vendor }))
    //     }
    //   } catch (error) {
    //     this.showErrorToast('Error', error)
    //   }
    // },
    async initializeForm() {
      // Reset state when creating new profile
      if (!this.profileId) {
        this.resetProfileState()
        this.isInitialProjectSet = false
      }
      this.$store.dispatch('profile/fetchAutomaticClassifiableDocTypes')
      this.gerProfileFields()
      await this.fetchProjects()
      if (this.profileId) {
        await this.fetchProfileDetails()
        // await this.fetchProfileVendors()
      }
      await this.onChangeProject(this.generalInfo.project)
    },
    async gerProfileFields() {
      try {
        const profileFieldsResponse = await axios.get('/dashboard/profile_fields_options/')
        this.options = profileFieldsResponse.data
      } catch (error) {
        this.loading = false
      }
    },
    async createProcessId() {
      const { countryCode, project } = this.generalInfo

      // If either countryCode or project is missing, clear the processId (similar to how process name is cleared)
      if (!countryCode || !project) {
        this.$store.commit('profile/setProcessId', null)

        // Also clear emailSubjectMatchText if it was set to ProcessId
        if (this.emailSubjectMatchOption === 'ProcessId') {
          this.emailSubjectMatchText = ''
        }
        return
      }

      // Don't generate new processId for existing profiles until initial project is set
      if (this.profileId && !this.isInitialProjectSet) return

      try {
        const params = {
          country: countryCode,
          project,
        }

        const response = await axios.get('/dashboard/profiles/next_sequence/', { params })

        if (response.data?.next_process_id) {
          const newProcessId = response.data.next_process_id

          // Set processId in store
          this.$store.commit('profile/setProcessId', newProcessId)

          if (this.emailSubjectMatchOption === 'ProcessId') {
            this.emailSubjectMatchText = newProcessId
          }
        }
      } catch (error) {
        this.showErrorToast('Error creating Process ID', error)
      }
    },

    setInitialState(project) {
      this.initialProject = project

      const projectKeyMap = new Map(this.projectKeyItems.map(item => [item.keyValue, item]))

      this.initialKeys = (this.$store.state.profile?.keys || [])
        .filter(item => projectKeyMap.has(item.keyValue))
        .map(item => {
          const projectItem = projectKeyMap.get(item.keyValue)
          return {
            ...item,
            label: item.label || projectItem.keyLabel,
            type: item.type || projectItem.type,
            addToProcess: projectItem.addToProcess ?? false,
            required: projectItem.required ?? false,
          }
        })

      this.initialDocTypes = (this.$store.state.profile?.documents || [])
        .filter(item => this.documentTypes.includes(item.doc_type))

      this.initialTranslatedDocuments = [...(this.$store.state.profile?.translated_documents || [])]

      this.isInitialProjectSet = true
    },

    syncKeysWithProject() {
      // This method does:
      // 1. Removes keys from profile that no longer exist in the project
      // 2. Updates metadata (required, addToProcess, etc.) for existing keys
      // 3. ADDS required keys from project that are missing from profile
      // It does NOT add addToProcess keys (unless required) - those only populate on new profile or project change
      if (!this.generalInfo.project) return

      const currentProfileKeys = this.$store.state.profile?.keys || []
      const projectKeyMap = new Map(this.projectKeyItems.map(item => [item.keyValue, item]))

      // Step 1: Filter and update existing keys
      const validKeys = currentProfileKeys
        .filter(profileKey => projectKeyMap.has(profileKey.keyValue))
        .map(profileKey => {
          const projectKey = projectKeyMap.get(profileKey.keyValue)
          return {
            ...profileKey,
            // Update metadata from project (required, addToProcess, etc.)
            label: profileKey.label || projectKey.keyLabel,
            type: projectKey.type, // Always use project key type to reflect changes
            addToProcess: projectKey.addToProcess ?? false,
            required: projectKey.required ?? false,
          }
        })

      // Step 2: Add REQUIRED keys that are missing from profile
      const profileKeyValues = new Set(validKeys.map(key => key.keyValue))
      const requiredKeysToAdd = this.projectKeyItems
        .filter(projectKey => projectKey.required && !profileKeyValues.has(projectKey.keyValue))
        .map(item => ({
          label: item.keyLabel,
          type: item.type,
          keyValue: item.keyValue,
          required: item.required ?? false,
          addToProcess: item.addToProcess ?? false,
          documents: [],
          process_prompt: {
            DocClass: item.DocClass || '',
            Field_Description: item.Field_Description || '',
            Rules_Description: item.Rules_Description || '',
          },
        }))

      // Combine valid keys with required keys that need to be added
      const syncedKeys = [...validKeys, ...requiredKeysToAdd]

      // Update the store with synced keys
      this.$store.commit('profile/SET_SELECTED_KEYS', syncedKeys)
    },

    async onChangeProject(project) {
      this.projectLoading = true
      try {
        if (!project) return

        // Create processId if in create mode
        await this.createProcessId()

        // Set project and fetch project data
        this.$store.commit('definitionSettings/SET_PROJECT', project)
        await this.$store.dispatch('definitionSettings/fetchData')

        // Set initial state when first loaded (only for existing profiles)
        if (!this.isInitialProjectSet && this.profileId) {
          this.setInitialState(project)
        }
        // Restore existing keys if the project change is reverted.
        if (project === this.initialProject && this.initialKeys.length > 0) {
          // Restore initial keys but filter removed ones and update metadata
          // DO NOT add new addToProcess keys (user may have deliberately deleted them)
          this.$store.commit('profile/SET_SELECTED_KEYS', [...this.initialKeys])
          this.syncKeysWithProject() // Only filters and updates, doesn't add new keys
        } else {
          // PRESERVE ORIGINAL BEHAVIOR: Replace with default keys from new project
          // This is when user actively CHANGES to a different project
          const defaultKeys = this.projectKeyItems
            .filter(item => item.addToProcess)
            .map(item => ({
              label: item.keyLabel,
              type: item.type,
              keyValue: item.keyValue,
              required: item.required ?? false,
              addToProcess: item.addToProcess ?? false,
              documents: [],
              process_prompt: {
                DocClass: item.DocClass || '',
                Field_Description: item.Field_Description || '',
                Rules_Description: item.Rules_Description || '',
              },
            }))

          this.$store.commit('profile/SET_SELECTED_KEYS', defaultKeys)
        }

        // Restore existing keys if the project change is reverted.
        if (project === this.initialProject && this.initialDocTypes.length > 0) {
          this.$store.commit('profile/UPDATE_DOCUMENTS', [...this.initialDocTypes])
          // Also restore translated documents when reverting to initial project
          this.$store.commit('profile/SET_TRANSLATED_DOCUMENTS', [...this.initialTranslatedDocuments])
        } else {
          // Add default from the changed project to the profile documents.
          const defaultDocumentTypes = this.defaultDocumentTypes.map(item => ({
            template: null,
            doc_type: item,
            content_location: 'Email Attachment',
            name_matching_option: 'Auto',
            name_matching_text: '',
            category: 'Processing',
            language: 'English',
            ocr_engine: 'S',
            page_rotate: false,
            barcode: false,
            show_embedded_img: false,
          }))

          this.$store.commit('profile/UPDATE_DOCUMENTS', defaultDocumentTypes)

          // Clear translated documents when changing to a new project
          // since the document IDs will be different
          this.$store.commit('profile/SET_TRANSLATED_DOCUMENTS', [])
        }
      } catch (error) {
        this.projectLoading = false
        // eslint-disable-next-line no-console
        console.error('Error changing project:', error)
      } finally {
        this.projectLoading = false
      }
    },
    async onSubmitForm() {
      // Validate current step first
      if (!(await this.validateGeneralForm())) {
        return
      }

      // Sync keys before saving: remove keys not in project, add keys with addToProcess
      this.syncKeysWithProject()

      try {
        this.loading = true

        // Create payload from Vuex store
        // Remove frontend-only ID fields (UUIDs) from documents before sending to API
        const documentsForAPI = this.profiles.documents.map(doc => {
          const { id, ...docWithoutId } = doc
          // Only include id if it's a valid integer (existing document from backend)
          if (id && Number.isInteger(id)) {
            return doc
          }
          return docWithoutId
        })

        // Remove frontend-only fields (tempId) from process_customers before sending to API
        const processCustomersForAPI = this.processCustomers.map(customer => {
          const { tempId, ...customerData } = customer
          // Only include id if it's a valid integer (existing customer from backend)
          if (customerData.id && Number.isInteger(customerData.id)) {
            return customerData
          }
          // Remove id if it's not a valid integer (new customer)
          const { id, ...newCustomerData } = customerData
          return newCustomerData
        })

        const payload = {
          ...this.generalInfo,
          manual_validation: this.manualValidation,
          multi_shipment: this.multiShipment,
          send_time_stamp: this.sendTimeStamp,
          automatic_splitting: this.automaticSplitting,
          ignore_dense_pages: this.ignoreDensePages,
          exceptional_excel: this.exceptionalExcel,
          email_domains: this.emailDomains,
          email_from: this.emailFrom,
          email_subject_match_option: this.emailSubjectMatchOption,
          email_subject_match_text: this.emailSubjectMatchText,
          customers: this.profiles.customers,
          process_customers: processCustomersForAPI,
          documents: documentsForAPI,
          translated_documents: this.profiles.translated_documents,
          free_name: this.generalInfo.freeName,
          country: this.generalInfo.countryCode,
          keys: this.profiles.keys,
          process_id: this.getProcessId,
          lookup_items: this.profiles.lookupItems,
          parties_config: this.$store.state.profile.partiesConfigTable || [],
          dictionaries: [],
          success_notify_email_recipients: this.successNotifyEmailRecipients,
          success_notify_email_sender: this.successNotifyEmailSender,
          success_notify_additional_emails: this.successNotifyAdditionalEmails,
          success_notify_exclude_emails: this.successNotifyExcludeEmails,
          failure_notify_email_sender: this.failureNotifyEmailSender,
          failure_notify_email_recipients: this.failureNotifyEmailRecipients,
          failure_notify_additional_emails: this.failureNotifyAdditionalEmails,
          failure_notify_exclude_emails: this.failureNotifyExcludeEmails,
        }
        const response = this.profileId
          ? await axios.put(`/dashboard/profiles/${this.profileId}/`, payload)
          : await axios.post('/dashboard/profiles/create_with_process_id/', payload)

        if ([200, 201].includes(response.status)) {
          const isEdit = !!this.profileId
          this.showSuccessToast(isEdit ? 'Process Updated Successfully' : 'Process Added Successfully')

          // Remove any locally persisted draft data
          localStorage.removeItem('profileCreation')

          if (!isEdit) {
            const createdProfile = response.data
            const createdProfileId = createdProfile?.id
              || createdProfile?.profile?.id
              || createdProfile?.data?.id
              || createdProfile?.process_id

            if (createdProfile && typeof createdProfile === 'object') {
              this.$store.commit('profile/loadProfile', createdProfile)
            }

            if (createdProfileId) {
              await this.$router.replace({
                name: 'edit-process',
                params: { id: createdProfileId },
              })
            } else {
              await this.fetchProfileDetails()
            }
          } else {
            await this.fetchProfileDetails()
          }

          // Update initial state after save to capture the newly saved keys and documents
          // This ensures that when users change projects and change back (without saving),
          // they get the SAVED state instead of an outdated initial state
          if (this.generalInfo.project) {
            this.setInitialState(this.generalInfo.project)
          }
        }
      } catch (error) {
        let errorMessage = 'Error Saving Process'

        if (error.response) {
          // errorMessage = this.parseBackendErrors(error.response.data)
          const { generalErrors, documentErrors } = this.parseBackendErrors(error.response.data)
          // Pass document errors to child component
          this.documentErrors = documentErrors || {} // Reactively update

          if (generalErrors.includes('email_subject_match_text: Email Subject should be unique')) {
            this.matchTextError = 'Email Subject should be unique'
            this.currentStep = 0
          }

          // Navigate to step 4 if document errors exist
          if (Object.keys(documentErrors).length > 0) {
            this.currentStep = 4
          }

          errorMessage = generalErrors
        } else if (error.request) {
          errorMessage = 'No response from server - please check your network connection'
        } else if (error.response.status === 500) {
          errorMessage = 'Internal server error'
        } else {
          errorMessage = error.message
        }

        if (errorMessage) {
          this.showErrorToast(errorMessage)
        }
      } finally {
        this.loading = false
      }
    },
    parseBackendErrors(errorData) {
      // Handle simple cases first
      if (typeof errorData === 'string') {
        return {
          generalErrors: errorData,
          documentErrors: {},
        }
      }

      if (errorData.detail) {
        return {
          generalErrors: errorData.detail,
          documentErrors: {},
        }
      }

      // Initialize error containers
      const documentErrors = {}
      const otherErrors = []

      // Handle non-field errors
      if (errorData.non_field_errors) {
        const message = Array.isArray(errorData.non_field_errors)
          ? errorData.non_field_errors.join(', ')
          : errorData.non_field_errors
        otherErrors.push(message)
      }

      // Process all field errors
      Object.entries(errorData).forEach(([field, errors]) => {
        // Skip non_field_errors as we already handled them
        if (field === 'non_field_errors') return

        // Handle document errors (both formats)
        if (field === 'documents' && Array.isArray(errors)) {
          errors.forEach((itemErrors, index) => {
            if (itemErrors && typeof itemErrors === 'object') {
              if (!documentErrors[index]) documentErrors[index] = {}
              Object.entries(itemErrors).forEach(([nestedField, nestedErrors]) => {
                documentErrors[index][nestedField] = Array.isArray(nestedErrors) ? nestedErrors.join(', ') : nestedErrors
              })
            }
          })
          return
        }

        // Handle other array fields (not documents)
        if (Array.isArray(errors)) {
          const formattedErrors = errors
            .map((item, index) => {
              if (item && typeof item === 'object') {
                return Object.entries(item)
                  .map(([nestedField, nestedErrors]) => (
                    `${field}[${index}].${nestedField}: ${
                      Array.isArray(nestedErrors) ? nestedErrors.join(', ') : nestedErrors
                    }`
                  ))
              }
              return `${field}: ${Array.isArray(item) ? item.join(', ') : item}`
            })
            .flat()
            .filter(Boolean)

          otherErrors.push(...formattedErrors)
          return
        }

        // Handle object fields
        if (typeof errors === 'object') {
          const formattedErrors = Object.entries(errors)
            .map(([nestedField, nestedErrors]) => (
              `${field}.${nestedField}: ${
                Array.isArray(nestedErrors) ? nestedErrors.join(', ') : nestedErrors
              }`
            ))
          otherErrors.push(...formattedErrors)
          return
        }

        // Handle simple field errors
        otherErrors.push(`${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
      })

      return {
        generalErrors: otherErrors.length ? otherErrors.join('; ') : null,
        documentErrors,
      }
    },
    handleErrorsUpdate(updatedErrors) {
      this.documentErrors = updatedErrors
    },
    // showErrorToast(message) {
    //   const errorMessages = message.split('; ').map((msg, index) => {
    //     const isDocumentError = msg.startsWith('documents')
    //     const isCustomerError = msg.startsWith('customers')

    //     let variant = 'danger'
    //     if (isDocumentError) variant = 'warning'
    //     if (isCustomerError) variant = 'primary'

    //     return {
    //       id: index,
    //       text: msg,
    //       variant,
    //     }
    //   })

    //   errorMessages.forEach(({ text, variant }) => {
    //     this.$toast({
    //       component: ToastificationContent,
    //       props: {
    //         title: 'Error',
    //         icon: 'AlertTriangleIcon',
    //         text,
    //         variant,
    //       },
    //     })
    //   })
    // },
    showErrorToast(message, error) {
      this.$toast({
        component: ToastificationContent,
        props: {
          title: 'Error',
          icon: 'AlertTriangleIcon',
          text: error?.response?.data?.detail || message,
          variant: 'danger',
        },
      })
    },
    showSuccessToast(message, error) {
      this.$toast({
        component: ToastificationContent,
        props: {
          title: 'Success',
          icon: 'CheckIcon',
          text: error?.response?.data?.detail || message,
          variant: 'success',
        },
      })
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
        const dropdownMenuItems = this.$refs?.selectedProject?.$refs?.dropdownMenu
        const countryCodeItems = this.$refs?.countryCode?.$refs?.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options.findIndex(option => option.name === selectedValue)
        const findSelectedIndex = options.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        if (dropdownMenuItems) scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
        if (countryCodeItems) scrollDropdownToSelected(countryCodeItems, findSelectedIndex)
      })
    },

    // ===== PRESENCE TRACKING METHODS =====

    async initializePresence() {
      const { profileId } = this
      if (!profileId) return

      try {
        // Import getTabId
        const { getTabId } = await import('@/utils/presence')
        this.currentTabId = getTabId()

        // Create presence manager
        this.presenceManager = new PresenceManager('process', profileId)

        // Start tracking
        const result = await this.presenceManager.start()

        // Store current user's ID from the response
        if (result.current_user_id) {
          this.currentUserId = result.current_user_id
        }

        // Set initial active editors (who were here when you joined)
        if (result.active_editors && result.active_editors.length > 0) {
          this.activeEditors = result.active_editors
          this.initialActiveEditors = [...result.active_editors] // Copy initial list
          this.showEditorsToast()
        }

        // Join WebSocket presence room
        WS.sendRawMessage({
          type: 'join_presence_room',
          resource_type: 'process',
          resource_id: profileId,
        })
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to initialize presence:', error)
      }
    },

    async cleanupPresence() {
      const { profileId } = this

      // Hide toast
      this.hideEditorsToast()

      // Leave WebSocket room
      if (profileId) {
        try {
          WS.sendRawMessage({
            type: 'leave_presence_room',
            resource_type: 'process',
            resource_id: profileId,
          })
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('Failed to leave presence room:', error)
        }
      }

      // Stop presence manager
      if (this.presenceManager) {
        await this.presenceManager.stop()
        this.presenceManager = null
      }
    },

    formatEditorNames(editors) {
      if (!editors || editors.length === 0) return ''

      const names = editors.map(e => e.username)

      if (names.length === 1) {
        return names[0]
      } if (names.length === 2) {
        return `${names[0]} and ${names[1]}`
      }
      const lastIndex = names.length - 1
      const firstNames = names.slice(0, lastIndex).join(', ')
      return `${firstNames}, and ${names[lastIndex]}`
    },

    showEditorsToast() {
      if (!this.activeEditors || this.activeEditors.length === 0) {
        this.hideEditorsToast()
        return
      }

      // Sort editors by started_at to find the first one who joined
      const sortedEditors = [...this.activeEditors].sort((a, b) => new Date(a.started_at) - new Date(b.started_at))
      const firstEditorName = sortedEditors[0].username

      // Clear existing toast if any
      this.hideEditorsToast()

      // Show new toast
      this.presenceToastId = this.$toast(
        {
          component: ToastificationContent,
          props: {
            title: 'Concurrent Editing Warning',
            text: `${firstEditorName} is currently editing this Process`,
            icon: 'AlertCircleIcon',
            variant: 'warning',
            hideClose: true,
          },
        },
        {
          timeout: false, // No auto-dismiss
          closeButton: false, // No close button
          closeOnClick: false,
          position: 'top-center',
          hideProgressBar: true,
        },
      )
    },

    hideEditorsToast() {
      if (this.presenceToastId) {
        try {
          this.$toast.dismiss(this.presenceToastId)
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('[Presence] Error dismissing toast:', error)
        }
        this.presenceToastId = null
      } else {
        // Try to clear all toasts as fallback
        try {
          this.$toast.clear()
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('[Presence] Error clearing toasts:', error)
        }
      }
    },

    handleEditorJoined(event) {
      const data = event.data || event
      const { profileId } = this

      // Only handle events for this process
      if (data.resource_type !== 'process' || String(data.resource_id) !== String(profileId)) {
        return
      }
      // Ignore if this is the current user's own join event (Fix #1)
      if (data.user_id === this.currentUserId && data.tab_id === this.currentTabId) {
        return
      }
      // Check if this user is already in the list
      const exists = this.activeEditors.some(
        e => e.user_id === data.user_id && e.tab_id === data.tab_id,
      )

      if (!exists) {
        // Add to current list but DON'T show in toast (Fix #2 - they joined after you)
        this.activeEditors.push({
          user_id: data.user_id,
          username: data.username,
          tab_id: data.tab_id,
        })
        // Don't call showEditorsToast() - we don't want to notify about new joiners
      }
    },

    handleEditorLeft(event) {
      const data = event.data || event
      const { profileId } = this

      // Only handle events for this process
      if (data.resource_type !== 'process' || String(data.resource_id) !== String(profileId)) {
        return
      }

      // Remove from current list
      this.activeEditors = this.activeEditors.filter(
        e => !(e.user_id === data.user_id && e.tab_id === data.tab_id),
      )

      // Remove from initial list if present
      this.initialActiveEditors = this.initialActiveEditors.filter(
        e => !(e.user_id === data.user_id && e.tab_id === data.tab_id),
      )
      // If no initial editors remain, hide toast immediately
      if (this.initialActiveEditors.length === 0) {
        this.hideEditorsToast()
        return
      }

      // Check if any initial editors are still active
      const stillPresent = this.initialActiveEditors.filter(initial => this.activeEditors.some(current => current.user_id === initial.user_id && current.tab_id === initial.tab_id))

      if (stillPresent.length === 0) {
        this.hideEditorsToast()
      } else {
        // Refresh toast to show updated state (though message is generic)
        this.showEditorsToast()
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style scoped>
.customer-tab-wrapper {
  flex-shrink: 0;
}

.customer-tab-btn {
  white-space: nowrap;
  padding: 0.786rem 1.5rem;
  border-radius: 0.358rem;
}
</style>
