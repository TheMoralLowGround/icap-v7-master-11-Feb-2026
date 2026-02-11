<template>
  <b-modal
    v-model="showModal"
    centered
    :title="`${undo ? 'Undo' : 'Add'} Mapped Key To Project`"
    @ok="confirmHandler"
    @hidden="$emit('modal-closed')"
    @cancel="$emit('cancel')"
    @close="$emit('close')"
  >
    <b-card-text>
      Are you sure you want to{{ undo ? ' undo' : '' }} map '{{ draggedItemLable }}' to the project key '{{ dropTargetLabel }}' ?
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
        :disabled="submiting"
        @click="ok()"
      >
        {{ undo ? 'Undo Mapping' : 'Map' }}
        <b-spinner
          v-if="submiting"
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
    draggedItemLable: {
      type: String,
      required: true,
    },
    dropTargetLabel: {
      type: String,
      required: true,
    },
    undo: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showModal: true,
      submiting: false,
    }
  },
  methods: {
    async confirmHandler() {
      this.submiting = false
      this.$emit('confirmed')
      this.showModal = false
    },
  },
}

</script>
