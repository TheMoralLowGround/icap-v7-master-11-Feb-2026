<template>
  <div>
    <h2 class="mb-2">
      Classifier Settings
    </h2>
    <!-- <b-form-checkbox
      v-model="automaticSplitting"
      switch
    >
      Automatic Splitting
    </b-form-checkbox> -->
    <b-form-checkbox
      v-model="disableClassificationReview"
      switch
    >
      Disable Classification Review
    </b-form-checkbox>
  </div>
</template>

<script>
import { BFormCheckbox } from 'bootstrap-vue'

export default {
  components: {
    BFormCheckbox,
  },
  computed: {
    automaticSplitting: {
      get() {
        return this.$store.getters['project/projectClassifierSettings'].automatic_splitting
      },
      set(value) {
        this.$store.commit('project/SET_CLASSIFIER_SETTING', { automatic_splitting: value })
      },
    },
    disableClassificationReview: {
      get() {
        return this.$store.getters['project/projectClassifierSettings'].disable_classification_review
      },
      set(value) {
        this.$store.commit('project/SET_CLASSIFIER_SETTING', { disable_classification_review: value })
      },
    },
  },
}
</script>
