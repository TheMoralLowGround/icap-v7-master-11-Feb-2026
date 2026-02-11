<template>
  <div
    class="h-100"
    style="overflow-y: auto;"
  >
    <CanvasViewClassification
      v-if="pages.length && !isExcelVisible"
      class="canvas-view"
      :pages="pages"
    />
    <div
      v-if="excelUrl && isExcelVisible"
      style="height:90%; padding-top: 10px;"
    >
      <ExcelViewer
        :url="excelUrl"
      />
    </div>
    <div
      v-if="!excelUrl && !pages.length"
      class="text-center h-100 d-flex align-items-center justify-content-center"
    >
      <b-spinner variant="primary" />
    </div>
  </div>
</template>

<script>
import Tiff from 'tiff.js'
import {
  BSpinner,
} from 'bootstrap-vue'
import { getClassificationMediaURL } from '@/store/batch/helper'
import CanvasViewClassification from '@/components/Classification/CanvasViewClassification.vue'
import ExcelViewer from '@/components/Classification/ExcelViewer.vue'
import bus from '@/bus'

export default {
  components: {
    CanvasViewClassification,
    ExcelViewer,
    BSpinner,
  },
  data() {
    return {
      pages: [],
      tempPages: [],
      isExcelVisible: false,
      selectedExcelItem: false,
    }
  },
  computed: {
    classificationData() {
      return this.$store.getters['classifications/getClassificationData']
    },
    classificationRaJson() {
      return this.$store.getters['classifications/getClassificationRaJosn']
    },
    getAlldocs() {
      return this.$store.getters['classifications/getAlldocs']
    },
    excelUrl() {
      if (this.classificationData && this.classificationData.data && this.classificationData.data.length) {
        const element = this.classificationData.data.find(el => el.file_name && this.isExcelUrl(el.file_name) && el.file_name === this.selectedExcelItem)
        // If a matching element is found, return the URL
        if (element) {
          return getClassificationMediaURL(element.image_path)
        }
      }
      // Return null or a default value if no match is found
      return null
    },
  },
  watch: {
    classificationRaJson(value) {
      if (value) {
        this.loadPages()
      }
    },
  },
  created() {
    bus.$on('selectedExcelItem', value => {
      this.selectedExcelItem = value
    })
    bus.$on('isShowExcel', value => {
      this.isExcelVisible = value
    })
  },
  destroyed() {
    bus.$off('isShowExcel')
    bus.$off('selectedExcelItem')
  },
  methods: {
    async loadPages() {
      if (this.getAlldocs.length) {
        this.loading = true
        this.pages = []
        const pages = this.getAlldocs.map((page, index) => {
          const imagePath = getClassificationMediaURL(this.classificationData.data[index].image_path)
          let positionInfo
          if (page.pos) {
            positionInfo = page.pos.split(',').map(num => +num)
          }
          return {
            id: page.id,
            pos: page.pos,
            width: positionInfo[2],
            height: positionInfo[3],
            imageUrl: imagePath,
            image: null,
            wordNodes: page.children,
            styles: page.styles,
          }
        })
        this.tempPages[pages.length - 1] = undefined
        this.isDocidChanged = false
        const assignPages = async imageIndex => {
          try {
            const image = await this.fetchImage(pages[imageIndex].imageUrl)
            this.$emit('calculate-loaded-files', pages.length)
            pages[imageIndex].image = image
            this.$store.commit('classifications/MODIFY_FETCHED_IMAGE_LIST', {
              image,
              index: imageIndex,
              width: pages[imageIndex].width,
              height: pages[imageIndex].height,
            })

            if (this.pages.length === imageIndex) {
              this.pages.push(pages[imageIndex])
              let currentIndex = imageIndex + 1
              let nextPage
              if (currentIndex < pages.length) {
                nextPage = this.tempPages[currentIndex]
              }
              while (nextPage !== undefined) {
                this.pages.push(nextPage)
                currentIndex += 1
                if (currentIndex >= pages.length) {
                  break
                }
                nextPage = this.tempPages[currentIndex]
              }
            } else {
              this.tempPages[imageIndex] = pages[imageIndex]
              if ((pages.length - 1) === imageIndex) {
                setTimeout(() => {
                  for (let indexLocal = this.pages.length; indexLocal < this.tempPages.length; indexLocal += 1) {
                    if (this.tempPages[indexLocal] === undefined) {
                      break
                    }
                    this.pages.push(this.tempPages[indexLocal])
                  }
                }, 1000)
              }
            }
          } catch (error) {
            this.loadingError = error.message
          }
          this.loading = false
        }

        let index = 0
        while (index < pages.length) {
          if (!this.isDocidChanged && !this.cancelLoading) {
            assignPages(index)
            index += 1
          } else {
            this.isDocidChanged = false
            this.loading = true
            this.$emit('calculate-loaded-files', 0)
            break
          }
        }
        this.$store.commit('batch/SET_TEMP_IMGE_LIST', this.pages)
      }
    },
    async fetchImage(imageUrl) {
      try {
        const response = await fetch(imageUrl)
        const buffer = await response.arrayBuffer()
        const tiff = new Tiff({ buffer })
        return tiff.toCanvas()
      } catch (error) {
        throw new Error('Error loading image')
      }
    },
    isExcelUrl(urls) {
      const excelExtensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
      const status = excelExtensions.some(extension => urls.endsWith(extension))
      return status
    },
  },
}
</script>
