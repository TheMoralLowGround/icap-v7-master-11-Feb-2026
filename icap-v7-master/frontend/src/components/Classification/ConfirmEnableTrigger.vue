<template>
  <b-modal
    v-model="showModal"
    centered
    title="Pick trigger"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      There Name matching classified value. Are you sure to pick trigger?
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
        Confirm
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
    async confirmHandler() {
      this.isDeleting = false
      this.$emit('confirmed')
      this.showModal = false
    },
  },
}

</script>
