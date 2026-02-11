<template>
  <div
    v-if="atmWizardTabs.tableRowSelection.active"
    class="mx-1"
  >
    <b-form-checkbox
      v-model="multipleLineRecord"
      class="mx-1 my-1"
      name="multipleLineRecord"
      switch
      inline
      @change="onSwitch"
    >
      Multiple Row Selection
    </b-form-checkbox>

    <!-- Single Row Selection Tab -->
    <div
      v-if="!multipleLineRecord"
      class="mx-1"
    >
      <validation-observer
        ref="selectionRules"
        tag="form"
      >
        <b-form-group
          label="Please select one or multiple table lines"
        >
          <validation-provider
            #default="{ errors }"
            name="pattern"
            rules="required"
          >
            <div class="d-flex align-items-center">
              <b-form-input
                :value="userSelectedPatterns.map(e => e.pattern).join(',  ')"
                type="text"
                name="pattern"
                placeholder="Please select one or multiple table lines"
                class="w-50"
                disabled
              />

              <feather-icon
                v-if="userSelectedPatterns.length"
                icon="TrashIcon"
                size="20"
                class="cursor-pointer mx-1"
                @click="resetUserSelectedPatterns"
              />
            </div>
            <small class="text-danger">{{ errors[0] ? 'Please Select Table rows' : '' }}</small>
          </validation-provider>
        </b-form-group>
      </validation-observer>
    </div>

    <!-- Multiple Row Selection Tab -->
    <div
      v-if="multipleLineRecord"
    >
      <pipe-separated-input
        :value="extendedUserSelectedPatterns.map(e => e.map(i => i.pattern).join(',  ')).join('|')"
        label="Multiple Row Selection"
        selection-value-attr="text"
        listenable-input
        validation-rules="selectTextFromImage"
        validation-key="extendedUserSelectedPatterns"
        readonly
        inline-add-button
        :width="50"
        @focus="onFocus"
        @item-deleted="onDeleteExtendedUserSelectedPatterns($event)"
        @click="onClick"
      />
    </div>
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BFormGroup, BFormInput, BFormCheckbox,
} from 'bootstrap-vue'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import PipeSeparatedInput from '@/components/UI/PipeSeparatedInput.vue'

export default {
  components: {
    BFormGroup,
    BFormInput,
    // BButtonGroup,
    // BButton,
    BFormCheckbox,
    ValidationProvider,
    ValidationObserver,
    PipeSeparatedInput,
  },
  data() {
    return {
      scrollTop: 0,
      scrollToTopIconHover: false,
      selectedIndex: 0,
    }
  },
  computed: {
    // Retrieves the current batch ID from the Vuex store
    batchId() {
      return this.$store.getters['batch/batch'].id
    },
    // Retrieves ATM wizard tab information from the Vuex store
    atmWizardTabs() {
      return this.$store.getters['atm/atmWizardTabs']
    },
    // Retrieves chunk line records from the Vuex store
    chunkLineRecords() {
      return this.$store.getters['atm/chunkLineRecords']
    },
    // Retrieves user-selected patterns from the Vuex store
    userSelectedPatterns() {
      return this.$store.getters['atm/userSelectedPatterns']
    },
    // Retrieves extended user-selected patterns from the Vuex store
    extendedUserSelectedPatterns() {
      return this.$store.getters['atm/extendedUserSelectedPatterns']
    },
    // Alias for retrieving extended user-selected patterns from the Vuex store
    getExtendedUserSelectedPatterns() {
      return this.$store.getters['atm/extendedUserSelectedPatterns']
    },
    // Two-way binding for multipleLineRecord:
    // Getter retrieves the value from the Vuex store.
    // Setter commits a new value to the Vuex store.
    multipleLineRecord: {
      get() {
        return this.$store.getters['dataView/modelMultipleLineRecord']
      },
      set(value) {
        this.$store.commit('dataView/SET_MODEL_MULTIPLE_LINE_RECORD', value)
      },
    },
  },
  created() {
    // Sets up the initial state for the component
    this.setInternalState()
    // Subscribes to the 'atm/selectTableRow' event from the event bus
    bus.$on('atm/selectTableRow', this.selectTableRow)
  },
  destroyed() {
    // Unsubscribes from the 'atm/selectTableRow' event to prevent memory leaks
    bus.$off('atm/selectTableRow', this.selectTableRow)
    // Resets the user-selected patterns when the component is destroyed
    this.resetUserSelectedPatterns()
  },
  methods: {
  // Initializes the component's internal state based on wizard tabs and patterns
    async setInternalState() {
      if (this.atmWizardTabs.tableRowSelection.active) {
        // Fetches chunk data if table row selection is active
        await this.$store.dispatch('atm/fetchAtmChunkData')
      }

      // Refreshes patterns based on the multipleLineRecord state
      if (this.multipleLineRecord) {
        this.$store.dispatch('atm/refreshExtendUserSelectedPatterns')
      } else {
        this.$store.dispatch('atm/refreshUserSelectedPatterns')
      }
    },

    // Handles click events and calculates positions for scrolling
    onClick(value) {
      const index = value === -1 ? 0 : value

      // Creates a copy of the extended user-selected patterns
      const extendedUserSelectedPatterns = [...this.extendedUserSelectedPatterns]

      if (index < extendedUserSelectedPatterns.length && extendedUserSelectedPatterns[index].length) {
        let pageId = null
        let documentId = null
        let batchId = null
        let left
        let top
        let right
        let bottom

        // Iterates through each position and calculates bounds
        extendedUserSelectedPatterns[index].forEach(e => {
          const [itemLeft, itemTop, itemRight, itemBottom, itemPageId, itemDocumentId, itemBatchId] = e.pos.split(',')

          if (pageId == null || documentId == null || batchId == null) {
            pageId = itemPageId
            documentId = itemDocumentId
            batchId = itemBatchId
          }

          // Updates left, top, right, and bottom boundaries
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

        // Dispatches an action to scroll to the calculated position
        this.$store.dispatch('batch/scrollToPos', [left, top, right, bottom, pageId, documentId, batchId])
      }
    },

    // Toggles patterns and updates chunk line records
    onSwitch(value) {
      // Clears existing patterns in the Vuex store
      this.$store.commit('atm/SET_ATM_PATTERNS', [])
      this.$store.commit('atm/SET_SELECTED_ATM_PATTERNS', [])

      if (value) {
        // Updates chunk line records for user-selected patterns
        this.userSelectedPatterns.forEach(e => {
          this.$store.dispatch('atm/updateChunkLineRecords', e.pos)
        })
        // Refreshes extended user-selected patterns
        this.$store.dispatch('atm/refreshExtendUserSelectedPatterns')
      } else {
        // Updates chunk line records for extended user-selected patterns
        this.extendedUserSelectedPatterns.forEach(item => {
          item.forEach(e => {
            this.$store.dispatch('atm/updateChunkLineRecords', e.pos)
          })
        })
        // Refreshes user-selected patterns
        this.$store.dispatch('atm/refreshUserSelectedPatterns')
      }
    },

    // Updates the selected index for focus
    onFocus(index) {
      this.selectedIndex = index
    },

    // Resets the user-selected patterns in the Vuex store
    resetUserSelectedPatterns() {
      this.userSelectedPatterns.forEach(e => {
        this.$store.dispatch('atm/updateChunkLineRecords', e.pos)
      })

      // Clears user-selected patterns in the Vuex store
      this.$store.commit('atm/SET_USER_SELECTED_PATTERNS', [])
    },
    async selectTableRow(posRef) {
      const pos = await this.$store.dispatch('atm/updateChunkLineRecords', posRef)

      if (!pos) {
        return
      }

      if (this.multipleLineRecord) {
        this.updateExpandedUserSelectedPatterns(posRef, pos)

        return
      }

      this.updateUserSelectedPatterns(posRef, pos)
    },
    updateUserSelectedPatterns(posRef, pos) {
      let userSelectedPatterns = [...this.userSelectedPatterns]

      if (userSelectedPatterns.map(e => e.pos).includes(posRef)) {
        userSelectedPatterns = userSelectedPatterns.filter(e => e.pos !== posRef)
      } else {
        userSelectedPatterns.push({
          batchId: this.batchId,
          pattern: pos[9].replaceAll('*comma*', ','),
          pos: pos.join(','),
        })
      }

      this.$store.commit('atm/SET_USER_SELECTED_PATTERNS', userSelectedPatterns)
      this.$store.commit('dataView/SET_MODEL_USER_SELECTED_PATTERNS', userSelectedPatterns)
    },
    updateExpandedUserSelectedPatterns(posRef, pos) {
      const extendedUserSelectedPatterns = [...this.extendedUserSelectedPatterns]
      let index = this.selectedIndex === -1 ? 0 : this.selectedIndex

      // check undefined, if so then replace with empty array
      extendedUserSelectedPatterns.forEach((e, i) => {
        if (!e) {
          extendedUserSelectedPatterns[i] = []
        }
      })

      // Find correct index for unselect when index is not properly selected by user.
      if (pos[8] === 'blank') {
        extendedUserSelectedPatterns.every((item, idx) => {
          if (item.map(e => e.pos).includes(posRef)) {
            index = idx
            return false
          }

          return true
        })
      }

      // create empty array if necessary. Ex. index is greater than the length
      if (!extendedUserSelectedPatterns[index]) {
        extendedUserSelectedPatterns[index] = []
      }

      // If unselect, then remove
      if (extendedUserSelectedPatterns[index].map(e => e.pos).includes(posRef)) {
        extendedUserSelectedPatterns[index] = extendedUserSelectedPatterns[index].filter(e => e.pos !== posRef)

        if (!extendedUserSelectedPatterns[index].length) {
          extendedUserSelectedPatterns.splice(index, 1)
        }
      } else {
        // If select, then add

        // If not empty
        if (extendedUserSelectedPatterns[index].length) {
          const lastIndexPageIds = extendedUserSelectedPatterns.map(e => {
            if (!e.length) {
              return -1
            }

            const elmPpos = e[e.length - 1].pos.split(',')

            return `${elmPpos[4]}_${elmPpos[6]}`
          })

          // If page id not equal to the current index
          if (lastIndexPageIds[index] !== `${pos[4]}_${pos[6]}`) {
            // if page id is not included among the previous selected patterns
            if (!lastIndexPageIds.includes(`${pos[4]}_${pos[6]}`)) {
              index = extendedUserSelectedPatterns.length
              extendedUserSelectedPatterns[index] = []
            } else {
              // Generate distance array from topDistance & bottomDistance of the position
              const distances = extendedUserSelectedPatterns.map(e => {
                if (!e.length) {
                  return -1
                }

                const lastIndexPos = e[e.length - 1].pos.split(',')

                // matching the page id
                if (`${lastIndexPos[4]}_${lastIndexPos[6]}` !== `${pos[4]}_${pos[6]}`) {
                  return -1
                }

                const topDistance = Math.abs(parseInt(pos[1], 10) - parseInt(lastIndexPos[1], 10))
                const bottomDistance = Math.abs(parseInt(pos[3], 10) - parseInt(lastIndexPos[3], 10))

                return Math.min(topDistance, bottomDistance)
              })

              // Find the correct index from distance array to push
              let calculatedIndex = -1

              distances.forEach((e, i) => {
                if (e === -1) {
                  return
                }

                if (calculatedIndex === -1 || i === 0 || distances[calculatedIndex] > e) {
                  calculatedIndex = i
                }
              })

              if (calculatedIndex !== -1) {
                index = calculatedIndex
              }
            }
          }
        }

        // Check order of selected patterns & re-order if necessary
        const botomPositions = extendedUserSelectedPatterns[index].map(e => parseInt(e.pos.split(',')[3], 10))

        let subIndex = extendedUserSelectedPatterns[index].length

        botomPositions.forEach((e, i) => {
          if (parseInt(pos[3], 10) < e && (subIndex === extendedUserSelectedPatterns[index].length || botomPositions[subIndex] > e)) {
            subIndex = i
          }
        })

        // update extendedUserSelectedPatterns array
        extendedUserSelectedPatterns[index].splice(subIndex, 0, {
          batchId: this.batchId,
          pattern: pos[9].replaceAll('*comma*', ','),
          pos: pos.join(','),
        })
      }

      // update the changes in the store
      this.$store.commit('atm/SET_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
      this.$store.commit('dataView/SET_MODEL_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
    },
    onDeleteExtendedUserSelectedPatterns(index) {
      this.selectedIndex = 0
      const extendedUserSelectedPatterns = [...this.extendedUserSelectedPatterns]

      if (index !== -1 && index < extendedUserSelectedPatterns.length) {
        extendedUserSelectedPatterns[index].forEach(async e => {
          await this.$store.dispatch('atm/updateChunkLineRecords', e.pos)
        })

        extendedUserSelectedPatterns.splice(index, 1)
      }

      this.$store.commit('atm/SET_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
      this.$store.commit('dataView/SET_MODEL_EXTENDED_USER_SELECTED_PATTERNS', extendedUserSelectedPatterns)
    },
    onChangeNestedTab(parent, key) {
      const atmWizardTabs = { ...this.atmWizardTabs }

      if (atmWizardTabs[parent].children[key].active) {
        return
      }

      Object.keys(atmWizardTabs[parent].children).forEach(keyItem => {
        if (key === keyItem) {
          atmWizardTabs[parent].children[keyItem].active = true
        } else {
          atmWizardTabs[parent].children[keyItem].active = false
        }
      })

      this.$store.commit('atm/SET_ATM_WIZARD_TABS', atmWizardTabs)
    },
  },
}
</script>
