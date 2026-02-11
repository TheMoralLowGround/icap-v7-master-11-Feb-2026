<!--
 Organization: AIDocbuilder Inc.
 File: ReProcessBatch.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   The `ReProcessBatch.vue` component provides a modal for reprocessing one or multiple batches.
   It allows users to select the reprocessing type (all or extraction) and confirms their choice to
   trigger the reprocessing action. Upon confirmation, the component sends a request to reprocess the batches
   and displays success or error messages via toast notifications.

 Features:
   - Modal for confirming reprocessing of one or more batches.
   - Radio button group for selecting the reprocessing type: "All" or "Extraction".
   - Displays a confirmation message with the selected batch IDs.
   - Displays a loading spinner on the "Re-Process" button during the reprocessing action.
   - Toast notifications for success or failure of the reprocessing request.
   - Emits a custom `completed` event upon successful reprocessing to notify parent components.
   - Disables "All" option and defaults to "Extraction" when any ID starts with "multi_".

 Dependencies:
   - `axios`: For making HTTP requests to trigger the batch reprocessing.
   - `bootstrap-vue`: For modal, buttons, radio groups, and spinner components.
   - `ToastificationContent`: For displaying custom toast notifications on success or failure.

 Notes:
   - The modal footer contains two buttons: Cancel and Re-Process, with the Re-Process button showing a loading spinner
     while the reprocessing is in progress.
   - The `ToastificationContent` component is used to show success or error messages based on the result
     of the reprocessing request.
   - When any batch ID starts with "multi_", only "Extraction" option is available and selected by default.
-->

<template>
  <!-- A Bootstrap modal component with reprocessing options -->
  <b-modal
    v-model="showModal"
    centered
    :title="title"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      <!-- A radio button group for selecting the reprocessing type -->
      <div class="d-flex justify-content-center">
        <b-form-group class="pt-1">
          <b-form-radio-group
            v-model="reprocessType"
            class="custom-radio-width"
            size="small"
            button-variant="outline-primary"
            :options="reprocessOptions"
            buttons
          />
        </b-form-group>
      </div>

      <!-- Displays the confirmation message and IDs based on the number of items -->
      <div v-if="ids.length === 1">
        {{ message }} <span class="text-primary">{{ ids[0] }}</span>?
      </div>
      <div v-else>
        {{ message }}
        <div
          v-for="(id, index) of ids"
          :key="index"
          class="text-primary"
        >
          {{ id }}
        </div>
      </div>
    </b-card-text>

    <!-- Custom footer template for the modal -->
    <template #modal-footer="{ ok, cancel }">
      <!-- Cancel button -->
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <!-- Re-Process button -->
      <b-button
        variant="primary"
        :disabled="isProcessing"
        @click="ok()"
      >
        Re-Process
        <b-spinner
          v-if="isProcessing"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import axios from 'axios'
import {
  BModal, BCardText, BButton, BSpinner, BFormRadioGroup, BFormGroup,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
    BFormRadioGroup,
    BFormGroup,
  },
  props: {
    title: {
      type: String,
      required: true, // Title for the modal, required prop
    },
    message: {
      type: String,
      default: 'Are you sure you want to re-process the following batches?', // Default confirmation message
    },
    ids: {
      type: Array,
      required: true, // List of batch IDs to reprocess, required prop
    },
    templateName: {
      type: String,
      required: false, // Optional template name for the payload
      default: '',
    },
    apiUrl: {
      type: String,
      default: '/pipeline/re_process_extraction/', // Default API endpoint for reprocessing
    },
  },
  data() {
    return {
      showModal: true, // Controls the modal visibility
      isProcessing: false, // Indicates if the reprocessing action is ongoing
    }
  },
  computed: {
    currentRouteName() {
      return this.$route.name // Gets the current route name
    },

    // Check if any ID starts with "multi_"
    hasMultiIds() {
      return this.ids.some(id => id.startsWith('multi_'))
    },

    // Dynamic reprocess type based on whether multi_ IDs are present
    reprocessType: {
      get() {
        return this.hasMultiIds ? 'extraction' : this.$data.reprocessTypeInternal || 'all'
      },
      set(value) {
        this.$data.reprocessTypeInternal = value
      },
    },

    // Dynamic options for the radio group
    reprocessOptions() {
      return [
        {
          text: 'All',
          value: 'all',
          disabled: this.hasMultiIds, // Disable "All" option when multi_ IDs are present
        },
        {
          text: 'Extraction',
          value: 'extraction',
        },
      ]
    },
  },

  // Initialize the internal reprocess type
  created() {
    this.$set(this.$data, 'reprocessTypeInternal', this.hasMultiIds ? 'extraction' : 'all')
  },

  methods: {
    confirmHandler(event) {
      event.preventDefault()
      this.isProcessing = true // Starts the processing indicator

      const payload = {
        ids: this.ids, // List of batch IDs
        reprocess_type: this.reprocessType, // Selected reprocessing type
      }
      if (this.currentRouteName === 'templates') {
        payload.template_name = this.templateName // Adds template name if on the templates route
      }

      // Sends the reprocessing request
      axios.post(this.apiUrl, payload)
        .then(() => {
          this.$emit('completed') // Emits a completed event on success

          // Displays a success toast notification
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Batches Queued for re-processing',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.showModal = false // Closes the modal
        })
        .catch(error => {
          // Displays an error toast notification
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Something went wrong',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          this.isProcessing = false // Stops the processing indicator
        })
    },
  },
}

</script>

<style lang="scss">
  .custom-radio-width .btn {
    min-width: 95px;
  }

  // Style for disabled radio buttons
  .custom-radio-width .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
