<template>
  <b-form-input
    v-model="search"
    placeholder="Search"
  />
</template>

<script>
import { BFormInput } from 'bootstrap-vue'

export default {
  components: {
    BFormInput,
  },
  computed: {
    search: {
      get() {
        return this.$store.getters['lookup/search']
      },
      set(value) {
        this.$store.commit('lookup/SET_SEARCH', value)
      },
    },
  },
}
</script>
