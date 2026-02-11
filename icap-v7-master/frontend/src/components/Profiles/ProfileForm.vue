<template>
  <div>
    <b-card>
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
          <p>
            {{ loadingError }}
          </p>
        </div>
      </b-alert>

      <validation-observer
        v-if="!loading && !loadingError"
        ref="profileForm"
      >
        <b-form
          @submit.prevent="submitForm"
        >
          <b-alert
            variant="danger"
            :show="errorMessage !== null ? true : false"
          >
            <div class="alert-body">
              <p>
                {{ errorMessage }}
              </p>
            </div>
          </b-alert>

          <b-row>
            <b-col
              cols="12"
            >
              <b-form-group
                label="Profile Name"
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
              cols="3"
            >
              <validation-provider
                #default="{ errors }"
                rules="required"
                name="Customer Name"
                vid="customerName"
                mode="eager"
              >
                <b-form-group
                  label="Customer Name"
                  label-for="customer-name"
                  label-class="font-1rem"
                >
                  <b-form-input
                    id="customer-name"
                    v-model="customerName"
                    :state="errors.length > 0 ? false:null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col
              cols="3"
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
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="project"
                    ref="selectedProject"
                    v-model="project"
                    :options="options.project"
                    @input="onChangeProject"
                    @open="scrollToSelected(options.project, project)"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col
              cols="3"
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

            <b-col
              cols="3"
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
                  label-class="font-1rem"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="mode-of-transport"
                    v-model="modeOfTransport"
                    :options="options.mode_of_transport"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>

            <b-col
              cols="2"
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

            <b-col
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
            </b-col>

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

            <b-col
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
            </b-col>

            <b-col
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
            </b-col>

            <b-col
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
            </b-col>

            <b-col cols="12">
              <hr>
              <h5>Documents</h5>
            </b-col>

            <b-col cols="12">
              <b-table-simple class="custom-table">
                <b-thead>
                  <b-tr>
                    <b-th>
                      Document Type
                    </b-th>
                    <b-th>
                      Content Location
                    </b-th>
                    <b-th>
                      Name Matching
                    </b-th>
                    <b-th>
                      Category
                    </b-th>
                    <b-th>
                      Language
                    </b-th>
                    <b-th>
                      OCR Engine
                    </b-th>
                    <b-th>
                      Actions
                    </b-th>
                  </b-tr>
                </b-thead>
                <b-tbody>
                  <b-tr
                    v-for="(documentItem, documentItemIndex) of documents"
                    :key="documentItemIndex"
                  >
                    <b-td>
                      <validation-provider
                        #default="{ errors }"
                        name="Document Type"
                        :vid="`document${documentItemIndex}-docType`"
                        mode="eager"
                        rules="required"
                      >
                        <b-form-group
                          class="mb-0"
                          :state="errors.length > 0 ? false:null"
                        >
                          <v-select
                            ref="documentDocType"
                            v-model="documents[documentItemIndex].docType"
                            :options="documentTypes"
                            :no-drop="!project"
                            @search:focus="documentTypeFocused = true"
                            @search:blur="documentTypeFocused = false"
                            @open="scrollToSelected(documentTypes, documents[documentItemIndex].docType, documentItemIndex)"
                          />
                          <small class="text-danger">
                            {{ errors[0] || documentTypeFocused && !project ? 'Please select a "Project" to view document types' : null }}
                          </small>
                        </b-form-group>
                      </validation-provider>
                    </b-td>
                    <b-td>
                      <validation-provider
                        #default="{ errors }"
                        name="Content Location"
                        :vid="`document${documentItemIndex}-contentLocation`"
                        mode="eager"
                        rules="required"
                      >
                        <b-form-group
                          class="mb-0"
                          :state="errors.length > 0 ? false:null"
                        >
                          <v-select
                            v-model="documents[documentItemIndex].contentLocation"
                            :options="['Email Body', 'Email Attachment', 'Additional Document']"
                            @input="documentContentLocationChangeHandler(documentItemIndex)"
                          />
                          <small class="text-danger">{{ errors[0] }}</small>
                        </b-form-group>
                      </validation-provider>
                    </b-td>
                    <b-td>
                      <div class="d-flex">
                        <validation-provider
                          #default="{ errors }"
                          name="Name Matching Option"
                          :vid="`document${documentItemIndex}-nameMatchingOption`"
                          mode="eager"
                          :rules="!['Email Body', 'Additional Document'].includes(documents[documentItemIndex].contentLocation) ? 'required' : ''"
                          style="flex-basis: 180px;"
                        >
                          <b-form-group
                            class="mb-0"
                            :state="errors.length > 0 ? false:null"
                          >
                            <v-select
                              v-model="documents[documentItemIndex].nameMatchingOption"
                              :options="nameMatchingOptions[documentItemIndex]"
                              :disabled="['Email Body', 'Additional Document'].includes(documents[documentItemIndex].contentLocation)"
                              @input="onChangeNameMatchingOption(documentItemIndex)"
                            />
                            <small class="text-danger">{{ errors[0] }}</small>
                          </b-form-group>
                        </validation-provider>

                        <validation-provider
                          #default="{ errors }"
                          name="Name Matching Text"
                          :vid="`document${documentItemIndex}-nameMatchingText`"
                          mode="eager"
                          :rules="!['Email Body', 'Additional Document'].includes(documents[documentItemIndex].contentLocation) && !['None', 'Auto'].includes(documents[documentItemIndex].nameMatchingOption) ? 'required' : ''"
                          class="flex-grow-1"
                        >
                          <b-form-group
                            class="mb-0"
                          >
                            <b-form-input
                              v-model="documents[documentItemIndex].nameMatchingText"
                              :state="errors.length > 0 ? false:null"
                              :disabled="['Email Body', 'Additional Document'].includes(documents[documentItemIndex].contentLocation) || ['None', 'Auto'].includes(documents[documentItemIndex].nameMatchingOption)"
                            />
                            <small class="text-danger">{{ errors[0] }}</small>
                          </b-form-group>
                        </validation-provider>

                      </div>
                    </b-td>
                    <!-- <b-td>
                      <validation-provider
                        #default="{ errors }"
                        name="Template"
                        :vid="`document${documentItemIndex}-template`"
                        mode="eager"
                      >
                        <b-form-group
                          class="mb-0"
                          :state="errors.length > 0 ? false:null"
                        >
                          <v-select
                            v-model="documents[documentItemIndex].template"
                            :options="templateNames"
                          />
                          <small class="text-danger">{{ errors[0] }}</small>
                        </b-form-group>
                      </validation-provider>
                    </b-td> -->
                    <b-td>
                      <validation-provider
                        #default="{ errors }"
                        name="Category"
                        :vid="`document${documentItemIndex}-category`"
                        mode="eager"
                        rules="required"
                      >
                        <b-form-group
                          class="mb-0"
                          :state="errors.length > 0 ? false:null"
                        >
                          <v-select
                            v-model="documents[documentItemIndex].category"
                            :options="categoryOptions(documentItemIndex)"
                          />
                          <small class="text-danger">{{ errors[0] }}</small>
                        </b-form-group>
                      </validation-provider>
                    </b-td>
                    <b-td>
                      <validation-provider
                        #default="{ errors }"
                        name="Language"
                        :vid="`document${documentItemIndex}-language`"
                        mode="eager"
                        :rules="customRules[documentItemIndex]"
                      >
                        <b-form-group
                          class="mb-0"
                          :state="errors.length > 0 ? false:null"
                        >
                          <v-select
                            ref="documentLanguage"
                            v-model="documents[documentItemIndex].language"
                            :options="options.language"
                            :disabled="documents[documentItemIndex].contentLocation === 'Additional Document'"
                            @open="scrollToSelected(options.language, documents[documentItemIndex].language, documentItemIndex)"
                          />
                          <small class="text-danger">{{ errors[0] }}</small>
                        </b-form-group>
                      </validation-provider>
                    </b-td>
                    <b-td>
                      <validation-provider
                        #default="{ errors }"
                        name="OCR Engine"
                        :vid="`document${documentItemIndex}-OCREngine`"
                        mode="eager"
                        :rules="customRules[documentItemIndex]"
                      >
                        <b-form-group
                          class="mb-0"
                          :state="errors.length > 0 ? false:null"
                        >
                          <v-select
                            v-model="documents[documentItemIndex].OCREngine"
                            :options="['S', 'P', 'A']"
                            label="label"
                            :disabled="documents[documentItemIndex].contentLocation === 'Additional Document'"
                          />
                          <small class="text-danger">{{ errors[0] }}</small>
                        </b-form-group>
                      </validation-provider>
                    </b-td>

                    <b-td>
                      <feather-icon
                        v-b-tooltip.hover
                        title="Additional Settings"
                        icon="SettingsIcon"
                        class="cursor-pointer ml-1"
                        size="20"
                        @click="documentIndexToUpdate = documentItemIndex"
                      />
                      <feather-icon
                        v-b-tooltip.hover
                        title="Delete Document"
                        icon="Trash2Icon"
                        class="cursor-pointer ml-1"
                        size="20"
                        @click="deleteDocument(documentItemIndex)"
                      />
                    </b-td>
                  </b-tr>
                </b-tbody>

                <div
                  style="display:block; width: 250px;"
                  class="mt-25 ml-25"
                >
                  <add-item
                    label="Document"
                    button-variant="outline-primary"
                    @add="addDocuments"
                  />
                </div>
              </b-table-simple>
            </b-col>

            <b-col cols="12">
              <hr>
              <h5>Email Settings</h5>
            </b-col>

            <b-col
              cols="12"
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
            <b-col
              cols="12"
            >
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

            <b-col
              cols="12"
            >
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
                        :options="['StartsWith', 'EndsWith', 'Contains', 'Regex']"
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
                        :state="errors.length > 0 ? false:null"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                </div>
              </b-form-group>
            </b-col>

            <b-col cols="12">
              <hr>
              <h5>Email Notification Settings</h5>
              <p>Note: Email notifications will be always sent, following additional settings will be respected if provided.</p>
            </b-col>

            <b-col cols="6">
              <b-card border-variant="success">
                <h6>Success Notification Settings</h6>

                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify With Source Email Subject"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="successNotificationWithSameSubject"
                      switch
                      class="mt-50"
                      @input="onSuccessNotificationWithSameSubjectInput"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Notification Email Subject"
                    vid="successNotificationSubject"
                    mode="eager"
                    :rules="successNotificationWithSameSubject ? '' : 'required'"
                  >
                    <b-form-group
                      label="Notification Email Subject"
                      label-cols-md="3"
                      label-cols-lg="3"
                    >
                      <b-form-input
                        v-model="successNotificationSubject"
                        :disabled="successNotificationWithSameSubject"
                        :state="errors.length > 0 ? false:null"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                </b-col>
                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify Email Sender"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="successNotifyEmailSender"
                      switch
                      class="mt-50"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify Email Recipients"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="successNotifyEmailRecipients"
                      switch
                      class="mt-50"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify CC Users"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="successNotifyCCUsers"
                      switch
                      class="mt-50"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Notify Additional Emails"
                    vid="successNotifyAdditionalEmails"
                    mode="eager"
                  >
                    <b-form-group
                      label="Notify Additional Emails"
                      label-cols-md="3"
                      label-cols-lg="3"
                    >
                      <b-form-input
                        v-model="successNotifyAdditionalEmails"
                        :state="errors.length > 0 ? false:null"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                </b-col>

              </b-card>
            </b-col>

            <b-col
              cols="6"
            >
              <b-card border-variant="danger">
                <h6>Failure Notification Settings</h6>

                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify With Source Email Subject"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="failureNotificationWithSameSubject"
                      switch
                      class="mt-50"
                      @input="onFailureNotificationWithSameSubjectInput"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Notification Email Subject"
                    vid="failureNotificationSubject"
                    mode="eager"
                    :rules="failureNotificationWithSameSubject ? '' : 'required'"
                  >
                    <b-form-group
                      label="Notification Email Subject"
                      label-cols-md="3"
                      label-cols-lg="3"
                    >
                      <b-form-input
                        v-model="failureNotificationSubject"
                        :disabled="failureNotificationWithSameSubject"
                        :state="errors.length > 0 ? false:null"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                </b-col>
                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify Email Sender"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="failureNotifyEmailSender"
                      switch
                      class="mt-50"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify Email Recipients"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="failureNotifyEmailRecipients"
                      switch
                      class="mt-50"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <b-form-group
                    label="Notify CC Users"
                    label-cols-md="3"
                    label-cols-lg="3"
                  >
                    <b-form-checkbox
                      v-model="failureNotifyCCUsers"
                      switch
                      class="mt-50"
                    />
                  </b-form-group>
                </b-col>

                <b-col
                  cols="12"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Notify Additional Emails"
                    vid="failureNotifyAdditionalEmails"
                    mode="eager"
                  >
                    <b-form-group
                      label="Notify Additional Emails"
                      label-cols-md="3"
                      label-cols-lg="3"
                    >
                      <b-form-input
                        v-model="failureNotifyAdditionalEmails"
                        :state="errors.length > 0 ? false:null"
                      />
                      <small class="text-danger">{{ errors[0] }}</small>
                    </b-form-group>
                  </validation-provider>
                </b-col>

              </b-card>
            </b-col>

            <b-col
              offset-md="3"
              offset-lg="2"
            >
              <b-button
                type="submit"
                variant="primary"
                class="mr-1"
                :disabled="submitting"
              >
                Submit
                <b-spinner
                  v-if="submitting"
                  small
                  label="Small Spinner"
                />
              </b-button>
              <b-button
                type="button"
                variant="outline-secondary"
                :to="{ name: 'profiles' }"
              >
                Cancel
              </b-button>
            </b-col>
          </b-row>
        </b-form>

      </validation-observer>
    </b-card>

    <additional-document-settings
      v-if="documentIndexToUpdate != null"
      v-model="documents[documentIndexToUpdate]"
      :template-names="templateNames"
      @modal-closed="documentIndexToUpdate = null"
    />
    <ProfileConfirmation
      v-if="profileId && !acceptTempleteChange"
      @modal-closed="closedProfileConfirmation"
      @submit="confirmTempleteChange = true"
    />
  </div>
</template>

<script>
import {
  BForm, BCol, BRow, BFormGroup, BFormInput, BButton, BCard, BTableSimple, BTr, BTh, BTd, BThead, BTbody, VBTooltip,
  BFormCheckbox, BSpinner, BAlert,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import ProfileConfirmation from '@/components/Profiles/ProfileConfirmation.vue'
import axios from 'axios'
import vSelect from 'vue-select'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import { cloneDeep } from 'lodash'

// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import AddItem from '@/components/UI/AddItem.vue'
import AdditionalDocumentSettings from './AdditionalDocumentSettings.vue'

const defaultDocument = {
  id: null,
  docType: null,
  contentLocation: 'Email Attachment',
  nameMatchingOption: 'None',
  nameMatchingText: '',
  category: 'Processing',
  template: null,
  language: 'English',
  OCREngine: 'S',
  pageRotage: false,
  barcode: false,
  showEmbeddedImg: false,
}

export default {
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
    BTableSimple,
    BTr,
    BTh,
    BTd,
    BThead,
    BTbody,
    BFormCheckbox,
    BSpinner,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    AddItem,
    AdditionalDocumentSettings,
    ProfileConfirmation,
  },
  props: {
    profileId: {
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
      customerName: null,
      modeOfTransport: null,
      project: null,
      manualValidation: true,
      reassignManualValidation: false,
      storedProject: null,
      multiShipment: false,
      sendTimeStamp: false,
      automaticSplitting: false,
      ignoreDensePages: false,
      exceptionalExcel: false,
      emailDomains: null,
      emailFrom: null,
      emailSubjectMatchOption: 'StartsWith',
      emailSubjectMatchText: null,
      documents: [
        cloneDeep(defaultDocument),
      ],
      documentTypeFocused: false,
      profileDetails: null,

      successNotificationWithSameSubject: false,
      successNotificationSubject: 'DHL iCAP Automated Success Notification',
      successNotifyEmailSender: true,
      successNotifyEmailRecipients: false,
      successNotifyCCUsers: false,
      successNotifyAdditionalEmails: null,

      failureNotificationWithSameSubject: false,
      failureNotificationSubject: 'DHL iCAP Automated Failure Notification',
      failureNotifyEmailSender: true,
      failureNotifyEmailRecipients: false,
      failureNotifyCCUsers: false,
      failureNotifyAdditionalEmails: null,

      selectedMatchingOption: '',
      documentIndexToUpdate: null,
      templateNames: [],
      previousTemplates: [],
      acceptTempleteChange: true,
      confirmTempleteChange: false,
      classifiableDocTypes: [],
    }
  },
  computed: {
    nameMatchingOptions() {
      const commonOptions = ['None', 'StartsWith', 'EndsWith', 'Contains', 'Regex']
      const docTypes = this.documents.map(document => (document.docType ? document.docType.toLowerCase() : document.docType))
      return docTypes.map(docType => (this.classifiableDocTypes.includes(docType) ? [...commonOptions, 'Auto'] : commonOptions))
    },
    customRules() {
      const category = this.documents.map(document => document.category)
      return category.map(categoryItem => (categoryItem === 'Supporting' ? '' : 'required'))
    },
    userProjects() {
      return this.$store.getters['auth/projectCountries'].map(e => e.project)
    },
    userCountries() {
      return this.$store.getters['auth/projectCountries'].filter(e => this.project === e.project).map(e => e.countryCode)
    },
    countryOptions() {
      let countryCodeOptions = this.options?.country_code || []
      countryCodeOptions = countryCodeOptions.filter(e => this.userCountries.includes(e.code))

      return countryCodeOptions.map(item => ({ label: `${item.name} - ${item.code}`, value: item.code }))
    },
    profileName() {
      if (this.countryCode && this.customerName && this.modeOfTransport && this.project) {
        return `${this.countryCode}_${this.customerName.toUpperCase()}_${this.modeOfTransport}_${this.project}`
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
      return [... new Set(arr)]
    },
    pageTitle() {
      let title = this.profileId ? 'Edit Profile' : 'Create Profile'

      if (this.profileId && this.profileDetails) {
        title += ` - ${this.profileDetails.name}`
      }

      return title
    },
  },
  watch: {
    confirmTempleteChange() {
      this.submitForm()
    },
    project(value) {
      if (this.storedProject !== value) {
        this.reassignManualValidation = true
      }
      if (this.reassignManualValidation) {
        this.manualValidation = !['ShipmentCreate', 'ShipmentUpdate'].includes(value)
      }
    },
  },
  created() {
    this.initializeForm()
    this.fetchTemplates()
    this.fetchAutomaticClassifiableDocTypes()
  },
  destroyed() {
    this.$store.dispatch('applicationSettings/reset')
  },
  methods: {
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
        const res = await axios.get('/dashboard/projects/', {
          params: {
            no_pagination: true,
            sort_by: 'name',
          },
        })

        const projectOptions = res.data.map(e => e.name)

        this.options.project = projectOptions.filter(e => this.userProjects.includes(e))
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
        return
      }

      // Get Profile (if Edit)
      if (this.profileId) {
        try {
          const profileDataResponse = await axios.get(`/dashboard/profiles/${this.profileId}/`)
          const profileData = profileDataResponse.data
          this.profileDetails = profileData
          this.countryCode = profileData.country
          this.customerName = profileData.customer_name
          this.modeOfTransport = profileData.mode_of_transport
          this.project = profileData.project
          this.manualValidation = profileData.manual_validation
          this.multiShipment = profileData.multi_shipment
          this.sendTimeStamp = profileData.send_time_stamp
          this.automaticSplitting = profileData.automatic_splitting
          this.ignoreDensePages = profileData.ignore_dense_pages
          this.exceptionalExcel = profileData.exceptional_excel

          this.emailDomains = profileData.email_domains
          this.emailFrom = profileData.email_from
          this.emailSubjectMatchOption = profileData.email_subject_match_option
          this.emailSubjectMatchText = profileData.email_subject_match_text

          if (profileData.manual_validation && ['ShipmentCreate', 'ShipmentUpdate'].includes(profileData.project)) {
            this.reassignManualValidation = false
          }
          this.storedProject = profileData.project

          this.documents = profileData.documents.map(document => ({
            id: document.id,
            template: document.template,
            docType: document.doc_type,
            contentLocation: document.content_location,
            nameMatchingOption: document.name_matching_option === '' ? 'None' : document.name_matching_option,
            nameMatchingText: document.name_matching_text ? document.name_matching_text : '',
            category: document.category,
            language: document.language !== 'None' ? document.language : null,
            OCREngine: document.ocr_engine !== 'None' ? document.ocr_engine : null,
            pageRotage: document.page_rotate,
            barcode: document.barcode,
            showEmbeddedImg: document.show_embedded_img,
          }))
          this.previousTemplates = profileData.documents.map(document => ({ id: document.id, template: document.template }))

          this.successNotificationWithSameSubject = profileData.success_notification_with_same_subject
          this.successNotificationSubject = profileData.success_notification_subject
          this.successNotifyEmailSender = profileData.success_notify_email_sender
          this.successNotifyEmailRecipients = profileData.success_notify_email_recipients
          this.successNotifyCCUsers = profileData.success_notify_cc_users
          this.successNotifyAdditionalEmails = profileData.success_notify_additional_emails

          this.failureNotificationWithSameSubject = profileData.failure_notification_with_same_subject
          this.failureNotificationSubject = profileData.failure_notification_subject
          this.failureNotifyEmailSender = profileData.failure_notify_email_sender
          this.failureNotifyEmailRecipients = profileData.failure_notify_email_recipients
          this.failureNotifyCCUsers = profileData.failure_notify_cc_users
          this.failureNotifyAdditionalEmails = profileData.failure_notify_additional_emails

          await this.onChangeProject(this.project, false)
        } catch (error) {
          this.loadingError = error?.response?.data?.detail || 'Error fetching profile'
          this.loading = false
          return
        }
      }

      this.loading = false
    },
    async onChangeProject(project, resetDocType = true) {
      try {
        if (resetDocType || !project) {
          this.documents = this.documents.map(document => ({
            ...document,
            docType: null,
          }))
        }

        if (!project) {
          return
        }

        this.$store.commit('definitionSettings/SET_PROJECT', project)
        await this.$store.dispatch('definitionSettings/fetchData')
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching definition settings'
      }
    },
    categoryOptions(documentItemIndex) {
      if (this.documents[documentItemIndex].contentLocation === 'Additional Document') {
        return ['Supporting', 'Ignoring']
      }

      return ['Processing', 'Supporting']
    },
    async fetchAutomaticClassifiableDocTypes() {
      try {
        const response = await axios.get('/pipeline/automatic_classifiable_doc_types/')
        this.classifiableDocTypes = response.data.map(docType => docType.toLowerCase())
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching doc types'
      }
    },
    submitForm() {
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

        const documents = this.documents.map((document, index) => {
          const newDocument = {
            doc_type: document.docType,
            content_location: document.contentLocation,
            name_matching_option: document.nameMatchingOption === 'None' ? '' : document.nameMatchingOption,
            name_matching_text: document.nameMatchingText,
            category: document.category,
            // template: document.template,
            language: document.language || 'None',
            ocr_engine: document.OCREngine || 'None',
            page_rotate: document.pageRotage,
            barcode: document.barcode,
            show_embedded_img: document.showEmbeddedImg,
          }
          const profileDocument = this.profileDetails?.documents[index]
          if (document.template !== profileDocument?.template && this.profileId) {
            newDocument.template = document.template
          } else if (!this.profileId) {
            newDocument.template = document.template
          }
          if (this.profileId && !document.id) {
            const prevDocument = this.profileDetails.documents.find(doc => `${doc.doc_type}_${doc.name_matching_text}` === `${document.docType}_${document.nameMatchingText}`)
            if (prevDocument?.doc_type) {
              newDocument.id = prevDocument.id
            }
          }
          if (document.id) {
            newDocument.id = document.id
          }
          return newDocument
        })

        const requestData = {
          country: this.countryCode,
          customer_name: this.customerName,
          mode_of_transport: this.modeOfTransport,
          project: this.project,
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
          documents,

          success_notification_with_same_subject: this.successNotificationWithSameSubject,
          success_notification_subject: this.successNotificationSubject,
          success_notify_email_sender: this.successNotifyEmailSender,
          success_notify_email_recipients: this.successNotifyEmailRecipients,
          success_notify_cc_users: this.successNotifyCCUsers,
          success_notify_additional_emails: this.successNotifyAdditionalEmails,

          failure_notification_with_same_subject: this.failureNotificationWithSameSubject,
          failure_notification_subject: this.failureNotificationSubject,
          failure_notify_email_sender: this.failureNotifyEmailSender,
          failure_notify_email_recipients: this.failureNotifyEmailRecipients,
          failure_notify_cc_users: this.failureNotifyCCUsers,
          failure_notify_additional_emails: this.failureNotifyAdditionalEmails,
        }

        // Assuming profileData.documents and this.documents are arrays of objects with properties 'template' and 'id'
        const submitTemplates = documents.map(document => ({ id: document.id, template: document.template }))
        if (this.profileId && !this.confirmTempleteChange) {
          let hasChange = false
          // Create a map for fast lookup of templates using IDs as keys
          const submitTemplateMap = new Map()
          submitTemplates.forEach(document => {
            submitTemplateMap.set(document.id, document.template)
          })
          for (let i = 0; i < this.previousTemplates.length; i += 1) {
            const prevTemplate = this.previousTemplates[i]
            // Check if the template content matches
            const submitTemplate = submitTemplateMap.get(prevTemplate.id)
            if (submitTemplate !== undefined && submitTemplate !== prevTemplate.template) {
              hasChange = true
              break
            }
          }
          // If any change detected, set acceptTempleteChange to false
          if (hasChange) {
            this.acceptTempleteChange = false
            this.loading = false
            this.submitting = false
            return
          }
        }

        let request
        let message
        if (this.profileId) {
          request = axios.patch(`/dashboard/profiles/${this.profileId}/`, requestData)
          message = 'Profile updated successfully'
        } else {
          request = axios.post('/dashboard/profiles/', requestData)
          message = 'Profile created successfully'
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
          this.$router.push({ name: 'profiles' })
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
                documentErrors[`document${index}-nameMatchingText`] = document.name_matching_text
                documentErrors[`document${index}-category`] = document.category
                documentErrors[`document${index}-template`] = document.template
                documentErrors[`document${index}-language`] = document.language
                documentErrors[`document${index}-OCREngine`] = document.ocr_engine
              })
            }

            this.$refs.profileForm.setErrors({
              countryCode: serverErrors.country,
              customerName: serverErrors.customer_name,
              modeOfTransport: serverErrors.mode_of_transport,
              project: serverErrors.project,
              emailDomains: serverErrors.email_domains,
              emailFrom: serverErrors.email_from,
              emailSubjectMatchOption: serverErrors.email_subject_match_option,
              emailSubjectMatchText: serverErrors.email_subject_match_text,
              ...documentErrors,
              successNotificationSubject: serverErrors.success_notification_subject,
              successNotifyAdditionalEmails: serverErrors.success_notify_additional_emails,
              failureNotificationSubject: serverErrors.failure_notification_subject,
              failureNotifyAdditionalEmails: serverErrors.failure_notify_additional_emails,
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
                title: error?.response?.data?.detail || 'Error submitting profile',
                icon: 'AlertTriangleIcon',
                variant: 'danger',
              },
            })
          }

          this.submitting = false
        })
      })
    },
    addDocuments(count) {
      const newDocuments = []
      for (let i = 0; i < count; i += 1) {
        newDocuments.push(cloneDeep(defaultDocument))
      }
      this.documents = this.documents.concat(newDocuments)
    },
    deleteDocument(index) {
      this.documents.splice(index, 1)
    },
    documentContentLocationChangeHandler(index) {
      const updatedDocument = cloneDeep(this.documents[index])

      if (this.documents[index].contentLocation === 'Additional Document') {
        updatedDocument.category = 'Supporting'
      } else {
        updatedDocument.category = updatedDocument.category === 'Ignoring' ? 'Processing' : updatedDocument.category
      }

      if (['Email Body', 'Additional Document'].includes(this.documents[index].contentLocation)) {
        updatedDocument.nameMatchingOption = null
        updatedDocument.nameMatchingText = ''
      } else {
        updatedDocument.nameMatchingOption = defaultDocument.nameMatchingOption
        updatedDocument.nameMatchingText = defaultDocument.nameMatchingText
      }
      this.documents.splice(index, 1, updatedDocument)
    },
    onChangeNameMatchingOption(documentItemIndex) {
      if (['None', 'Auto'].includes(this.documents[documentItemIndex].nameMatchingOption)) {
        this.documents[documentItemIndex].nameMatchingText = ''
      }
    },
    onSuccessNotificationWithSameSubjectInput() {
      if (this.successNotificationWithSameSubject) {
        this.successNotificationSubject = null
      }
    },
    onFailureNotificationWithSameSubjectInput() {
      if (this.failureNotificationWithSameSubject) {
        this.failureNotificationSubject = null
      }
    },
    fetchTemplates() {
      this.loading = true
      const params = {
        page_size: 1000,
        page: 1,
      }
      axios.get('/dashboard/template/', {
        params,
      })
        .then(res => {
          this.templateNames = res.data.results.map(item => item.template_name)
        })
        .catch(error => {
          this.error = error?.response?.data?.detail || ' Error fetching Template'
        })
    },
    closedProfileConfirmation() {
      this.acceptTempleteChange = true
      this.loading = false
      this.submitting = false
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected(options, selectedValue, documentItemIndex = 0) {
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
        const documentDocTypeItems = this.$refs.documentDocType[documentItemIndex]?.$refs?.dropdownMenu
        const countryCodeItems = this.$refs?.countryCode?.$refs?.dropdownMenu
        const languageItems = this.$refs.documentLanguage[documentItemIndex]?.$refs?.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options.indexOf(selectedValue)
        const findSelectedIndex = options.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        if (dropdownMenuItems) scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
        if (documentDocTypeItems) scrollDropdownToSelected(documentDocTypeItems, selectedIndex)
        if (countryCodeItems) scrollDropdownToSelected(countryCodeItems, findSelectedIndex)
        if (languageItems) scrollDropdownToSelected(languageItems, selectedIndex)
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
