<template>
  <b-modal
    v-model="showModal"
    title="Import Definitions"
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form @submit.prevent="onSubmit">
      <b-form-group
        label="Definitions JSON File"
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

      <div v-if="fileLoaded">
        <definitions-list
          v-if="newDefinitions.length > 0"
          :definitions="newDefinitions"
          mode="new"
        />
        <definitions-list
          v-if="existingDefinitions.length > 0"
          :definitions="existingDefinitions"
          mode="existing"
        />

        <div v-if="existingDefinitions.length > 0">
          <p class="mb-25">
            Update Settings
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
              <b-form-checkbox
                v-model="updateSettings[updateSettingIndex].key"
              >
                Update Key Settings
              </b-form-checkbox>
              <b-form-checkbox
                v-model="updateSettings[updateSettingIndex].table"
              >
                Update Table Settings
              </b-form-checkbox>
            </div>
          </div>
        </div>
      </div>
    </b-form>

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
        :disabled="submitting || !enableSubmit"
        @click="ok()"
      >
        Submit
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
  BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormCheckbox, BFormFile,
} from 'bootstrap-vue' // Importing required Bootstrap Vue components
import axios from 'axios' // Importing Axios for HTTP requests

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue' // Importing custom toast notification component
import DefinitionsList from './DefinitionsList.vue' // Importing a local component for displaying a list of definitions

export default {
  components: {
    BFormGroup, // Used for grouping form fields
    BButton, // Used for buttons
    BForm, // Used for forms
    BSpinner, // Used for displaying loading spinners
    BAlert, // Used for alerts
    BModal, // Used for modal dialogs
    BFormCheckbox, // Used for checkboxes in forms
    BFormFile, // Used for file inputs in forms
    DefinitionsList, // Custom component to display definitions
  },
  data() {
    return {
      definitionsFile: null, // Stores the uploaded definitions file
      definitions: [], // Array to hold parsed definitions data
      updateSettings: [], // Array to hold update settings for existing definitions
      loadingFile: false, // Boolean to indicate whether the file is being loaded
      fileLoaded: false, // Boolean to indicate whether the file has been successfully loaded
      fileLoadError: null, // Error message for file loading errors
      submitting: false, // Boolean to indicate whether the form is being submitted
      showModal: true, // Boolean to control the visibility of a modal dialog
    }
  },
  computed: {
    definitionVersions() {
      // Fetches definition versions from Vuex store
      return this.$store.getters['applicationSettings/definitionVersions']
    },
    newDefinitions() {
      // Filters definitions to get only the new ones (non-existing)
      return this.definitions.filter(definition => !definition.exists)
    },
    existingDefinitions() {
      // Filters definitions to get only the existing ones
      return this.definitions.filter(definition => definition.exists)
    },
    enableSubmit() {
      // Enables the submit button if there are new or existing definitions
      return this.newDefinitions.length > 0 || this.existingDefinitions.length > 0
    },
  },
  watch: {
    existingDefinitions() {
      // Resets update settings if there are no existing definitions
      if (this.existingDefinitions.length === 0) {
        this.resetUpdateSettings()
      }
    },
  },
  created() {
    // Resets update settings when the component is created
    this.resetUpdateSettings()
  },
  methods: {
    // Resets the update settings array to default values based on definition versions
    resetUpdateSettings() {
      this.updateSettings = this.definitionVersions.map(definitionVersion => ({
        version: definitionVersion, // Version of the definition
        key: false, // Indicates if the "key" setting is enabled
        table: false, // Indicates if the "table" setting is enabled
      }))
    },

    // Handles loading and parsing the uploaded file, and fetching the status of definitions
    async loadFile() {
      this.fileLoaded = false // Reset the file loaded state

      if (!this.definitionsFile) {
        // If no file is uploaded, reset related properties and return
        this.definitions = []
        this.fileLoadError = null
        return
      }

      this.loadingFile = true // Indicate that the file is being loaded

      this.parseDefinitions() // Parse the uploaded file
        .then(definitions => this.fetchDefinitionsStatus(definitions)) // Fetch definitions' statuses from the server
        .then(definitions => {
          this.definitions = definitions // Store the parsed and status-checked definitions
          this.fileLoadError = null // Clear any previous file load error
          this.fileLoaded = true // Mark the file as successfully loaded
          this.loadingFile = false // Stop the loading spinner
        })
        .catch(error => {
          // Handle any errors during file parsing or status fetching
          this.definitions = []
          this.fileLoadError = error.message // Store the error message
          this.loadingFile = false
        })
    },

    // Parses the definitions file into a JSON object
    parseDefinitions() {
      return new Promise((resolve, reject) => {
        const reader = new FileReader() // Create a FileReader instance
        reader.onload = event => {
          const data = event.target.result // Get the file contents
          try {
            const definitions = JSON.parse(data) // Attempt to parse the file as JSON
            resolve(definitions) // Resolve with the parsed definitions
          } catch (error) {
            reject(error) // Reject if JSON parsing fails
          }
        }
        reader.readAsText(this.definitionsFile) // Read the file as text
      })
    },

    // Fetches the existence status of definitions from the server
    async fetchDefinitionsStatus(definitions) {
      // Map definitions to their IDs and types for the API request
      const definitionDetails = definitions.map(definition => ({
        definition_id: definition.definition_id,
        type: definition.type,
      }))

      let res
      try {
        // Make a POST request to check if the definitions already exist
        res = await axios.post('/pipeline/check_definitions_exist/', {
          definitions: definitionDetails,
        })
      } catch (error) {
        // Handle errors and throw a new error with a meaningful message
        const message = error?.response?.data?.detail || 'Error fetching definitions status'
        throw new Error(message)
      }

      // Process the API response to determine which definitions already exist
      const existingDefinitions = res.data.exist
      const newDefinitions = definitions.map(definition => {
        const matchingDefinition = existingDefinitions.find(existingDefinition => existingDefinition.definition_id === definition.definition_id && existingDefinition.type === definition.type)
        return {
          exists: !!matchingDefinition, // Mark as existing if a match is found
          ...definition, // Retain other properties of the definition
        }
      })

      return newDefinitions // Return the updated definitions with status
    },

    // Handles form submission to import definitions
    onSubmit(event) {
      event.preventDefault() // Prevent default form submission behavior
      this.submitting = true // Indicate that the form is being submitted

      // Prepare the definitions data for submission by removing the `exists` property
      const definitions = this.definitions.map(definition => {
        const newDefinition = {
          ...definition,
        }
        delete newDefinition.exists // Remove the `exists` property
        return newDefinition
      })

      // Make a POST request to import definitions and update settings
      axios.post('/pipeline/import_definitions/', {
        definitions,
        update_settings: this.updateSettings,
      })
        .then(res => {
          // Show a success toast notification
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail, // Use the response message as the title
              icon: 'CheckIcon', // Success icon
              variant: 'success', // Success variant
            },
          })
          this.submitting = false // Stop the submitting state
          this.$emit('imported') // Emit an event to notify the parent component
          this.showModal = null // Hide the modal
        })
        .catch(error => {
          // Show an error toast notification in case of failure
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error importing definitions', // Use error details or a default message
              icon: 'AlertTriangleIcon', // Error icon
              variant: 'danger', // Error variant
            },
          })
          this.submitting = false // Stop the submitting state
        })
    },
  },
}
</script>
