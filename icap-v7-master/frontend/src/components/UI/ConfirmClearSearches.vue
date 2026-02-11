<template>
  <b-modal
    v-model="showModal"
    centered
    title="Clear Search"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      Are you sure you want to clear all searches ?
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
        Clear
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
  props: {
    value: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
    }
  },
  methods: {
    async confirmHandler(event) {
      event.preventDefault()

      const resetSearchBy = Object.fromEntries(
        Object.keys(this.value).map(key => [key, key === 'extension_type' ? 'all' : null]),
      )

      this.$emit('input', resetSearchBy)
      this.$emit('submited')

      this.showModal = false
    },
  },
}

</script>
