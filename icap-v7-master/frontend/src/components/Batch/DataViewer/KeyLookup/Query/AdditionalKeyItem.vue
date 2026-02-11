<!--
 Organization: AIDocbuilder Inc.
 File: AdditionalKeyItem.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-02

 Description:
   This component represents an individual key item used for rule-based lookups. It includes dropdown selections for choosing
   a target column and key, as well as a delete icon for removing the item. The component manages and emits changes to
   the selected values, integrating with the state and options provided by the parent component and Vuex store.

 Features:
   - Dropdown selection for target column and key with clearable options.
   - Delete icon to remove the key item from the list.
   - Tooltip for hover effect on the delete icon.
   - Uses Vuex for managing key options for rules and table columns.

 Dependencies:
   - VueSelect for the dropdown functionality.
   - BootstrapVue for tooltips.
   - Lodash for deep cloning and comparison of data.

-->

<template>
  <div
    class="d-flex align-items-center my-50"
    style="column-gap: 10px;"
  >
    <div style="flex-basis:500px;">
      <v-select
        ref="columnOptions"
        v-model="item.target_column"
        :options="columnOptions"
        :clearable="false"
        @open="scrollToSelected(columnOptions, item.target_column)"
      />
    </div>
    <div style="flex-basis:500px;">
      <v-select
        ref="keyOptionsForRules"
        v-model="item.target_key"
        :options="keyOptionsForRules"
        :clearable="false"
        label="label"
        :reduce="option => option.value"
        placeholder="Select a key"
        @open="scrollToSelected(keyOptionsForRules, item.target_key)"
      />
    </div>
    <div>
      <feather-icon
        v-b-tooltip.hover
        title="Delete Key"
        icon="Trash2Icon"
        class="cursor-pointer mx-auto"
        size="20"
        @click.stop="$emit('delete')"
      />
    </div>
  </div>
</template>

<script>
import { VBTooltip } from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    vSelect,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    tableColumns: {
      type: Array,
      required: true,
    },
    queryResultOptions: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      item: {},
    }
  },
  computed: {
    out() {
      return cloneDeep(this.item)
    },
    columnOptions() {
      return this.tableColumns.map(tableColumn => tableColumn.name)
    },
    keyOptionsForRules() {
      const options = this.$store.getters['definitionSettings/keyOptionsForRules']
      const UniqeRuleoptions = options.filter((item, index) => options.findIndex(el => el.label === item.label) === index)
      return UniqeRuleoptions
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
      this.item = cloneDeep(this.value)

      // Find the matching option in keyOptionsForRules based on item.target_key
      const matchingOption = this.keyOptionsForRules.find(option => JSON.stringify(option.value.fieldInfo) === JSON.stringify(this.item.target_key?.fieldInfo))

      // Set the item.target_key to the found option's value (if any)
      if (matchingOption) {
        this.item.target_key = matchingOption.value
      }
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected(options, selectedValue) {
      this.$nextTick(() => {
        // Helper function to scroll a dropdown menu to the selected item
        const scrollDropdownToSelected = (dropdownMenu, selectedIndex) => {
          if (dropdownMenu && selectedIndex >= 0) {
            // Calculate scroll position by assuming each item has a uniform height
            const itemHeight = dropdownMenu.scrollHeight / options.length

            // Adjust scrollTop to bring the selected item closer to the top
            const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
            // eslint-disable-next-line no-param-reassign
            dropdownMenu.scrollTop = scrollPosition
          }
        }

        // Get references to dropdown menus
        const columnOptionsItems = this.$refs.columnOptions?.$refs.dropdownMenu
        const keyOptionsForRulesItems = this.$refs.keyOptionsForRules?.$refs.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options?.indexOf(selectedValue)
        const findSelectedIndex = options?.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        scrollDropdownToSelected(columnOptionsItems, selectedIndex)
        scrollDropdownToSelected(keyOptionsForRulesItems, findSelectedIndex)
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
