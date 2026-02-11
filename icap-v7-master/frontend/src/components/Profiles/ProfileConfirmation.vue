<template>
  <b-modal
    v-model="showModal"
    centered
    title="Template Update"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      One or more templates will be updated? Existing definitions will be lost. Confirm?
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
        @click="ok()"
      >
        Confirm
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BModal, BCardText, BButton,
} from 'bootstrap-vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
  },
  data() {
    return {
      showModal: true,
    }
  },
  methods: {
    confirmHandler() {
      this.$emit('submit')
      this.showModal = false
    },
  },
}

</script>
