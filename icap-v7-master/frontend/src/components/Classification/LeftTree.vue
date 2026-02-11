<template>
  <div ref="scrollContainer">
    <div v-if="classificationData.data && classificationData.data.length">
      <div
        class="d-flex justify-content-between align-items-center border cursor-pointer"
        style="padding: 10px; border-color: #3a3a3a; color: #ffffff;"
        @click.stop="toggleExpandAll"
      >
        <h5 style="margin: 0; font-weight: bold;">
          {{ allExpanded ? '-' : '+' }} {{ batchId }}
        </h5>
        <div
          class="badge badge-primary"
          style="margin-right: 5px;"
        >
          <feather-icon
            :icon="allExpanded ? 'ChevronsUpIcon' : 'ChevronsDownIcon'"
            style="width: 16px; height: 16px;"
          />
        </div>
      </div>
      <b-card
        v-for="(itm, indx) in localGroupedData"
        :key="`card-${indx}`"
        class="border"
        style="margin-bottom: 3px;"
        body-class="p-0"
        :border-variant="itm.expanded? 'primary': ''"
      >
        <b-card-header
          class="d-flex justify-content-between align-items-center"
          style="cursor: pointer; padding: 8px 6px 0 6px;"
          :class="itm.expanded? 'text-primary': 'pb-1'"
          @click="toggleExpandItem(indx)"
        >
          <span>{{ itm.label }}</span>
          <feather-icon
            :key="`icon-${indx}`"
            :icon="itm.expanded ? 'ChevronsUpIcon' : 'ChevronsDownIcon'"
            size="20"
            class="mr-1"
          />
        </b-card-header>
        <b-collapse
          :id="`page-list-${indx}`"
          v-model="itm.expanded"
          role="presentation"
        >
          <div
            v-for="(item, index) in itm.file_data"
            :id="`view-classification-${item.image_path}`"
            :key="item.image_path"
            class="m-1 rounded cursor-pointer overflow-hidden"
            :class="{ 'selected-item': selectedItem === item.image_path }"
            style="min-height: 99px; position: relative;"
            @mouseenter="showRemarksPopover(item.image_path)"
            @mouseleave="showRemarksPopover(' ')"
            @dblclick="showDocPopover(item.image_path)"
            @click="selectedItem = item.image_path"
          >
            <div
              class="flex-grow-1 pointer"
              style="position: relative;"
            >
              <div
                style="position: relative;"
                @click.exact="onClickPage(item)"
              >
                <div
                  class="d-flex flex-column justify-content-between file-index"
                  style="position: absolute; left: 0; right: 0; top: 0; bottom: 48px; z-index: 5;"
                >
                  <div
                    class="d-flex justify-content-between"
                  >
                    <b-badge
                      class="align-self-start"
                      variant="secondary"
                      style="margin: 6px 3px; width: fit-content;"
                    >
                      File: {{ item.file_index + 1 }}
                    </b-badge>
                    <b-badge
                      :key="keyValue + '-package-icon'"
                      class="align-self-end"
                      variant="secondary"
                      style="margin: 6px 3px; width: fit-content;"
                      @click.stop="showDocPopover(item.image_path)"
                    >
                      <div style="width: 20px; height: 20px;">
                        <feather-icon
                          :icon="'SettingsIcon'"
                          style="width: 100%; height: 100%;"
                        />
                      </div>
                    </b-badge>
                  </div>
                  <b-badge
                    v-if="item.user_classified_doc_type || item.name_matching_doc_type || item.auto_classified_doc_type"
                    :style="{'background-color': backgroundClass(item)}"
                    style="margin: 6px 3px; width: fit-content;"
                  >
                    {{ getBadge(item) }}
                  </b-badge>
                </div>
                <v-stage
                  v-if="getFetchedImages[item.imageIndex]"
                  :config="stageConfig"
                >
                  <v-layer
                    :config="{
                      scaleX: (containerSize.width -20)/getFetchedImages[index].width,
                      scaleY: (containerSize.width -20)/getFetchedImages[index].width,
                    }"
                  >
                    <v-image
                      :config="getFetchedImages[item.imageIndex]"
                    />
                  </v-layer>
                </v-stage>
                <div
                  v-else-if="isExcelUrl(item.file_name)"
                  style="height: 188px; background-color: aqua;"
                >
                  <img
                    src="../../assets/images/excel_icon.svg"
                    alt="Excel Thumbnail"
                    style="width: 445px; height:188px;"
                  >
                </div>
                <div
                  v-else
                  class="text-center d-flex align-items-center justify-content-center"
                  style="height: 188px;"
                >
                  <b-spinner variant="primary" />
                </div>
              </div>
              <div
                class="d-flex flex-column justify-content-center"
                :style="{'background-color': backgroundClass(item)}"
                style="position: absolute; left: 0; right: 0; bottom: 0; z-index: 2; min-height: 48px; padding-top: 4px"
              >
                <h5
                  v-if="!item.auto_classified_doc_type && !item.user_classified_doc_type && !item.name_matching_doc_type"
                  class="text-white text-center mb-0"
                >
                  Unknown
                </h5>
                <h5
                  v-if="item"
                  class="text-white text-center mb-0"
                >
                  {{ item.user_classified_doc_type || item.auto_classified_doc_type || item.name_matching_doc_type }}
                </h5>
                <p
                  v-if="item.score"
                  class="text-white text-center mb-0"
                >
                  {{ `Score: ${item.score.toFixed(2) }` }}
                </p>
              </div>
            </div>
            <b-popover
              v-if="activeDocBPopover === item.image_path"
              :show.sync="activeDocBPopover === item.image_path"
              :target="`view-classification-${ item.image_path }`"
              placement="auto"
              boundary="window"
              custom-class="no-padding-popover"
            >
              <ul
                class="nav-pills"
                style="cursor: pointer; padding-inline-start: 0; margin: -10px -20px;"
              >
                <li
                  v-for="(type, idx) in classificationData.doc_types"
                  :key="type + idx"
                  class="border-bottom p-1 nav-link"
                  :class="item.auto_classified_doc_type === type? 'bg-primary': 'bg-white'"
                  style="list-style-type: none;"
                  @click="closePopover(item.image_path, type)"
                >
                  <span
                    :class="item.auto_classified_doc_type === type? 'text-white': 'text-primary'"
                  >
                    {{ type }}
                  </span>
                </li>
              </ul>
            </b-popover>
            <b-popover
              v-if="activeToolBPopover === item.image_path"
              :show.sync="activeToolBPopover === item.image_path"
              :target="`view-classification-${ item.image_path }`"
              placement="topright"
              boundary="scrollParent"
              custom-class="no-padding-popover"
            >
              <ul
                class="mb-0 pl-1"
                style="cursor: pointer; padding-inline-start: 0;"
              >
                <template v-if="item.remarks && item.remarks[0] && item.remarks[0].length">
                  <li
                    v-for="(type, idx) in item.item.remarks[0]"
                    :key="type + idx"
                  >
                    <feather-icon
                      icon="ChevronsRightIcon"
                      size="16"
                      class="text-primary"
                    />
                    <span
                      class="text-primary"
                    >
                      {{ type }}
                    </span>
                  </li>
                </template>
                <li
                  class="text-primary"
                >
                  No Remarks
                </li>
              </ul>
            </b-popover>
          </div>
        </b-collapse>
      </b-card>
    </div>
  </div>
</template>
<script>
import bus from '@/bus'
import {
  BPopover, VBTooltip, BSpinner, BBadge, BCard, BCardHeader, BCollapse, VBToggle,
} from 'bootstrap-vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
    'b-toggle': VBToggle,
  },
  components: {
    BPopover,
    BSpinner,
    BBadge,
    BCard,
    BCardHeader,
    BCollapse,
  },
  data() {
    return {
      activeDocBPopover: ' ',
      activeDocBPopover2: ' ',
      activeToolBPopover: ' ',
      loadingError: null,
      loading: null,
      visible: false,
      containerSize: {
        width: 1,
        height: 0,
      },
      keyValue: 0,
      selectedItem: null,
      localGroupedData: [],
    }
  },
  computed: {
    batchId() {
      return this.$route.params.id
    },
    classificationData() {
      return this.$store.getters['classifications/getClassificationData']
    },
    groupedData() {
      const data = { ...this.classificationData }

      data.data.forEach((element, index) => {
        // eslint-disable-next-line no-param-reassign
        element.imageIndex = index
        // Ensure expanded is defined on each item in Vuex
        if (element.expanded === undefined) {
          this.$set(element, 'expanded', false)
        }
      })
      // Ensure expanded state is defined independently for each grouped item
      const types = [...new Set(data.data.map(item => item.file_name))]

      const groupedData = data.data.reduce((acc, item) => {
        const key = item.file_index
        if (!acc[key]) {
          acc[key] = {
            label: types[Object.keys(acc).length] || `Type ${Object.keys(acc).length + 1}`,
            expanded: false,
            file_data: [],
          }
        }
        acc[key].file_data.push(item)
        return acc
      }, {})

      // Return an array for template iteration with independent expanded state
      return Object.values(groupedData)
    },
    getFetchedImages() {
      return this.$store.getters['classifications/getFetchedImages']
    },
    stageConfig() {
      return {
        width: window.innerWidth,
        height: 188,
        x: 0,
        y: 0,
      }
    },
    allExpanded() {
      return this.localGroupedData.some(group => group.expanded === true)
    },
  },
  watch: {
    // groupedData: {
    //   immediate: true,
    //   handler(newGroupedData) {
    //     if (newGroupedData && newGroupedData.length > 0) {
    //       this.localGroupedData = newGroupedData.map(group => ({
    //         ...group,
    //         expanded: group.expanded || false, // Set default expanded state if needed
    //       }))
    //     }
    //   },
    // },
    classificationData(value) {
      if (value.data.length) {
        this.containerSize.width = (this.$refs.scrollContainer.clientWidth) - 8
        this.containerSize.height = (this.$refs.scrollContainer.clientHeight) - 8
      }
    },
  },
  created() {
    bus.$on('classification/clearTreeDocSelection', this.clearPopover)
  },
  async mounted() {
    await this.fetchManual()
    await this.fetchRaJson()

    if (this.groupedData && this.groupedData.length > 0) {
      this.localGroupedData = this.groupedData.map(group => ({
        ...group,
        expanded: group.expanded || false,
      }))
    }
  },
  destroyed() {
    bus.$on('classification/clearTreeDocSelection', this.clearPopover)
  },
  methods: {
    showDocPopover(imagePath) {
      if (this.classificationData.manual_classification_status === 'ready') {
        this.activeToolBPopover = ''
        setTimeout(() => {
          this.activeDocBPopover = imagePath
        }, 1)
      }
    },
    showRemarksPopover(imagePath) {
      if (this.classificationData.manual_classification_status === 'ready') {
        this.activeToolBPopover = imagePath
      }
    },
    clearPopover() {
      this.activeDocBPopover = ''
    },
    closePopover(imagePath, type) {
      this.activeDocBPopover = ''

      // Update classificationData.data directly based on localGroupedData's expanded state
      this.classificationData.data.forEach(item => {
        const matchingLocalItem = this.localGroupedData
          .flatMap(group => group.file_data) // Flatten to access all items
          .find(localItem => localItem.image_path === item.image_path)
        if (item.image_path === imagePath) {
          // eslint-disable-next-line no-param-reassign
          item.user_classified_doc_type = type
          // eslint-disable-next-line no-param-reassign
          item.color = 'green'
        }

        // Update expanded state from localGroupedData if matching item found
        if (matchingLocalItem) {
          // eslint-disable-next-line no-param-reassign
          item.expanded = matchingLocalItem.expanded
        }
      })

      this.$store.commit('classifications/SET_CLASSIFICATION_DATA', this.classificationData)
      this.$store.commit('classifications/SET_VERIFIED', false)
    },
    onClickPage(item) {
      if (!item.file_name.endsWith('xlsx')) {
        const startIndex = item?.layout_file_path?.indexOf('TM') || item?.image_path?.indexOf('tm')
        const pageId = item?.layout_file_path?.substring(startIndex, startIndex + 8) || item?.image_path?.substring(startIndex, startIndex + 8)
        bus.$emit('isShowExcel', false)
        bus.$emit('scrollToPage', pageId.toUpperCase())
        this.clearPopover()
      } else {
        bus.$emit('isShowExcel', true)
        bus.$emit('selectedExcelItem', item.file_name)
        this.clearPopover()
      }
    },
    backgroundClass(item) {
      const colorCodes = {
        green: 'rgba(40, 199, 111, .8)',
        yellow: 'rgba(255, 159, 67, .8)',
        red: 'rgba(234, 84, 85, .8)',
      }
      if (item.name_matching_doc_type) {
        return colorCodes.green
      }
      return colorCodes[item.color]
    },
    async fetchRaJson() {
      await this.$store.dispatch('classifications/fetchRaJsonClassification', this.batchId)
    },
    async fetchManual() {
      await this.$store.dispatch('classifications/fetchManualClassification', this.batchId)
    },
    formattedRemarks(remarks) {
      if (!remarks || !remarks.length) {
        return 'No remarks'
      }
      return remarks.flat().join(', ')
    },
    getBadge(item) {
      switch (true) {
        case !!item.user_classified_doc_type:
          return 'user'
        case !!item.auto_classified_doc_type:
          return 'auto'
        case !!item.name_matching_doc_type:
          return 'name matching'
        default:
          return ''
      }
    },
    toggleExpandAll() {
      if (!this.localGroupedData || this.localGroupedData.length === 0) {
        return // Exit if localGroupedData is undefined or empty
      }
      const newExpandState = !this.allExpanded
      this.localGroupedData.forEach((group, index) => {
        // Use Vue.set to ensure reactivity on each group's expanded property
        this.$set(this.localGroupedData[index], 'expanded', newExpandState)
      })
    },
    toggleExpandItem(index) {
      // Toggle expanded state for the specific item in localGroupedData
      this.$set(this.localGroupedData[index], 'expanded', !this.localGroupedData[index].expanded)
    },

    isExcelUrl(urls) {
      const excelExtensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
      const status = excelExtensions.some(extension => urls?.endsWith(extension))
      return status
    },
  },
}
</script>

<style scoped lang='scss'>
::v-deep .no-padding-popover .popover-body {
  padding: 0 !important;
}
.wide-popover {
  max-width: 100px;
}
.file-index {
  font-size: 1.2rem;
  width: 100%;
  color: white;
  font-weight: bold;
  text-align: center;
  background: rgba(0, 0, 0, 0.2) ;
}
.selected-item {
  border: 2px solid #007bff;
  box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
  background-color: rgba(0, 123, 255, 0.1);
}
</style>
