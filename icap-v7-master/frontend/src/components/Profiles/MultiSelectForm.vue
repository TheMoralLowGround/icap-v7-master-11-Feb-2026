<template>
  <div>
    <b-modal
      :visible="modelValue"
      :title="title"
      centered
      no-close-on-backdrop
      size="md"
      ok-title="Save"
      @ok="onSaveKey"
      @hidden="$emit('update:modelValue', false)"
    >
      <div class="d-flex flex-column gap-y-3">
        <div class="d-flex justify-content-end">
          <b-button
            v-if="options.length && items.length !== options.length"
            size="sm"
            variant="link"
            :class="{ 'mr-2': items.length }"
            @click="selectAll"
          >
            Select All
          </b-button>
          <b-button
            v-if="items.length"
            size="sm"
            variant="link"
            class="text-danger"
            @click="clearAll"
          >
            Clear
          </b-button>
        </div>
        <b-form-select
          v-model="items"
          :options="options"
          multiple
          :select-size="6"
          class="mb-3"
        >
          <template #first>
            <option
              disabled
              value=""
            >
              Select a Key
            </option>
          </template>
        </b-form-select>
      </div>
      <div
        v-if="errorMessage"
        class="my-4 px-4 py-2 bg-light-danger text-danger rounded"
      >
        {{ errorMessage }}
      </div>
    </b-modal>
  </div>
</template>

<script>
import {
  BModal,
  BButton,
  BFormSelect,
} from 'bootstrap-vue'

export default {
  components: {
    BModal,
    BButton,
    BFormSelect,
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    options: {
      type: Array,
      default: () => [],
    },
    selectedItems: {
      type: Array,
      default: () => [],
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
  watch: {
    selectedItems: {
      handler(newVal) {
        if (newVal) {
          this.items = [...this.selectedItems]
        }
      },
      immediate: true,
    },
    modelValue(newVal) {
      if (newVal) {
        this.items = [...this.selectedItems]
      }
    },
  },
  methods: {
    selectAll() {
      this.items = [...this.options]
    },
    clearAll() {
      this.items = []
    },
    onSaveKey() {
      this.$emit('save', this.items)
      this.$emit('update:modelValue', false)
    },
    requiredValidator(value) {
      return !!value || 'This field is required'
    },
  },
}
</script>

<style scoped>
.bg-light-danger {
  background-color: rgba(220, 53, 69, 0.1);
}
</style>
