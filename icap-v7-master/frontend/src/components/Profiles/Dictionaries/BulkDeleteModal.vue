<template>
  <b-modal
    :id="id"
    v-model="isVisible"
    :title="title"
    :ok-title="okTitle"
    ok-variant="danger"
    cancel-title="Cancel"
    centered
    @ok="handleBulkDelete"
    @hidden="handleHidden"
  >
    <p>Are you sure you want to delete  selected records ?</p>
    <p class="text-danger mb-0">
      <small>This action cannot be undone.</small>
    </p>
  </b-modal>
</template>

<script>
import {
  BModal,
} from 'bootstrap-vue'

export default {
  name: 'BulkDeleteModal',
  components: {
    BModal,
  },
  props: {
    id: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
    okTitle: {
      type: String,
      default: 'Delete',
    },
    visible: {
      type: Boolean,
      default: false,
    },
    count: {
      type: Number,
      default: 0,
    },
  },
  computed: {
    isVisible: {
      get() {
        return this.visible
      },
      set(val) {
        if (!val) {
          this.$emit('close')
        }
      },
    },
  },
  methods: {
    handleBulkDelete() {
      this.$emit('delete')
    },
    handleHidden() {
      this.$emit('close')
    },
  },
}
</script>
