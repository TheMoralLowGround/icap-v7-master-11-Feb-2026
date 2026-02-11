<template>
  <div>
    <b-table
      :items="rows"
      :fields="fields"
      :sort-by.sync="sortBy"
      :sort-desc.sync="sortDesc"
      striped
      responsive
      @sort-changed="generateRows"
    >
      <template #cell(show_patterns)="row">
        <b-form-checkbox
          v-model="row.item.checked"
          @change="() => onClick(row, false)"
        />
      </template>
      <template #cell(pattern)="row">
        <div
          :ref="`${row.item.pos[7]}`"
          class="d-flex"
          :class="{
            'cursor-pointer': !row.item.nitb,
            'highlight-cell': highlightAtmPatternRecord === `${row.item.pos[7]}`
          }"
          @click="onClick(row, true)"
        >
          <div
            class="dot-container mr-1 align-self-center"
            :style="{
              'background-color': row.item.pos[8] === 'blank' ? 'transparent' : row.item.pos[8]
            }"
          />

          <div>
            <p
              v-for="(pattern, index) in row.item.pattern.split('\n')"
              :key="index"
              class="m-0"
            >
              {{ pattern }}
            </p>
          </div>
        </div>
      </template>
      <template #cell(openBlock)="row">
        <b-form-checkbox
          v-model="row.item.openBlock"
          @change="() => onCheckOpenBlock(row.item)"
        />
      </template>
    </b-table>
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BTable, BFormCheckbox,
} from 'bootstrap-vue'

export default {
  components: {
    BTable,
    BFormCheckbox,
  },
  props: {
    rows: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      // Stores the field used for sorting the table (default is 'confidenceScore')
      sortBy: 'confidenceScore',
      // Determines whether the sorting should be in ascending or descending order (default is descending)
      sortDesc: true,
      // Holds the items that are rendered/displayed in the table
      renderedItems: [],
      // Keeps track of the ATM pattern record currently highlighted
      highlightAtmPatternRecord: null,
      // Timer to remove the highlight on the ATM pattern record after a delay
      highlightAtmPatternRecordTimer: null,
    }
  },
  computed: {
    // Fetches the selected ATM patterns from the Vuex store
    selectedAtmPatterns() {
      return this.$store.getters['atm/selectedAtmPatterns']
    },
    // Fetches the accordion options for the ATM from the Vuex store
    atmAccordionOptions() {
      return this.$store.getters['atm/atmAccordionOptions']
    },
    // Determines if the multiple line record view is enabled from the Vuex store
    multipleLineRecord() {
      return this.$store.getters['dataView/modelMultipleLineRecord']
    },
    // Defines the columns (fields) for the table and adds or removes the 'Open Record' column based on the multipleLineRecord flag
    fields() {
      const fields = [
        { key: 'show_patterns' },
        { key: 'pattern', label: 'Patterns' },
        { key: 'confidenceScore', label: 'confidence Score', sortable: true },
      ]

      // If multiple line record is disabled, add the 'Open Record' column
      if (!this.multipleLineRecord) {
        fields.push({ key: 'openBlock', label: 'Open Record' })
      }

      return fields
    },
  },
  created() {
    // Sets up event listeners for custom events triggered via the bus
    bus.$on('atm/scrollToAtmPatternRecord', this.scrollToAtmPatternRecord)
    bus.$on('atm/onShiftClick', this.onShiftClick)
  },
  destroyed() {
    // Removes the event listeners when the component is destroyed to prevent memory leaks
    bus.$off('atm/scrollToAtmPatternRecord', this.scrollToAtmPatternRecord)
    bus.$off('atm/onShiftClick', this.onShiftClick)
  },
  methods: {
    // Updates the selected ATM pattern's multi-line property based on the item clicked
    onCheckOpenBlock(item) {
      const selectedAtmPatterns = [...this.selectedAtmPatterns]

      // Finds the pattern in the selected ATM patterns list
      const index = selectedAtmPatterns.map(e => e.pattern).indexOf(item.pattern)

      // If the pattern is already selected, update its multiLine value
      if (index !== -1) {
        selectedAtmPatterns[index] = {
          ...selectedAtmPatterns[index],
          multiLine: item.openBlock.toString(),
        }
      }

      // Commit the updated selected ATM patterns to the store
      this.$store.commit('atm/SET_SELECTED_ATM_PATTERNS', selectedAtmPatterns)
    },

    // Handles the shift-click event to toggle the checked state of a row
    onShiftClick(posRef) {
      const index = this.rows.findIndex(e => e.pos[7] === posRef)

      // If the row with the given posRef is found, toggle its checked state
      if (index === -1) {
        return
      }

      this.rows[index].checked = !this.rows[index].checked

      // Emit the checked event to notify the parent component
      this.$emit('checked', { data: this.rows[index], scrollToPos: false })
    },

    // Handles the click event on a row to toggle its checked state and possibly scroll to the row
    onClick(row, scrollToPos) {
      // If the row has no 'nitb' property, emit the checked event and possibly scroll to position
      if (!row.item.nitb) {
        this.$emit('checked', { data: row.item, scrollToPos })
      }
    },

    // Dispatches the action to generate rows for the ATM pattern table
    generateRows() {
      this.$store.dispatch('atm/generateAtmPatternTableRows')
    },

    // Scrolls to the specific ATM pattern record based on the data provided
    scrollToAtmPatternRecord(data) {
      // Make a copy of the ATM accordion options and update the visibility of the corresponding section
      const atmAccordionOptions = [...this.atmAccordionOptions]

      atmAccordionOptions.forEach((item, index) => {
        if (!item.visible && item.key === data.refStatus) {
          atmAccordionOptions[index].visible = true
        }
      })

      // Commit the updated accordion options to the store
      this.$store.commit('atm/SET_ATM_ACCORDION_OPTIONS', atmAccordionOptions)

      // Select the DOM element associated with the provided position reference
      const refElement = this.$refs[data.posRef]

      // If the element is not found, return early
      if (!refElement) {
        return
      }

      // Clear any previously set timeout for removing the highlight
      clearTimeout(this.highlightAtmPatternRecordTimer)

      // Set the current highlighted ATM pattern record
      this.highlightAtmPatternRecord = data.posRef

      // Scroll the element into view after the next DOM update
      this.$nextTick(() => {
        setTimeout(() => {
          refElement.parentNode.scrollIntoView()
        }, 200)

        // Set a timeout to remove the highlight after 1.5 seconds
        this.highlightAtmPatternRecordTimer = setTimeout(() => {
          this.highlightAtmPatternRecord = null
        }, 1500)
      })
    },
  },
}
</script>

<style scoped lang="scss">
.highlight-cell {
  border: 2px solid red;
}
.dot-container {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: green;
}
</style>
