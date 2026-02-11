<template>
  <b-modal
    v-model="showModal"
    title="Clone Template"
    centered
    no-close-on-backdrop
    size="lg"
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
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
                label="Template Name"
                label-for="template-name"
                label-cols-md="3"
              >
                <b-form-input
                  id="template-name"
                  :value="profileName"
                  readonly
                />
              </b-form-group>
            </b-col>

            <b-col
              md="12"
            >
              <b-form-group
                label="Name"
                label-for="name"
                label-cols-md="3"
              >
                <b-form-input
                  id="name"
                  v-model="localTemplate.name"
                  @input="errorMessage = null"
                />
              </b-form-group>
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
                    ref="vSelect"
                    v-model="localTemplate.project"
                    :options="options.project"
                    @input="onChangeProject(true)"
                    @open="scrollToSelected(options.projects, localTemplate.project)"
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
                name="Country"
                vid="country"
                mode="eager"
              >
                <b-form-group
                  label="Country"
                  label-for="country"
                  label-cols-md="3"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="country"
                    ref="countryCode"
                    v-model="localTemplate.country"
                    :options="options.country_code"
                    :reduce="option => option.value"
                    @input="onChangeProject(true)"
                    @open="scrollToSelected(options.country_code, localTemplate.country)"
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
                name="doc_type"
                vid="doc_type"
                mode="eager"
              >
                <b-form-group
                  label="Document Type"
                  label-for="doc_type"
                  label-cols-md="3"
                  :state="errors.length > 0 ? false:null"
                >
                  <v-select
                    id="doc_type"
                    ref="documentDocType"
                    v-model="localTemplate.doc_type"
                    :options="documentTypes"
                    @input="errorMessage = null"
                    @open="scrollToSelected(documentTypes, localTemplate.doc_type)"
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
        :disabled="submitting || loading || !profileName"
        @click="ok()"
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
  props: {
    template: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      submitting: false,
      errorMessage: null,
      localTemplate: { ...this.template },
      options: {
        project: [],
        country_code: [],
      },
      showModal: true,
    }
  },
  computed: {
    profileName() {
      if (this.localTemplate.country && this.localTemplate.name && this.localTemplate.doc_type && this.localTemplate.project) {
        return `${this.localTemplate.country}_${this.localTemplate.name.toUpperCase()}_${this.localTemplate.project}_${this.localTemplate.doc_type}`
      }
      return ''
    },
    documentTypes() {
      if (!this.localTemplate.project) {
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
  created() {
    this.init()
    this.onChangeProject()
  },
  methods: {
    async init() {
      try {
        const res = await axios.get('/dashboard/projects/')

        this.options.project = res.data.results.map(e => e.name).sort()
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
      }
      try {
        const res = await axios.get('/dashboard/profile_fields_options/')

        const countryCodeOptions = res.data.country_code || []
        this.options.country_code = countryCodeOptions.map(item => ({ label: `${item.name} - ${item.code}`, value: item.code }))

        // this.options.project = res.data.results.map(e => e.name).sort()
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching field options'
        this.loading = false
      }
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
          await axios.post('/dashboard/clone_template/', {
            source_template_id: this.localTemplate.id,
            name: this.localTemplate.name,
            project: this.localTemplate.project,
            country: this.localTemplate.country,
            doc_type: this.localTemplate.doc_type,
          })
          this.$emit('cloned')
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'template cloned successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.submitting = false
          this.errorMessage = null
          this.showModal = false
        } catch (error) {
          this.errorMessage = error?.response?.data?.detail || 'Something went wrong'
          this.submitting = false
        }
      })
    },
    async onChangeProject(isChanged = false) {
      try {
        if (isChanged) {
          this.localTemplate.doc_type = ''
        }
        this.$store.commit('definitionSettings/SET_PROJECT', this.localTemplate.project)
        await this.$store.dispatch('definitionSettings/fetchData')
      } catch (error) {
        this.loadingError = error?.response?.data?.detail || 'Error fetching definition settings'
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
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
