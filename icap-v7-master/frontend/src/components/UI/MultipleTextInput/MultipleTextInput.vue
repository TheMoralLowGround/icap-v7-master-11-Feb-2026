<template>
  <div class="mb-1">
    <b-form-group
      :label="placeholder"
      class="mb-0"
    />

    <!-- First Field -->
    <div
      v-if="items.length > 0"
      class="d-flex align-items-baseline first-field-section"
    >
      <form-input
        v-model="items[0]"
        :placeholder="inputFieldPlaceholder"
      />
      <div>
        <feather-icon
          icon="Trash2Icon"
          class="cursor-pointer ml-50"
          size="20"
          @click.stop="delteItem(0)"
        />
      </div>
      <div>
        <feather-icon
          :icon="expanded ? 'ChevronDownIcon' : 'ChevronUpIcon'"
          class="cursor-pointer ml-50"
          size="20"
          @click="expanded = !expanded"
        />
      </div>
    </div>

    <!-- Expanded Fields -->
    <div
      v-if="expanded"
      class="d-flex flex-column expanded-field-section"
    >
      <div
        v-for="(item, itemIndex) of items.slice(1)"
        :key="itemIndex"
        class="d-flex align-items-baseline"
      >
        <form-input
          v-model="items[itemIndex + 1]"
          :placeholder="inputFieldPlaceholder"
        />
        <div>
          <feather-icon
            icon="Trash2Icon"
            class="cursor-pointer ml-50"
            size="20"
            @click.stop="delteItem(itemIndex + 1)"
          />
        </div>
      </div>
    </div>

    <!-- Add Item Section -->
    <div
      v-if="expanded || (!expanded && items.length === 0)"
    >
      <add-item
        label="Item"
        @add="additems"
      />
    </div>
  </div>
</template>

<script>
import { BFormGroup } from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'

import FormInput from '../FormInput.vue'
import AddItem from '../AddItem.vue'

export default {
  components: {
    FormInput,
    AddItem,
    BFormGroup,
  },
  props: {
    placeholder: {
      type: String,
      required: false,
      default: '',
    },
    inputFieldPlaceholder: {
      type: String,
      required: false,
      default: '',
    },
    value: {
      type: Array,
      required: false,
      default() {
        return []
      },
    },
  },
  data() {
    return {
      items: [],
      expanded: false,
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
      this.items = cloneDeep(this.value)
    },
    additems(count) {
      const items = []
      for (let i = 0; i < count; i += 1) {
        const item = null
        items.push(item)
      }
      this.items = this.items.concat(items)
      if (!this.expanded) {
        this.expanded = true
      }
    },
    delteItem(index) {
      this.items.splice(index, 1)
    },
  },
}
</script>

<style scoped>
.first-field-section, .expanded-field-section {
  margin-bottom:0.25rem;
}
.expanded-field-section {
  row-gap:0.25rem;
}
</style>
