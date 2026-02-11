<template>
  <div>
    <!-- v-select component for project selection -->
    <v-select
      ref="projectOptions"
      v-model="project"
      :clearable="false"
      :options="projectOptions"
      @open="scrollToSelected"
    />
  </div>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash' // Utility functions for deep comparisons and cloning
import vSelect from 'vue-select'
import { VBTooltip } from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip, // Registering the tooltip directive
  },
  components: {
    vSelect, // Registering the v-select component
  },
  props: {
    // Array of project options for the dropdown
    projectOptions: {
      type: Array, // Expects an array
      required: true, // Prop is mandatory
    },
    // Current value selected in the parent component
    value: {
      type: String, // Expects a string
      required: true, // Prop is mandatory
    },
  },
  data() {
    return {
      project: null, // Local state to hold the selected project
    }
  },
  computed: {
    // Returns a deep clone of the local `project` state
    out() {
      return cloneDeep(this.project)
    },
  },
  watch: {
    // Watches for changes in `out` and emits them to the parent if different from `value`
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val) // Emits the updated value
        }
      },
      deep: true, // Deep watch to handle nested objects
    },
    // Watches for changes in the `value` prop and updates the local state if needed
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState() // Synchronizes local state with the prop
        }
      },
      deep: true, // Deep watch for nested changes
    },
  },
  created() {
    // Sets the initial state of `project` based on the `value` prop
    this.setInternalState()
  },
  methods: {
    // Synchronizes the local `project` state with the `value` prop
    setInternalState() {
      this.project = cloneDeep(this.value) // Deep copy to avoid direct mutation
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs?.projectOptions?.$refs?.dropdownMenu

        const selectedIndex = this.projectOptions.indexOf(this.project)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.projectOptions.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style lang="scss">
// Import styles for the v-select component
@import '@core/scss/vue/libs/vue-select.scss';
</style>
