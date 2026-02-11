<!--
 Organization: AIDocbuilder Inc.
 File: TestOptions.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-04

 Description:
   This component provides an interface for initiating test actions and configuring test options. The component
   contains buttons to run either a batch test or a document test, with spinners to indicate the test status.
   Additionally, it includes a dropdown menu for configuring test options, such as skipping post-processing, key
   processing, or table processing. It communicates with Vuex to store and sync test options, and interacts with
   the backend API to run the selected tests.

 Main Features:
   - Provides buttons for running batch or document tests with associated spinners for progress indication.
   - Includes a dropdown menu for configuring test options with checkboxes for skipping processing steps.
   - Syncs test options with the Vuex store to persist the configurations across sessions.
   - Sends a POST request to the backend to run the selected test with the configured options.

 Dependencies:
   - Bootstrap Vue: For button, spinner, dropdown, and form components
   - Vuex: For managing the state of test options and batch/document data
   - Axios: For sending requests to the backend API to trigger tests
   - Toastification: For displaying success or error messages after test completion
   - Lodash: For deep comparison and cloning of test options

 Notes:
   - The component listens for changes in the `testOptions` and Vuex store to ensure that the test options are always up-to-date.
   - When a test is run, the component sends a request to the backend with the current test options and selected test mode.
   - Error handling and toast notifications are included to notify the user about the test result.
-->

<template>
  <!-- Button group containing test actions and a dropdown for test options -->
  <b-button-group>
    <!-- Button to run a set test (all batches in transaction) -->
    <b-button
      variant="outline-primary"
      :class="[customVariantClass]"
      :disabled="runningTransaction || runningTestBatch || runningTestDocument"
      @click="runTest('transaction')"
    >
      {{ testTransactionTitle }}
      <!-- Spinner to indicate set test is in progress -->
      <b-spinner
        v-if="runningTransaction"
        small
        label="Small Spinner"
      />
    </b-button>
    <b-button
      variant="outline-primary"
      :class="[customVariantClass]"
      :disabled="runningTransaction || runningTestBatch || runningTestDocument"
      @click="runTest('batch')"
    >
      {{ testBatchTitle }}
      <!-- Spinner to indicate batch test is in progress -->
      <b-spinner
        v-if="runningTestBatch"
        small
        label="Small Spinner"
      />
    </b-button>

    <!-- Button to run a document test -->
    <b-button
      variant="outline-primary"
      :class="[customVariantClass]"
      :disabled="runningTransaction || runningTestBatch || runningTestDocument"
      @click="runTest('document')"
    >
      {{ testDocumentTitle }}
      <!-- Spinner to indicate document test is in progress -->
      <b-spinner
        v-if="runningTestDocument"
        small
        label="Small Spinner"
      />
    </b-button>

    <!-- Dropdown for additional test options -->
    <b-dropdown
      right
      variant="outline-primary"
      :disabled="runningTransaction || runningTestBatch || runningTestDocument"
      no-caret
      size="sm"
      :class="{'custom-dropdown-btn': customVariantClass === 'btn-xs'}"
    >
      <!-- Dropdown button content with an icon -->
      <template #button-content>
        <feather-icon
          icon="ChevronDownIcon"
          :size="customVariantClass === 'btn-xs' ? '14' : '20'"
        />
      </template>
      <!-- Dropdown form containing test options -->
      <b-dropdown-form :style="{ width: customVariantClass === 'btn-xs' ? '170px' : '250px' }">
        <!-- Checkbox to skip post-processing during testing -->
        <b-form-group>
          <b-form-checkbox
            v-model="testOptions.skipPostProcessor"
            v-b-tooltip.hover.top="{boundary:'window'}"
            class="cursor-pointer"
          >
            Skip Post-Processor
          </b-form-checkbox>
        </b-form-group>

        <!-- Checkbox to skip key processing during testing -->
        <b-form-group>
          <b-form-checkbox
            v-model="testOptions.skipKeyProcessing"
            class="cursor-pointer"
          >
            Skip Key Processing
          </b-form-checkbox>
        </b-form-group>

        <!-- Checkbox to skip table processing during testing -->
        <b-form-group>
          <b-form-checkbox
            v-model="testOptions.skipTableProcessing"
            class="cursor-pointer"
          >
            Skip Table Processing
          </b-form-checkbox>
        </b-form-group>
      </b-dropdown-form>
    </b-dropdown>
  </b-button-group>
</template>

<script>
import {
  BDropdown, BDropdownForm, BFormGroup, BButton, BSpinner, BButtonGroup, BFormCheckbox, VBTooltip,
} from 'bootstrap-vue'
import axios from 'axios'
import { isEqual, cloneDeep } from 'lodash'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BDropdown,
    BDropdownForm,
    BFormGroup,
    BButton,
    BSpinner,
    BButtonGroup,
    BFormCheckbox,
  },
  props: {
    testTransactionTitle: {
      type: String,
      default: 'Test Batch',
    },
    testBatchTitle: {
      type: String,
      default: 'Test Set',
    },
    testDocumentTitle: {
      type: String,
      default: 'Test Document',
    },
    customVariantClass: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      runningTransaction: false, // Indicates if the "set" test is currently running
      runningTestBatch: false, // Indicates if the "batch" test is currently running
      runningTestDocument: false, // Indicates if the "document" test is currently running
      testOptions: {}, // Holds the test options such as processing skips
    }
  },
  computed: {
    storeTestOptions() {
      // Retrieves the test options from the Vuex store
      return this.$store.getters['batch/testOptions']
    },
    currentRouteName() {
      // Gets the current route's name
      return this.$route.name
    },
  },
  watch: {
    testOptions: {
      deep: true, // Deep watcher to monitor nested changes in `testOptions`
      handler() {
        // Syncs the local `testOptions` with the Vuex store when changes occur
        this.setTestOptions()
      },
    },
    storeTestOptions: {
      deep: true, // Deep watcher to monitor nested changes in the store's test options
      handler() {
        // Loads test options from the Vuex store when they change
        this.loadTestOptions()
      },
    },
  },
  created() {
    // Lifecycle hook to load initial test options from the Vuex store
    this.loadTestOptions()
  },
  methods: {
    loadTestOptions() {
      // Compares local `testOptions` with the store's test options and updates if necessary
      if (!isEqual(this.testOptions, this.storeTestOptions)) {
        this.testOptions = cloneDeep(this.storeTestOptions) // Deep copy to avoid direct mutations
      }
    },
    setTestOptions() {
      // Syncs local `testOptions` back to the Vuex store if there are changes
      if (!isEqual(this.testOptions, this.storeTestOptions)) {
        this.$store.commit('batch/SET_TEST_OPTIONS', cloneDeep(this.testOptions)) // Commits the updates
      }
    },
    runTest(mode) {
      // Determines whether to run a batch test, document test, or set test
      let flagname
      if (mode === 'document') {
        flagname = 'runningTestDocument'
      } else if (mode === 'transaction') {
        flagname = 'runningTransaction'
      } else {
        flagname = 'runningTestBatch'
      }
      this[flagname] = true // Sets the corresponding running flag to true

      // Retrieves necessary data from the Vuex store for the test
      const batch = this.$store.getters['batch/batch']
      const documentId = this.$store.getters['batch/selectedDocumentId']
      const selectedDefinitionVersion = this.$store.getters['dataView/selectedDefinitionVersion']
      const params = {
        skip_post_processor: this.testOptions.skipPostProcessor, // Skip post-processing if selected
        skip_key_processing: this.testOptions.skipKeyProcessing, // Skip key processing if selected
        skip_table_processing: this.testOptions.skipTableProcessing, // Skip table processing if selected
        definition_version: selectedDefinitionVersion, // Selected definition version for processing
      }

      if (mode === 'transaction') {
        // For set mode, send all batch IDs from the transaction
        // const transaction = this.$store.getters['batch/transaction']
        // const batchIds = transaction?.batches?.map(b => b.id) || []
        const batchIds = this.$store.getters['batch/batchesIds'] || []
        params.batch_ids = JSON.stringify(batchIds) // Send as JSON array
      } else {
        // For batch or document mode, send single batch_id
        params.batch_id = batch.id
      }

      if (mode === 'document') {
        // Adds document ID if the test is for a document
        params.document_id = documentId
      }
      if (this.currentRouteName === 'template-batch') {
        // Includes the template ID if on the "template-batch" route
        params.template = batch.definitionId
      }

      // Sends a POST request to run the test with the specified parameters
      axios.post('/pipeline/process_batch/', null, {
        params,
      }).then(res => {
        this.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
        this[flagname] = false
      }).catch(error => {
        const message = error?.response?.data?.detail || 'Something went wrong'
        this.$toast({
          component: ToastificationContent,
          props: {
            title: message,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        this[flagname] = false
      })
    },
  },
}
</script>

<style scoped>
.cursor-pointer >>> * {
  cursor: pointer !important;
}

.btn {
  padding: 0.75rem !important;
  font-size: 12px;
}

.btn-xs {
  padding: 0.125rem 0.75rem !important;
  font-size: 0.85rem;
  line-height: 1.2;
  border-radius: 0.2rem;
}

.custom-dropdown-btn >>> .btn-sm {
  padding: 0.486rem .3rem !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.custom-dropdown-btn >>> .b-dropdown-form {
  padding: 0.5rem;
  padding-bottom: 0;
  padding-left: 0.65rem;
}

/* Make checkboxes and text smaller when btn-xs */
.custom-dropdown-btn >>> .custom-control {
  font-size: 0.95rem !important; /* Smaller text */
  margin-bottom: 0.35rem !important; /* Less spacing */
}

.custom-dropdown-btn >>> .custom-control-input {
  width: 1rem !important;
  height: 1rem !important;
}

.custom-dropdown-btn >>> .custom-control-label::before {
  width: 1rem !important;
  height: 1rem !important;
  /* top: 0.1rem !important; */
}

.custom-dropdown-btn >>> .custom-control-label::after {
  width: 1rem !important;
  height: 1rem !important;
  top: 0.1rem !important;
}

.custom-dropdown-btn >>> .custom-control {
  min-height: 1.4rem !important; /* Increase container height */
  padding-left: 1.5rem !important; /* Increase left padding */
}

.custom-dropdown-btn >>> .custom-control-label {
  font-size: 0.85rem !important;
  line-height: 1.4 !important;
  padding-left: 0.20rem !important; /* Adjust spacing */
}

.custom-dropdown-btn >>> .form-group {
  margin-bottom: 0.15rem !important;
}
</style>
