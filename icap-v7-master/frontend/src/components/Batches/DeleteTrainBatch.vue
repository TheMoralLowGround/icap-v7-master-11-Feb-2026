<!--
 Organization: AIDocbuilder Inc.
 File: deleteTrainBatch.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   The `deleteBatches.vue` component provides a modal for deleting one or multiple batches.
   It allows users to confirm deletion, optionally remove batch files from disk, and displays
   a success or error message via toast notifications.

 Features:
   - Modal for confirming the deletion of one or more batches.
   - Option to delete batch files from disk with a checkbox.
   - Displays a loading spinner on the delete button during the deletion process.
   - Toast notifications on success or failure of the delete action.
   - Emits a custom `deleted` event upon successful deletion to notify parent components.

 Dependencies:
   - `axios`: For making HTTP requests to delete batches.
   - `bootstrap-vue`: For modal, buttons, form checkboxes, and spinner components.
   - `ToastificationContent`: For displaying custom toast notifications on success or failure.

 Key Data Properties:
   - `showModal`: A boolean that controls the visibility of the modal.
   - `isDeleting`: A boolean that indicates whether the deletion is in progress.

 Notes:
   - The `b-modal` component from Bootstrap Vue is used to display the deletion confirmation dialog.
   - The modal footer contains two buttons: Cancel and Delete, with the Delete button showing a loading spinner
     while the deletion is in progress.
   - The `ToastificationContent` component is used to show success or error messages based on the result
     of the deletion API request.
-->

<template>
  <!-- Modal for delete train batch -->
  <b-modal
    v-model="showModal"
    centered
    title="Delete Train Batch"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      <div v-if="ids.length === 1">
        Are you sure you want to delete the train batch <span class="text-primary">{{ ids[0] }}</span>?
      </div>
      <div v-else>
        Are you sure you want to delete the following train batches?
        <div
          v-for="(id, index) of ids"
          :key="index"
          class="text-primary"
        >
          {{ id }}
        </div>
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
        variant="danger"
        :disabled="isDeleting"
        @click="ok()"
      >
        Delete
        <b-spinner
          v-if="isDeleting"
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
  BModal, BCardText, BButton, BSpinner,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
  },
  props: {
    ids: {
      type: Array,
      required: true,
    },
    isProfileTraining: {
      type: Boolean,
      required: false,
    },
  },
  data() {
    return {
      showModal: true,
      isDeleting: false,
    }
  },
  methods: {
    // Confirm handler for delete train batch
    confirmHandler(event) {
      event.preventDefault()
      let data = {}
      this.isDeleting = true
      let endpoint = '/train-batches/delete_multiple/'
      if (this.isProfileTraining) {
        endpoint = '/delete_from_profile_training/'
        data = { batch_ids: this.ids }
      } else {
        data = { ids: this.ids }
      }
      axios.delete(endpoint, { data })
        .then(() => {
          this.$emit('deleted')

          this.$toast({
            component: ToastificationContent,
            props: {
              title: this.ids.length === 1 ? 'Train Batch deleted sucessfully' : 'Train Batches deleted sucessfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.showModal = false
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Somthing went wrong',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          this.isDeleting = false
        })
    },
  },
}

</script>
