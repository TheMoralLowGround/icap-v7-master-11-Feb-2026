<template>
  <div class="h-100">
    <b-card style="height: 100%;">
      <div class="d-flex justify-content-end align-items-center mb-1 gap-3">
        <div class="flex-grow-1">
          <span
            v-if="isPageLoading"
            class="font-weight-bold"
          >
            Loaded Pages: {{ loadedFiles }} / {{ totalFiles }}
          </span>
        </div>
        <feather-icon
          v-b-tooltip.hover
          icon="ZoomInIcon"
          size="20"
          class="cursor-pointer"
          title="Zoom In"
          @click="zoomIn()"
        />
        <feather-icon
          v-b-tooltip.hover
          icon="ZoomOutIcon"
          size="20"
          class="cursor-pointer"
          title="Zoom Out"
          @click="zoomOut()"
        />
        <feather-icon
          v-b-tooltip.hover
          icon="MinimizeIcon"
          size="20"
          class="cursor-pointer"
          title="Fit to width"
          @click="fitToWidth"
        />
        <b-button
          v-if="classificationData.manual_classification_status === 'ready'"
          variant="primary"
          @click="testClassification"
        >
          Test
          <b-spinner
            v-if="submitting"
            small
            label="Small Spinner"
          />
        </b-button>
        <b-button
          v-if="classificationData.manual_classification_status === 'ready'"
          variant="primary"
          :disabled="!getVerified"
          @click="isOpenSubmit = true"
        >
          Submit
        </b-button>
      </div>
      <div class="h-100 d-flex flex-column">
        <div class="flex-grow-1">
          <div class="image-viewer">
            <image-tree
              class="canvas-view"
              @calculate-loaded-files="onCalculateLoadedFiles"
            />
          </div>
        </div>
      </div>
    </b-card>
    <ConfirmSubmit
      v-if="isOpenSubmit"
      @modal-closed="isOpenSubmit = false"
      @submited="isOpenSubmit = false"
    />
  </div>
</template>
<script>
import axios from 'axios'
import {
  VBTooltip, BCard, BButton, BSpinner,
} from 'bootstrap-vue'
import ImageTree from '@/components/Classification/ImageTree.vue'
import ConfirmSubmit from '@/components/Classification/ConfirmSubmit.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import bus from '@/bus'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    ImageTree,
    ConfirmSubmit,
    BCard,
    BButton,
    BSpinner,
  },
  data() {
    return {
      isOpenSubmit: false,
      verified: false,
      submitting: false,
      loadedFiles: 0,
      totalFiles: 0,
    }
  },
  computed: {
    classificationData() {
      return this.$store.getters['classifications/getClassificationData']
    },
    currentCanvas() {
      // return this.$store.getters['training/getCurrentCanvas']
      return {
        value: '2',
        image: '',
      }
    },
    canvasList() {
      return this.$store.getters['training/getCanvasDataList']
    },
    getVerified() {
      return this.$store.getters['classifications/getVerified']
    },
    getZoomValue() {
      return this.$store.getters['training/getZoomValue']
    },
    getToolbarView() {
      return this.$store.getters['training/getToolbarView']
    },
    getTempImageList() {
      return this.$store.getters['batch/getTempImageList']
    },
    isPageLoading() {
      return this.totalFiles && this.loadedFiles < this.totalFiles
    },
  },
  watch: {
    currentCanvas() {
      this.$store.dispatch('training/setToolbarView', 'text')
    },
  },
  methods: {
    ChangeDocumentStatus() {
      const parts = this.currentCanvas.image.split('/')
      this.currentCanvas.value = !this.currentCanvas.value
      const payload = {
        batch_id: parts[parts.length - 2],
        page_id: parts[parts.length - 1],
        page_status: this.currentCanvas.value,
      }
      axios.post('pipeline/update_page_status/', payload)
        .then(res => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          this.$store.dispatch('training/setValueById', this.currentCanvas)
          if (this.canvasList.length && this.currentCanvas.value) {
            const index = this.canvasList.findIndex(element => element.id === this.currentCanvas.id)
            if (index < this.canvasList.length - 1) {
              this.$store.dispatch('training/setCurrentCanvas', {
                image: this.canvasList[index + 1],
              })
            }
          }
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
    },
    zoomIn() {
      this.$store.dispatch('batch/zoomIn')
    },
    zoomOut() {
      this.$store.dispatch('batch/zoomOut')
    },
    fitToWidth() {
      bus.$emit('fitToWidthClassification')
    },
    setToolbarView() {
      const value = this.getToolbarView === 'text' ? 'table' : 'text'
      this.$store.dispatch('training/setToolbarView', value)
    },
    async testClassification() {
      const batchId = this.$route.params.id
      this.submitting = true
      this.submitting = await this.$store.dispatch('classifications/testClassification', batchId)
    },
    async verifyClassification() {
      const batchId = this.$route.params.id
      const isSucess = await this.$store.dispatch('classifications/verifyClassification', {
        train_batch_id: batchId,
        forceSubmit: false,
      })
      if (isSucess) {
        this.$router.push({ name: 'training' })
      }
    },
    onCalculateLoadedFiles(totalFiles) {
      this.loadedFiles += 1
      this.totalFiles = totalFiles
    },
  },
}
</script>

<style lang="scss" scoped>
.image-viewer {
    height: 100%;
    position: relative;
}
.canvas-view {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
}
.tab-pane {
  height: 100%;
}
</style>
