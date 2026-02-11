<template>
  <div>
    <div
      class="d-flex flex-column"
      style="row-gap: 0.25rem; margin-top: 0.25rem;"
    >
      <cell-range-selector
        v-model="item.columnStartCell"
        :validation-key="`${validationKey}-Column Start Cell}`"
        :validation-rules="validationRules"
        label="Column Start Cell"
        placeholder="Column Start Cell"
        class="w-100"
      />

      <cell-range-selector
        v-model="item.columnEndCell"
        :validation-key="`${validationKey}-Column End Cell}`"
        label="Column End Cell"
        placeholder="Column End Cell"
        class="w-100"
      />
    </div>
  </div>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import CellRangeSelector from '../CellRangeSelector/CellRangeSelector.vue'

export default {
  components: {
    CellRangeSelector,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    validationKey: {
      type: String,
      required: true,
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
  },
  data() {
    return {
      item: {
        columnStartCell: null,
        columnEndCell: null,
      },
    }
  },
  computed: {
    out() {
      return cloneDeep(this.item)
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
      this.item = cloneDeep(this.value)
    },
  },
}
</script>
