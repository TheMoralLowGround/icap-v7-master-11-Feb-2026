<template>
  <div>
    <div class="d-flex align-items-center">
      <AutoPatternInputItem
        :item="items"
        class="flex-grow-1"
        @toggle-expanded="expanded = !expanded"
      />
      <b-badge
        v-if="!expanded && items.length > 0"
        pill
        variant="secondary"
        class="cursor-pointer mx-50"
        @click="expanded = true"
      >{{ `+${(items.length)}` }}</b-badge>

      <feather-icon
        v-if="expanded === true && items.length > 0"
        icon="ChevronDownIcon"
        class="cursor-pointer mx-50"
        size="20"
        @click="expanded = false"
      />
    </div>
    <div
      v-if="expanded"
      class="mt-50"
    >
      <div
        v-for="(item, index) of items"
        :key="index"
        class="d-flex align-items-center mb-50"
      >
        <AutoPatternInputItem
          :item="items[index]"
          class="flex-grow-1"
        />

        <feather-icon
          icon="Trash2Icon"
          class="cursor-pointer ml-50"
          size="20"
          @click.stop="deleteItem(index)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import { BBadge } from 'bootstrap-vue'
import AutoPatternInputItem from './AutoPatternInputItem.vue'

export default {
  components: {
    BBadge,
    AutoPatternInputItem,
  },
  props: {
    value: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      expanded: false,
      items: [],
    }
  },
  computed: {
    out() {
      return cloneDeep(this.items)
    },
  },
  watch: {
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.items = Array.isArray(this.value) ? cloneDeep(this.value) : []
    },
    deleteItem(index) {
      this.items.splice(index, 1)
    },
  },
}
</script>

<style scoped>
::v-deep .custom-switch .custom-control-label {
  padding-left: .5rem;
}
</style>
