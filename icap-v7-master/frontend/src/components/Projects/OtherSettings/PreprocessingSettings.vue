<template>
  <div>
    <h2 class="mb-2">
      Preprocess Settings
    </h2>
    <b-form-checkbox
      v-model="ignoreDensePage"
      switch
    >
      Ignore Dense Page
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
    ignoreDensePage: {
      get() {
        return this.$store.getters['project/projectPreprocessSettings'].ignore_dense_page
      },
      set(value) {
        this.$store.commit('project/SET_PREPROCESS_SETTING', { ignore_dense_page: value })
      },
    },
  },
}
</script>
