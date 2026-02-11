<template>
  <b-input-group>
    <template #prepend>
      <b-input-group-text class="py-0 my-0">
        <span>
          <feather-icon
            v-b-tooltip.hover
            :icon="featherIcon"
            size="15"
            :title="title"
          />
        </span>
      </b-input-group-text>
    </template>
    <form-input
      type="text"
      :value="anchorShape.text"
      :placeholder="title"
      @input="onInput"
      @selection-input="onSelectionInput"
      @focus="$emit('focus')"
    />
    <b-input-group-append style="flex-basis: 100px">
      <b-form-input
        v-model="anchorShape.threshold"
        type="number"
        placeholder="Threshold"
        @focus="$emit('focus')"
      />
    </b-input-group-append>
  </b-input-group>
</template>

<script>
import {
  VBTooltip, BInputGroup, BInputGroupText, BInputGroupAppend, BFormInput,
} from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'
import FormInput from '../FormInput.vue'

const defaultValue = {
  text: null,
  pos: null,
  pageIndex: null,
  documentIndex: null,
  threshold: null,
}

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    FormInput,
    BInputGroup,
    BInputGroupText,
    BInputGroupAppend,
    BFormInput,
  },
  props: {
    value: {
      type: Object,
      required: false,
      default() {
        return null
      },
    },
    variant: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      anchorShape: null,
    }
  },
  computed: {
    title() {
      const variant = this.variant.charAt(0).toUpperCase() + this.variant.slice(1)
      return `${variant} Anchor Shape`
    },
    featherIcon() {
      let icon = null
      switch (this.variant) {
        case 'top':
          icon = 'ArrowUpIcon'
          break
        case 'bottom':
          icon = 'ArrowDownIcon'
          break
        case 'left':
          icon = 'ArrowLeftIcon'
          break
        case 'right':
          icon = 'ArrowRightIcon'
          break

        default:
          break
      }
      return icon
    },
    out() {
      return cloneDeep(this.anchorShape)
    },
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
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
    selectedDocumentId() {
      this.$store.dispatch('batch/clearAnchorHighlights')
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      if (this.value != null) {
        this.anchorShape = {
          ...defaultValue,
          ...this.value,
        }
      } else {
        this.anchorShape = cloneDeep(defaultValue)
      }
    },
    onInput(data) {
      if (data) {
        this.anchorShape.text = data
      } else {
        this.anchorShape = cloneDeep(defaultValue)
      }
    },
    onSelectionInput(data) {
      this.anchorShape.pos = `${data.startPos},${data.topPos},${data.endPos},${data.bottomPos}`
      this.anchorShape.pageIndex = data.pageIndex
      this.anchorShape.documentIndex = this.$store.getters['batch/selectedDocumentIndex']
    },
  },
}
</script>

<style scoped>

.invalid-input {
  border: 1px solid #ea5455;
  border-radius: 0.357rem;
}

</style>
