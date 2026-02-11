<template>
  <div>
    <OcrSettings />
    <hr class="my-4">
    <PreprocessingSettings />
    <hr class="my-4">
    <ClassifierSettings />
  </div>
</template>

<script>
import ClassifierSettings from './ClassifierSettings.vue'
import OcrSettings from './OcrSettings.vue'
import PreprocessingSettings from './PreprocessingSettings.vue'

export default {
  components: {
    ClassifierSettings,
    OcrSettings,
    PreprocessingSettings,
  },

}
</script>
