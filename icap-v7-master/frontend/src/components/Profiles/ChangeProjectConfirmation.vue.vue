<template>
  <div>
    <b-modal
      :visible="value"
      :title="title"
      no-close-on-backdrop
      size="lg"
      centered
      ok-title="Continue"
      @ok="onSaveKey"
      @hidden="$emit('modal-closed')"
    >
      <div class="d-flex flex-column gap-y-3">
        If you change Project then you will lost all Available keys
      </div>
    </b-modal>
  </div>
</template>

<script>
import {
  BModal,
} from 'bootstrap-vue'

export default {
  components: {
    BModal,

  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: 'Add New Key',
    },
  },
  data() {
    return {
      errorMessage: null,
      items: [],
    }
  },

  methods: {

    onSaveKey() {
      this.$emit('save')
      this.$emit('modal-closed')
    },

  },
}
</script>

<style scoped>
.bg-light-danger {
  background-color: rgba(220, 53, 69, 0.1);
}
.text-muted {
  color: #6c757d;
}
</style>
