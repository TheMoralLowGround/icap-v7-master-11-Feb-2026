<template>
  <div
    class="d-flex flex-column"
    :class="{'h-100 justify-content-center': loading && (atmWizardTabs.results.active || atmWizardTabs.test.active)}"
  >
    <atm-wizard>
      <template #results>
        <app-collapse
          v-if="Object.keys(atmPatternTableRows).length"
        >
          <template
            v-for="(item, index) in atmAccordionOptions"
          >
            <app-collapse-item
              v-if="Object.keys(atmPatternTableRows).includes(item.key)"
              :key="index"
              :is-visible="item.visible"
              :title="item.label"
              @visible="(val) => updateVisible(val, item)"
            >
              <atm-pattern-table
                :rows="atmPatternTableRows[item.key]"
                @checked="checked"
              />
            </app-collapse-item>
          </template>
        </app-collapse>
      </template>
    </atm-wizard>
  </div>
</template>

<script>
import bus from '@/bus'
import AppCollapse from '@core/components/app-collapse/AppCollapse.vue'
import AppCollapseItem from '@core/components/app-collapse/AppCollapseItem.vue'
import AtmPatternTable from './AtmPatternTable.vue'
import AtmWizard from './AtmWizard/AtmWizard.vue'

export default {
  components: {
    AtmPatternTable,
    AtmWizard,
    AppCollapse,
    AppCollapseItem,
  },
  computed: {
    // Computed property to get and set the loading state using Vuex.
    loading: {
      get() {
        return this.$store.getters['dataView/loading']
      },
      set(value) {
        this.$store.commit('dataView/SET_LOADING', value)
      },
    },

    // Fetches the current batch status from Vuex.
    status() {
      return this.$store.getters['batch/status']
    },

    // Retrieves the batch data object from Vuex.
    batch() {
      return this.$store.getters['batch/batch']
    },

    // Retrieves the ID of the currently selected document from Vuex.
    selectedDocumentId() {
      return this.$store.getters['batch/selectedDocumentId']
    },

    // Calculates the total number of pages by counting the keys in the pages object.
    totalPages() {
      return Object.keys(this.$store.getters['batch/documentData'].pages).length
    },

    // Fetches the ATM wizard tabs configuration from Vuex.
    atmWizardTabs() {
      return this.$store.getters['atm/atmWizardTabs']
    },

    // Retrieves the options for ATM accordion UI from Vuex.
    atmAccordionOptions() {
      return this.$store.getters['atm/atmAccordionOptions']
    },

    // Fetches the ATM patterns data from Vuex.
    atmPatterns() {
      return this.$store.getters['atm/atmPatterns']
    },

    // Retrieves the table rows for displaying ATM patterns from Vuex.
    atmPatternTableRows() {
      return this.$store.getters['atm/atmPatternTableRows']
    },

    // Retrieves the selected ATM patterns from Vuex.
    selectedAtmPatterns() {
      return this.$store.getters['atm/selectedAtmPatterns']
    },

    // Retrieves the pattern records for ATM from Vuex.
    atmPatternRecords() {
      return this.$store.getters['atm/atmPatternRecords']
    },

    // Retrieves the ATM configuration data from Vuex.
    atmConfig() {
      return this.$store.getters['atm/atmConfig']
    },

    // Fetches the chunk line records for ATM from Vuex.
    chunkLineRecords() {
      return this.$store.getters['atm/chunkLineRecords']
    },

    // Retrieves the user-selected patterns for ATM from Vuex.
    userSelectedPatterns() {
      return this.$store.getters['atm/userSelectedPatterns']
    },

    // Retrieves the extended user-selected patterns for ATM from Vuex.
    extendedUserSelectedPatterns() {
      return this.$store.getters['atm/extendedUserSelectedPatterns']
    },

    // Checks whether the multiple line record mode is active from Vuex.
    multipleLineRecord() {
      return this.$store.getters['dataView/modelMultipleLineRecord']
    },

    // Retrieves the selected definition version from Vuex.
    selectedDefinitionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },
  },

  watch: {
    // Watches for changes in ATM patterns and triggers updates for the pattern table rows.
    atmPatterns(newVal) {
      if (newVal.length) {
        this.$store.dispatch('atm/generateAtmPatternTableRows')
      } else {
        this.$store.commit('atm/SET_ATM_PATTERN_TABLE_ROWS', [])
      }
    },

    // Watches for changes in the batch status and handles transitions to different tabs.
    status: {
      handler() {
        // If the status is 'completed' or 'failed', switch to the appropriate tab.
        if (['completed', 'failed'].includes(this.status.status)) {
          if (this.atmWizardTabs.test.active) {
            bus.$emit('atm/onChangeTab', 'test') // Switches to the "test" tab.
          } else {
            bus.$emit('atm/onChangeTab', 'results') // Switches to the "results" tab.
          }
        }
      },
      deep: true, // Enables deep watching for nested properties in the status object.
    },
  },

  created() {
    // Registers event listeners for ATM-related updates.
    bus.$on('atm/updateStatus', this.updateStatus)
    bus.$on('atm/updateSelectedAtmPattern', this.updateSelectedAtmPattern)
    bus.$on('navigate', this.handleNavigation)
  },

  destroyed() {
    // Removes event listeners when the component is destroyed to avoid memory leaks.
    bus.$off('atm/updateStatus', this.updateStatus)
    bus.$off('atm/updateSelectedAtmPattern', this.updateSelectedAtmPattern)
    bus.$off('navigate', this.handleNavigation)
  },
  methods: {
    handleNavigation({ name, params }) {
      if (name === this.$route.name && params.id !== this.$route.params.id) {
        this.$router.replace({ name, params })
      }
    },
    // Updates the visibility state of an ATM accordion item
    updateVisible(visibleState, item) {
      const atmAccordionOptions = [...this.atmAccordionOptions]

      // Loop through accordion options to find the matching item and update its visibility
      atmAccordionOptions.forEach(({ key }, index) => {
        if (key === item.key) {
          atmAccordionOptions[index].visible = visibleState
        }
      })

      // Commit the updated accordion options to the store
      this.$store.commit('atm/SET_ATM_ACCORDION_OPTIONS', atmAccordionOptions)
    },

    // Handles the "checked" action, updates scroll position or selected ATM pattern
    checked(val) {
      // Dispatch action to scroll to a specific position
      if (val.scrollToPos) {
        this.$store.dispatch('batch/scrollToPos', val.data.pos)

        return
      }

      // Update selected ATM pattern and status
      this.updateSelectedAtmPattern(val.data)

      this.updateStatus({ posRef: val.data.pos[7], autoChecked: false })
    },

    // Updates the selected ATM pattern, adding or removing it from the list
    updateSelectedAtmPattern(data) {
      const selectedAtmPatterns = [...this.selectedAtmPatterns]
      const item = {
        pattern: data.pattern,
        multiLine: data.openBlock.toString(),
        digit_threshold: this.atmConfig.digit_threshold.value,
        text_threshold: this.atmConfig.text_threshold.value,
        n: this.atmConfig.record_line.value,
        pos: data.pos,
      }

      // Check if the pattern already exists in the list
      const index = selectedAtmPatterns.map(e => e.pattern).indexOf(item.pattern)

      if (index !== -1) {
        // Remove the pattern from the list
        selectedAtmPatterns.splice(index, 1)

        // Handle table row deselection based on the record type
        if (this.multipleLineRecord) {
          this.removeTableRowSelectionForExtendedUserSelectedPatterns(data.pos[7])
        } else {
          this.removeTableRowSelectionForUserSelectedPatterns(data.pos[7])
        }
      } else {
        // Add the pattern to the list
        selectedAtmPatterns.push(item)
      }

      // Commit the updated list of selected patterns to the store
      this.$store.commit('atm/SET_SELECTED_ATM_PATTERNS', selectedAtmPatterns)
    },

    // Removes table row selection for extended user-selected patterns
    removeTableRowSelectionForExtendedUserSelectedPatterns(posRef) {
      const extendedUserSelectedPatterns = []

      // Process each extended user-selected pattern to check if it matches a record
      this.extendedUserSelectedPatterns.forEach(item => {
        let pageId = null
        let documentId = null
        let batchId = null
        let left
        let top
        let right
        let bottom

        item.forEach(e => {
          const [itemLeft, itemTop, itemRight, itemBottom, itemPageId, itemDocumentId, itemBatchId] = e.pos.split(',')

          // Update positional boundaries and IDs if not set
          if (pageId == null || documentId == null || batchId == null) {
            pageId = itemPageId
            documentId = itemDocumentId
            batchId = itemBatchId
          }

          // Update bounding box dimensions
          if (!left || left > parseInt(itemLeft, 10)) {
            left = parseInt(itemLeft, 10)
          }

          if (!top || top > parseInt(itemTop, 10)) {
            top = parseInt(itemTop, 10)
          }

          if (!right || right < parseInt(itemRight, 10)) {
            right = parseInt(itemRight, 10)
          }

          if (!bottom || bottom < parseInt(itemBottom, 10)) {
            bottom = parseInt(itemBottom, 10)
          }
        })

        // Check if the position matches any ATM pattern record
        const pos = [left, top, right, bottom, pageId, documentId, batchId, posRef, 'green', 'green']

        if (this.atmPatternRecords.includes(pos.join(','))) {
          item.forEach(e => {
            // Update chunk line records
            this.$store.dispatch('atm/updateChunkLineRecords', e.pos)
          })
        } else {
          extendedUserSelectedPatterns.push(item)
        }
      })

      // Commit the updated patterns to the store
      this.$store.commit('atm/SET_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
      this.$store.commit('dataView/SET_MODEL_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
    },

    // Removes table row selection for user-selected patterns
    removeTableRowSelectionForUserSelectedPatterns(posRef) {
      const userSelectedPatterns = []

      // Process each user-selected pattern
      this.userSelectedPatterns.forEach(e => {
        const pos = e.pos.split(',')
        pos[7] = posRef
        pos[9] = 'green'

        // Check if the updated position matches an ATM pattern record
        if (this.atmPatternRecords.includes(pos.join(','))) {
          // Update chunk line records
          this.$store.dispatch('atm/updateChunkLineRecords', e.pos)
        } else {
          userSelectedPatterns.push(e)
        }
      })

      // Commit the updated user-selected patterns to the store
      this.$store.commit('atm/SET_USER_SELECTED_PATTERNS', userSelectedPatterns)
      this.$store.commit('dataView/SET_MODEL_USER_SELECTED_PATTERNS', userSelectedPatterns)
    },

    // Updates the status of ATM pattern records based on the position reference
    updateStatus(data) {
      const posList = []
      const atmPatternRecords = [...this.atmPatternRecords]

      // Iterate over pattern records and update their status
      atmPatternRecords.forEach((e, i) => {
        const highlightedPos = e.split(',')

        const status = highlightedPos[8]
        let refStatus = highlightedPos[9]

        // Toggle the reference status if both are green
        if (status === 'green' && refStatus === 'green') {
          refStatus = 'blank'
        }

        // Update the status based on whether it was auto-checked
        if (highlightedPos[7] === data.posRef) {
          if (data.autoChecked) {
            highlightedPos[8] = 'green'
          } else {
            highlightedPos[8] = status === 'green' ? refStatus : 'green'
          }

          posList.push({ index: i, pos: highlightedPos })
        }
      })

      // Replace old records with updated ones
      posList.forEach((e, index) => {
        atmPatternRecords.splice(e.index - index, 1)
        atmPatternRecords.push(e.pos.join(','))
      })

      // Commit the updated pattern records to the store
      this.$store.commit('atm/SET_ATM_PATTERN_RECORDS', atmPatternRecords)
    },
  },
}
</script>
