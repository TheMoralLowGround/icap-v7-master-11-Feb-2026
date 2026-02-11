<template>
  <div>
    <div
      v-if="items.length > 0"
      class="d-flex align-items-center"
    >
      <cell-range-selector-input
        v-model="items[0]"
        :validation-key="`${validationKey}-0}`"
        :validation-rules="validationRules"
        :label="label"
        :deletable="deletable"
        :placeholder="placeholder"
        class="flex-grow-1"
      />
      <div v-if="multiple">
        <feather-icon
          v-if="!expanded && items.length === 1 && !isExcelBatch"
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
          v-if="expanded === true && !isExcelBatch"
          icon="ChevronDownIcon"
          class="cursor-pointer mx-50"
          size="20"
          @click="expanded = false"
        />
      </div>
    </div>
    <div
      v-show="expanded"
      class="mt-50"
    >
      <div
        v-for="(item, itemIndex) of items.slice(1)"
        :key="itemIndex"
        class="d-flex align-items-center mb-50"
      >
        <cell-range-selector-input
          v-model="items[itemIndex + 1]"
          :label="label"
          :deletable="deletable"
          :placeholder="placeholder"
          class="flex-grow-1"
          :validation-key="`${validationKey}-${itemIndex + 1}`"
          :validation-rules="validationRules"
        />

        <!-- <div>
          <feather-icon
            icon="Trash2Icon"
            class="cursor-pointer ml-50"
            size="20"
            @click.stop="deleteItem(itemIndex + 1)"
          />
        </div> -->
      </div>

      <div v-if="!isExcelBatch">
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
import { isEqual, cloneDeep } from 'lodash'
import AddItem from '../AddItem.vue'
import CellRangeSelectorInput from './CellRangeSelectorInput.vue'

const defaultCellRangeSelectorInputValue = {
  sheetNumber: null,
  cellRange: null,
  sheetName: null,
}

export default {
  components: {
    AddItem,
    BBadge,
    CellRangeSelectorInput,
  },
  props: {
    value: {
      type: [Array, Object, String],
      required: false,
      default() {
        return null
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
    initializeExpanded: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    multiple: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    placeholder: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    deletable: {
      type: Boolean,
      required: false,
      default() {
        return false
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
      if (this.multiple) {
        return cloneDeep(this.items)
      }
      return cloneDeep(this.items[0])
    },
    isExcelBatch() {
      return this.$store.getters['batch/batch'].isExcel
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
    this.expanded = this.initializeExpanded
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      let items = [defaultCellRangeSelectorInputValue]

      if (this.value !== null) {
        if (this.multiple) {
          if (this.value.length > 0) {
            items = this.value
          }
        } else {
          items = [this.value]
        }
      }

      this.items = cloneDeep(items)
    },
    addItems(count) {
      const items = []
      for (let i = 0; i < count; i += 1) {
        items.push({ ...defaultCellRangeSelectorInputValue })
      }
      this.items = this.items.concat(items)
    },
    deleteItem(index) {
      this.items.splice(index, 1)
    },
  },
}
</script>
