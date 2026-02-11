<template>
  <b-form-input
    v-bind="$attrs"
    :class="{
      'listening': listening
    }"
    v-on="$listeners"
    @focus="onFocus"
    @blur="onBlur"
  />
</template>

<script>
import { BFormInput } from 'bootstrap-vue'
import bus from '@/bus'

export default {
  components: {
    BFormInput,
  },
  props: {
    selectionValueAttr: {
      type: String,
      required: false,
      default() {
        return 'text'
      },
    },
  },
  data() {
    return {
      listening: false,
    }
  },
  computed: {
    mode() {
      return this.$store.getters['dataView/mode']
    },
    modelAutoPositionShiftCal() {
      return this.$store.getters['dataView/modelAutoPositionShiftCal']
    },
    positionShiftData() {
      return this.$store.getters['batch/positionShiftData']
    },
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },
  },
  methods: {
    onFocus() {
      this.listening = true
      bus.$on('imageViewerValueSelected', this.valueSelected)
      bus.$emit('focus')
    },
    onBlur() {
      this.listening = false
      bus.$off('imageViewerValueSelected', this.valueSelected)
    },
    valueSelected(data) {
      // const data = { ...val }

      // if (this.mode === 'table-columns' && data.startPos && data.endPos) {
      //   data.startPos = this.getUpdatedPos(data.startPos, data.pageId)
      //   data.endPos = this.getUpdatedPos(data.endPos, data.pageId)
      // }

      let value
      if (this.selectionValueAttr === 'textToShape') {
        value = this.textToShape(data.text)
      } else {
        value = data[this.selectionValueAttr]
      }

      this.$emit('input', value)
      this.$emit('selection-input', data)
    },
    getUpdatedPos(pos, pageId) {
      if (this.modelAutoPositionShiftCal === 'false' || !this.positionShiftData) {
        return pos
      }

      const adjustValue = this.positionShiftData[this.selectedDocumentId][pageId]
      const updatedPos = parseInt(pos, 10) + adjustValue

      return updatedPos.toString()
    },
    textToShape(text) {
      let stringText = String(text)
      stringText = stringText.replaceAll(/[A-Z]/g, 'X')
      stringText = stringText.replaceAll(/[a-z]/g, 'x')
      stringText = stringText.replaceAll(/[0-9]/g, 'D')
      stringText = stringText.replaceAll('.', 'b')
      stringText = stringText.replaceAll(',', 'c')
      stringText = stringText.replaceAll(':', 'y')
      return stringText
    },
  },
}
</script>

<style scoped>
.listening {
  outline: 3px solid yellow;
}
</style>
