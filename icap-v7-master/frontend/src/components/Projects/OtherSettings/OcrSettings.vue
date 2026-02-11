<template>
  <div>
    <h2 class="mb-2">
      OCR Engine Settings
    </h2>
    <b-form-group label="OCR Engine Type">
      <b-form-radio-group
        v-model="ocrEngineType"
        name="ocr-engine"
        stacked
      >
        <b-form-radio value="internal">
          Internal
        </b-form-radio>
        <b-form-radio value="external">
          External
        </b-form-radio>
      </b-form-radio-group>
    </b-form-group>
  </div>
</template>

<script>
import {
  BFormGroup,
  BFormRadio,
  BFormRadioGroup,
} from 'bootstrap-vue'

export default {
  components: {
    BFormGroup,
    BFormRadioGroup,
    BFormRadio,
  },

  computed: {
    ocrEngineType: {
      get() {
        return this.$store.getters['project/projectOcrSettings'].engine_type
      },
      set(newValue) {
        this.$store.commit('project/SET_OCR_ENGINE_TYPE', newValue)
      },
    },
  },
}
</script>
