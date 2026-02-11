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
          v-model="anchors.top"
          variant="top"
          :class="{
            'invalid-input': errors.length > 0 ? true : false
          }"
          class="flex-grow-1"
          @focus="$emit('focus', 'top')"
        />
        <small class="text-danger">{{ errors[0] }}</small>
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
          class="flex-grow-1"
          name="Bottom Anchor Shape"
          rules="validAnchorShape"
          :vid="`${validationKey}-anchors-bottom`"
        >
          <anchor-shape-input
            v-model="anchors.bottom"
            :class="{
              'invalid-input': errors.length > 0 ? true : false
            }"
            variant="bottom"
            @focus="$emit('focus', 'bottom')"
          />
          <small class="text-danger">{{ errors[0] }}</small>
        </validation-provider>

        <div
          v-for="(pattern, patternIndex) of patterns"
          :key="patternIndex"
          class="d-flex align-items-baseline"
        >
          <validation-provider
            #default="{ errors }"
            class="flex-grow-1"
            name="Pattern"
            rules="required"
            :vid="`${validationKey}-pattern-${patternIndex}`"
          >
            <form-input
              v-model="patterns[patternIndex]"
              :state="errors.length > 0 ? false:null"
              placeholder="Pattern"
            />
            <small class="text-danger">{{ errors[0] }}</small>
          </validation-provider>
          <div v-if="patterns.length > 1">
            <feather-icon
              icon="Trash2Icon"
              class="cursor-pointer ml-50"
              size="20"
              @click.stop="deletePattern(patternIndex)"
            />
          </div>
        </div>

        <div>
          <add-item
            label="Pattern"
            @add="addPatterns"
          />
        </div>
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

import AnchorShapeInput from '../AnchorShapes/AnchorShapeInput.vue'
import FormInput from '../FormInput.vue'
import AddItem from '../AddItem.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    AnchorShapeInput,
    FormInput,
    AddItem,
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
      anchors: null,
      patterns: [],
      expanded: false,
    }
  },
  computed: {
    out() {
      return {
        anchors: cloneDeep(this.anchors),
        patterns: cloneDeep(this.patterns),
      }
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
      this.anchors = cloneDeep(this.value.anchors)
      this.patterns = cloneDeep(this.value.patterns)
    },
    addPatterns(count) {
      const patterns = []
      for (let i = 0; i < count; i += 1) {
        const pattern = null
        patterns.push(pattern)
      }
      this.patterns = this.patterns.concat(patterns)
    },
    deletePattern(index) {
      this.patterns.splice(index, 1)
    },
  },
}
</script>
