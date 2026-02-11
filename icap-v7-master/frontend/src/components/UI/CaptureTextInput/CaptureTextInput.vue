<template>
  <div>
    <div
      v-if="items.length > 0"
      class="d-flex align-items-center"
    >
      <capture-text-input-item
        v-model="items[0]"
        :validation-key="`${validationKey}-0}`"
        :label="label"
        class="flex-grow-1"
        :type="type"
      />
      <div>
        <feather-icon
          v-if="!expanded && items.length === 1"
          icon="ChevronUpIcon"
          class="cursor-pointer mx-50"
          size="20"
          @click="expanded = true"
        />

        <b-badge
          v-if="!expanded && items.length > 1"
          pill
          variant="secondary"
          class="cursor-pointer mx-50"
          @click="expanded = true"
        >{{ `+${(items.length -1)}` }}</b-badge>

        <feather-icon
          v-if="expanded === true"
          icon="ChevronDownIcon"
          class="cursor-pointer mx-50"
          size="20"
          @click="expanded = false"
        />
      </div>
    </div>
    <div
      v-if="expanded"
      class="mt-50"
    >
      <div
        v-for="(item, itemIndex) of items.slice(1)"
        :key="itemIndex"
        class="d-flex align-items-center mb-50"
      >
        <capture-text-input-item
          v-model="items[itemIndex + 1]"
          :label="label"
          class="flex-grow-1"
          :validation-key="`${validationKey}-${itemIndex + 1}`"
          :type="type"
        />

        <div>
          <feather-icon
            icon="Trash2Icon"
            class="cursor-pointer ml-50"
            size="20"
            @click.stop="deleteItem(itemIndex + 1)"
          />
        </div>
      </div>

      <div>
        <add-item
          :label="label"
          @add="addItems"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { BBadge } from 'bootstrap-vue'
import { isEqual } from 'lodash'
import AddItem from '../AddItem.vue'
import CaptureTextInputItem from './CaptureTextInputItem.vue'

export default {
  components: {
    AddItem,
    BBadge,
    CaptureTextInputItem,
  },
  props: {
    value: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    label: {
      type: String,
      required: true,
    },
    validationKey: {
      type: String,
      required: true,
    },
    type: {
      type: String,
      required: true,
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
      return this.items.join('|')
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
    if (this.items.length === 0) {
      this.addItems(1)
    }
  },
  methods: {
    setInternalState() {
      this.items = this.value.split('|')
    },
    addItems(count) {
      const items = []
      for (let i = 0; i < count; i += 1) {
        items.push(null)
      }
      this.items = this.items.concat(items)
    },
    deleteItem(index) {
      this.items.splice(index, 1)
    },
  },
}
</script>
