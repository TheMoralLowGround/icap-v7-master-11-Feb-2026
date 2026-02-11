<template>
  <b-modal
    v-model="showDialog"
    title="Upload File"
    size="lg"
    centered
    no-close-on-backdrop
    :busy="submitting"
    @ok="submitHandler"
    @hidden="closeDialog"
  >

    <template #modal-ok>
      <span>
        Upload
        <b-spinner
          v-if="submitting"
          small
        />
      </span>
    </template>
    <div class="d-flex flex-column gap-y-6">
      <b-form-group label="File Type">
        <b-form-radio-group
          v-model="selectedType"
          buttons
          button-variant="outline-primary"
        >
          <b-form-radio value=".eml, .msg">
            Email
          </b-form-radio>
          <b-form-radio value=".pdf">
            Pdf
          </b-form-radio>
          <b-form-radio value=".doc, .docx">
            Doc
          </b-form-radio>
          <b-form-radio value=".xls, .xlsx">
            Excel
          </b-form-radio>
          <b-form-radio value=".csv">
            CSV
          </b-form-radio>
        </b-form-radio-group>
      </b-form-group>

      <v-select
        ref="vSelect"
        v-model="selectedProfile"
        :options="profiles"
        :reduce="profile => profile"
        label="name"
        :placeholder="`Select Process${selectedType === '.eml, .msg' ? ' (optional)' : ''}`"
        :clearable="true"
        :rules="[selectedType !== '.eml, .msg' ? requiredValidator : null]"
        @open="scrollToSelected(profiles, selectedProfile)"
      />

      <div class="d-flex align-items-center">
        <feather-icon
          icon="PaperclipIcon"
          class="cursor-pointer mr-1"
          size="17"
          @click="$refs.fileInput.$el.querySelector('input[type=file]').click()"
        />
        <b-form-file
          ref="fileInput"
          v-model="selectedFile"
          :placeholder="`Upload (${selectedType})`"
          :accept="selectedType"
          :clearable="true"
          multiple
          class="mr-1"
        />
      </div>
      <b-alert
        v-if="errorMessage"
        variant="danger"
        show
      >
        {{ errorMessage }}
      </b-alert>
    </div>
    <!-- <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="isUploading"
        @click="ok()"
      >
        Upload
        <b-spinner
          v-if="isUploading"
          small
          label="Small Spinner"
        />
      </b-button>
    </template> -->
  </b-modal>
</template>

<script>
import {
  BFormGroup, BModal, BFormFile,
  BAlert, BFormRadioGroup, BFormRadio,
  BSpinner,
} from 'bootstrap-vue'

import axios from 'axios'
import vSelect from 'vue-select'
import 'vue-select/dist/vue-select.css'

export default {
  components: {
    vSelect,
    BFormGroup,
    BModal,
    BFormFile,
    BAlert,
    BFormRadioGroup,
    BFormRadio,
    BSpinner,
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showDialog: true,
      errorMessage: '',
      submitting: false,
      selectedFile: null,
      selectedType: '.eml, .msg',
      profiles: [],
      selectedProfile: null,
      requiredValidator: value => {
        if (value) return true
        return 'Please select a process before uploading.'
      },
    }
  },
  computed: {
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    projectCountries() {
      const result = {}

      this.selectedProjectCountries.forEach(e => {
        const { countryCode, project } = e

        if (!result[countryCode]) {
          result[countryCode] = []
        }

        if (!result[countryCode].includes(project)) {
          result[countryCode].push(project)
        }
      })

      return result
    },
  },
  mounted() {
    this.fetchProfiles()
  },
  methods: {
    async submitHandler(bvModalEvt) {
      bvModalEvt.preventDefault()

      if (!this.selectedFile || this.selectedFile.length === 0) {
        this.errorMessage = 'Please select at least one file before uploading.'
        return
      }

      if (!this.selectedProfile && this.selectedType !== '.eml, .msg') {
        this.errorMessage = 'Please select a process before uploading.'
        return
      }

      this.submitting = true
      this.errorMessage = ''

      const formData = new FormData()

      const filesArray = Array.isArray(this.selectedFile)
        ? this.selectedFile
        : [this.selectedFile]

      try {
        // Only append profile if selected
        if (this.selectedProfile) {
          formData.append('profile_name', this.selectedProfile)
        }
        formData.append('file_type', this.getUploadFileType())

        const endpoint = '/pipeline/upload_email_batch/'

        const fieldName = 'files'

        filesArray.forEach(file => {
          formData.append(fieldName, file)
        })

        const res = await axios.post(endpoint, formData)

        if (res?.status === 200 && res?.data?.detail) {
          this.$bvToast.toast(res.data.detail, {
            title: 'Success',
            variant: 'success',
            solid: true,
          })
          this.$emit('uploaded')
          this.closeDialog()
        } else {
          this.errorMessage = res?.data?.detail || 'Unexpected response from server.'
        }
      } catch (error) {
        this.errorMessage = error?.response?.data?.detail || 'Error uploading files'
      } finally {
        this.submitting = false
      }
    },
    async fetchProfiles() {
      try {
        const res = await axios.post('/dashboard/profiles/filter_list/', { project_countries: this.projectCountries }, {
          params: {
            paginate: false,
          },
        })
        this.profiles = res.data?.map(p => p.name)
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error(error)
      }
    },
    toggleRecordsSelection(checked) {
      this.selectedProfile = checked ? this.profiles.map(profile => profile.id) : []
    },
    getUploadFileType() {
      const fileTypeObj = {
        '.eml, .msg': 'email',
        '.pdf': 'pdf',
        '.xls, .xlsx': 'excel',
        '.doc, .docx': 'word',
        '.csv': 'csv',
      }

      if (fileTypeObj[this.selectedType]) {
        return fileTypeObj[this.selectedType]
      }

      // if (this.selectedType === '.eml, .msg') {
      //   return 'email'
      // }

      // if (this.selectedType === '.pdf') {
      //   return 'pdf'
      // }

      // if (this.selectedType === '.xls, .xlsx') {
      //   return 'excel'
      // }

      // if (this.selectedType === '.doc, .docx') {
      //   return 'word'
      // }

      // if (this.selectedType === '.csv') {
      //   return 'csv'
      // }

      return ''
    },
    closeDialog() {
      this.showDialog = false
      this.$emit('modal-closed')
      this.resetForm()
    },
    resetForm() {
      this.selectedFile = null
      this.selectedProfile = null
      this.errorMessage = ''
      this.selectedType = '.eml, .msg'
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

        // Find the index of the selected value
        const selectedIndex = options?.indexOf(selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(dropdownMenuItems, selectedIndex)
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';

.gap-y-6 > * + * {
  margin-top: 1.5rem;
}
</style>
