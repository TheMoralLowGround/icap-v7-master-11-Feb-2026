<template>
  <div>
    <div class="d-flex align-items-center">
      <validation-provider
        #default="{ errors }"
        class="flex-grow-1"
        name="Top Anchor Shape"
        rules="validAnchorShape"
        :vid="`${validationKey}-anchors-top`"
      >
        <anchor-shape-input
          v-model="anchorShapes.top"
          variant="top"
          :class="{
            'invalid-input': errors.length > 0 || failedRules.requireAtleastOneAnchorShape ? true : false
          }"
          @focus="$emit('focus', 'top')"
        />
        <small class="text-danger">{{ errors[0] || failedRules.requireAtleastOneAnchorShape }}</small>
      </validation-provider>
      <div>
        <feather-icon
          :icon="expanded ? 'ChevronDownIcon' : 'ChevronUpIcon'"
          class="cursor-pointer mx-50"
          size="20"
          @click="expanded = !expanded"
        />
      </div>
    </div>
    <div v-show="expanded">
      <div
        class="d-flex flex-column"
        style="row-gap:0.25rem;margin-top:0.25rem;"
      >
        <validation-provider
          #default="{ errors }"
          name="Bottom Anchor Shape"
          rules="validAnchorShape"
          :vid="`${validationKey}-anchors-bottom`"
        >
          <anchor-shape-input
            v-model="anchorShapes.bottom"
            :class="{
              'invalid-input': errors.length > 0 || failedRules.requireAtleastOneAnchorShape ? true : false
            }"
            variant="bottom"
            @focus="$emit('focus', 'bottom')"
          />
          <small class="text-danger">{{ errors[0] || failedRules.requireAtleastOneAnchorShape }}</small>
        </validation-provider>
        <validation-provider
          #default="{ errors }"
          name="Left Anchor Shape"
          rules="validAnchorShape"
          :vid="`${validationKey}-anchors-left`"
        >
          <anchor-shape-input
            v-model="anchorShapes.left"
            :class="{
              'invalid-input': errors.length > 0 || failedRules.requireAtleastOneAnchorShape ? true : false
            }"
            variant="left"
            @focus="$emit('focus', 'left')"
          />
          <small class="text-danger">{{ errors[0] || failedRules.requireAtleastOneAnchorShape }}</small>
        </validation-provider>
        <validation-provider
          #default="{ errors }"

          name="Right Anchor Shape"
          rules="validAnchorShape"
          :vid="`${validationKey}-anchors-right`"
        >
          <anchor-shape-input
            v-model="anchorShapes.right"
            :class="{
              'invalid-input': errors.length > 0 || failedRules.requireAtleastOneAnchorShape ? true : false
            }"
            variant="right"
            @focus="$emit('focus', 'right')"
          />
          <small class="text-danger">{{ errors[0] || failedRules.requireAtleastOneAnchorShape }}</small>
        </validation-provider>
      </div>
    </div>
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import { isEqual, cloneDeep } from 'lodash'

import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import AnchorShapeInput from './AnchorShapeInput.vue'

const defaultValue = {
  top: null,
  bottom: null,
  left: null,
  right: null,
}

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    AnchorShapeInput,
    ValidationProvider,
  },
  props: {
    value: {
      type: Object,
      required: false,
      default() {
        return null
      },
    },
    validationKey: {
      type: String,
      required: true,
    },
    failedRules: {
      type: Object,
      required: true,
    },
    initializeExpanded: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
  },
  data() {
    return {
      anchorShapes: null,
      expanded: false,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.anchorShapes)
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
      if (this.value != null) {
        this.anchorShapes = cloneDeep(this.value)
      } else {
        this.anchorShapes = cloneDeep(defaultValue)
      }
    },
  },
}
</script>
