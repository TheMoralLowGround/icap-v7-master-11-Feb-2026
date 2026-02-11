<template>
  <div class="d-flex justify-content-between align-items-center mt-2">
    <div class="text-muted">
      Showing {{ localCountStart }} to {{ localCountEnd }} of {{ total }} entries
    </div>
    <div class="ml-auto pr-2">
      <slot />
    </div>
    <b-pagination
      v-model="currentPageInternal"
      :per-page="perPage"
      :total-rows="total"
      align="right"
      size="sm"
      first-number
      last-number
      class="my-auto"
      @input="emitPageChange"
    >
      <template #prev-text>
        <feather-icon
          icon="ChevronLeftIcon"
          size="18"
        />
      </template>
      <template #next-text>
        <feather-icon
          icon="ChevronRightIcon"
          size="18"
        />
      </template>
    </b-pagination>
  </div>
</template>

<script>
import { BPagination } from 'bootstrap-vue'

export default {
  name: 'LocalPagination',
  components: {
    BPagination,
  },
  props: {
    perPage: {
      type: Number,
      required: true,
    },
    total: {
      type: Number,
      required: true,
    },
    currentPage: {
      type: Number,
      default: 1,
    },
    localLength: {
      type: Number,
      default: 0,
    },
  },
  data() {
    return {
      currentPageInternal: this.currentPage,
    }
  },
  computed: {
    localCountStart() {
      return this.localLength ? (this.currentPageInternal - 1) * this.perPage + 1 : 0
    },
    localCountEnd() {
      return (this.currentPageInternal - 1) * this.perPage + this.localLength
    },
  },
  watch: {
    currentPage(val) {
      this.currentPageInternal = val
    },
  },
  methods: {
    emitPageChange(val) {
      this.$emit('page-changed', val)
    },
  },
}
</script>
