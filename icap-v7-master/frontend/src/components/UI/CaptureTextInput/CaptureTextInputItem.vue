<template>
  <validation-provider
    #default="{ errors }"
    :name="label"
    rules="required"
    :vid="validationKey"
  >
    <b-input-group
      class="input-group-merge"
      :class="[errors.length > 0 ? 'is-invalid' : null,]"
    >
      <template #append>
        <b-input-group-text
          class="py-0 my-0"
        >
          <span>
            <b-spinner
              v-if="loading"
              small
              label="Small Spinner"
            />

            <feather-icon
              v-if="!loading && selectorPosition === null"
              v-b-tooltip.hover
              icon="InfoIcon"
              size="15"
              title="Select area over image to capture value"
            />

            <feather-icon
              v-if="!loading && selectorPosition !== null"
              v-b-tooltip.hover
              icon="CrosshairIcon"
              size="15"
              class="cursor-pointer"
              :title="captured ? 'Captured!' : 'Capture'"
              @click="capture()"
            />
          </span>
        </b-input-group-text>
      </template>
      <form-input
        v-model="inputItem"
        :state="errors.length > 0 ? false:null"
        :selection-value-attr="type === 'startPos' ? 'startPos' : type === 'endPos' ? 'endPos': 'text'"
        :placeholder="placeholder"
      />
    </b-input-group>
    <small class="text-danger">{{ errors[0] }}</small>
  </validation-provider>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import {
  VBTooltip, BInputGroup, BInputGroupText, BSpinner,
} from 'bootstrap-vue'
import axios from 'axios'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

import FormInput from '../FormInput.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    FormInput,
    BInputGroup,
    BInputGroupText,
    ValidationProvider,
    BSpinner,
  },
  props: {
    value: {
      type: [String, Number],
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
    type: {
      type: String,
      required: true,
    },
    placeholder: {
      type: String,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      inputItem: null,
      captured: false,
      loading: false,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.inputItem)
    },
    selectorPosition() {
      return this.$store.getters['batch/selectorPosition']
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
      this.inputItem = cloneDeep(this.value)
    },
    async capture() {
      let captureValue = null

      // eslint-disable-next-line radix
      const startPos = parseInt(this.selectorPosition.startPos)
      // eslint-disable-next-line radix
      const endPos = parseInt(this.selectorPosition.endPos)
      // eslint-disable-next-line radix
      const topPos = parseInt(this.selectorPosition.topPos)
      // eslint-disable-next-line radix
      const bottomPos = parseInt(this.selectorPosition.bottomPos)

      if (this.type === 'startPos') {
        captureValue = `man-${startPos}`
      } else if (this.type === 'endPos') {
        captureValue = `man-${endPos}`
      } else if (this.type === 'text') {
        const batchId = this.$store.getters['batch/batch'].id
        const documentIndex = this.$store.getters['batch/selectedDocumentIndex']
        const {
          pageIndex,
        } = this.selectorPosition
        const positions = [startPos, topPos, endPos, bottomPos].join(',')

        this.loading = true
        let res = null
        try {
          res = await axios.post('/pipeline/get_text_by_pos/', {
            batch_id: batchId,
            document_index: documentIndex,
            page_index: pageIndex,
            positions,
          })
          this.loading = false
        } catch (error) {
          const message = error?.response?.data?.detail || 'Error fetching text from selection'
          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.loading = false
          return
        }
        captureValue = res.data.text
      }

      this.inputItem = captureValue
      this.captured = true
      setTimeout(() => {
        this.captured = false
      }, 1000)
    },
  },
}
</script>
