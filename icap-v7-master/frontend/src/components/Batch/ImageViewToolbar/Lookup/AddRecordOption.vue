<template>
  <div>
    <feather-icon
      v-b-tooltip.hover
      icon="PlusIcon"
      size="20"
      class="cursor-pointer"
      title="Add Record"
      @click="addRecord"
    />
    <record-form
      v-if="showModal"
      :is-edit="false"
      @modal-closed="showModal = false"
    />
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import RecordForm from '@/components/Lookup/RecordForm.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    RecordForm,
  },
  data() {
    return {
      showModal: false,
    }
  },
  methods: {
    addRecord() {
      this.showModal = true
    },
  },
}
</script>
