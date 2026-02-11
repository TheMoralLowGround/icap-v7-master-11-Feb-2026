<template>
  <v-select
    v-model="mode"
    :clearable="false"
    :options="options"
    label="label"
    :reduce="option => option.value"
  />
</template>

<script>
import vSelect from 'vue-select'

export default {
  components: {
    vSelect,
  },
  data() {
    return {
      // Array of mode options for the dropdown
      options: [
        {
          label: 'View Mode',
          value: 'view',
        },
        {
          label: 'Edit Mode',
          value: 'edit',
        },
      ],
    }
  },
  computed: {
    // Computed property `mode` for reactive access to the mode state in Vuex
    mode: {
      // Getter to retrieve the current mode from the Vuex store
      get() {
        return this.$store.getters['batch/mode']
      },
      // Setter to update the mode in the Vuex store
      set(value) {
        this.$store.commit('batch/SET_MODE', value)
      },
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
