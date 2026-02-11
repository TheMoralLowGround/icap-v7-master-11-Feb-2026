<template>
  <b-modal
    v-model="showModal"
    centered
    title="Submit Classifications"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      Are you sure you want to submit modified classification data?
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
        :disabled="isDeleting"
        @click="ok()"
      >
        Submit
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
import {
  BModal, BCardText, BButton, BSpinner,
} from 'bootstrap-vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
  },
  props: {
  },
  data() {
    return {
      showModal: true,
      isDeleting: false,
    }
  },
  methods: {
    async confirmHandler(event) {
      event.preventDefault()

      this.isDeleting = true

      const batchId = this.$route.params.id
      const isSucess = await this.$store.dispatch('classifications/verifyClassification', {
        train_batch_id: batchId,
        forceSubmit: false,
      })
      if (isSucess) {
        this.isDeleting = false
        this.$emit('submited')
        this.$router.push({ name: 'training' })
        this.showModal = false
      }
    },
  },
}

</script>
