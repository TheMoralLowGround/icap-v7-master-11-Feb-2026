<template>
  <b-row>
    <b-col
      cols="12"
      sm="6"
      class="d-flex align-items-center justify-content-center justify-content-sm-start"
    >
      <span class="text-muted">Showing {{ displayingFrom }} to {{ displayingTo }} of {{ totalRecords }} entries</span>
    </b-col>

    <b-col
      cols="12"
      sm="6"
      class="d-flex align-items-center justify-content-center justify-content-sm-end"
    >
      <b-pagination
        :value="currentPage"
        :total-rows="totalRecords"
        :per-page="perPage"
        first-number
        last-number
        class="mb-0 mt-1 mt-sm-0"
        prev-class="prev-item"
        next-class="next-item"
        @change="pageChanged"
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
    </b-col>
  </b-row>
</template>

<script>
import { BPagination, BRow, BCol } from 'bootstrap-vue'

export default {
  components: {
    BRow,
    BCol,
    BPagination,
  },
  props: {
    perPage: {
      type: Number,
      required: true,
    },
    currentPage: {
      type: Number,
      required: true,
    },
    totalRecords: {
      type: Number,
      required: true,
    },
    localRecords: {
      type: Number,
      required: true,
    },
  },
  computed: {
    displayingFrom() {
      return this.perPage * (this.currentPage - 1) + (this.localRecords ? 1 : 0)
    },
    displayingTo() {
      return this.perPage * (this.currentPage - 1) + this.localRecords
    },
  },
  methods: {
    pageChanged(page) {
      this.$emit('page-changed', page)
    },
  },
}
</script>
