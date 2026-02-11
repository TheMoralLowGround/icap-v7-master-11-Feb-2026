<template>
  <b-modal
    :id="id"
    v-model="isVisible"
    :title="title"
    ok-title="Delete"
    ok-variant="danger"
    cancel-title="Cancel"
    centered
    @ok="handleDelete"
    @hidden="handleHidden"
  >
    Are you sure you want to delete this record?
  </b-modal>
</template>

<script>
import {
  BModal,
} from 'bootstrap-vue'

export default {
  name: 'DeleteModal',
  components: {
    BModal,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    id: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: 'Confirm Delete Dictionary',
    },
    item: {
      type: Object,
      default: () => ({}),
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
    handleDelete() {
      this.$emit('delete')
    },
    handleHidden() {
      this.$emit('close')
    },
  },
}
</script>
