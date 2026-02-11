<template>
  <div class="timeline-wrapper">
    <b-spinner
      v-if="autoInitialize && loading"
      small
      label="Small Spinner"
    />
    <template v-if="(autoInitialize && !loading) || !autoInitialize">
      <feather-icon
        :id="`view-timeline-${batchId}`"
        v-b-tooltip.hover
        icon="EyeIcon"
        :size="iconSize"
        title="View Timeline"
        class="cursor-pointer"
        :class="{
          'text-warning': autoInitialize && hasWarnings
        }"
      />
      <b-popover
        ref="popoverRef"
        :show.sync="showDetails"
        :target="`view-timeline-${batchId}`"
        :placement="placement"
        boundary="window"
        custom-class="timeline-popover low-z-index-popover"
      >
        <timeline-detail
          :batch-id="batchId"
          :loading="loading"
          :loading-error="loadingError"
          :logs="logs"
          @close="onShowDetailsChange"
        />
      </b-popover>
    </template>
  </div>
</template>

<script>
import {
  VBTooltip, BPopover, BSpinner,
} from 'bootstrap-vue'
import axios from 'axios'
import WS from '@/utils/ws'
import bus from '@/bus'
import TimelineDetail from '@/components/UI/Timeline/TimelineDetail.vue'

export default {
  name: 'Timeline',
  components: {
    BPopover,
    TimelineDetail,
    BSpinner,
  },
  directives: {
    'b-tooltip': VBTooltip,
  },
  props: {
    batchId: {
      type: String,
      required: true,
    },
    placement: {
      type: String,
      required: false,
      default: 'auto',
    },
    iconSize: {
      type: String,
      required: true,
    },
    autoInitialize: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      loading: false,
      loadingError: null,
      logs: [],
      showDetails: false,
    }
  },
  computed: {
    hasWarnings() {
      if (this.loadingError) {
        return true
      }
      let { logs } = this
      const lastOperationLogIndex = this.logs.findIndex(log => log.status === 'retest' || log.status === 'export')
      if (lastOperationLogIndex !== -1) {
        logs = logs.slice(0, lastOperationLogIndex)
      }
      return logs.some(log => log.status === 'warning' || log.status === 'failed')
    },
  },
  watch: {
    batchId(_, oldValue) {
      if (this.autoInitialize) {
        this.cleanup(oldValue)
        this.initialize()
      }
    },
    showDetails(newVal) {
      if (!this.autoInitialize) {
        if (newVal) {
          this.initialize()
        } else {
          this.cleanup()
        }
      }
      if (newVal) {
        // Wait for popover to render in DOM before adding listeners
        this.$nextTick(() => {
          document.addEventListener('click', this.handleOutsideClick)
          document.addEventListener('mousedown', this.handleOutsideClick)
        })
      } else {
        document.removeEventListener('click', this.handleOutsideClick)
        document.removeEventListener('mousedown', this.handleOutsideClick)
      }
    },
  },
  created() {
    if (this.autoInitialize) {
      this.initialize()
    }
    bus.$on('setTimelineID', this.setActiveId)
  },
  destroyed() {
    if (this.autoInitialize) {
      this.cleanup()
    }
    bus.$off('setTimelineID', this.setActiveId)
  },
  methods: {
    initialize() {
      this.fetchTimelineData()
      WS.joinRoom(`batch_status_${this.batchId}`)
      bus.$on('wsData/batchStatus', this.onBatchStatus)
    },
    cleanup(batchId = null) {
      WS.leaveRoom(`batch_status_${batchId || this.batchId}`)
      bus.$off('wsData/batchStatus', this.onBatchStatus)
      this.logs = []
    },
    fetchTimelineData() {
      this.loading = true
      this.loadingError = null
      axios.get(`/batch_status/${this.batchId}`)
        .then(res => {
          this.logs = res.data
          this.loading = false
          this.$store.commit('batch/SET_STATUS', {
            status: res.data[0].status,
            remarks: res.data[0].remarks,
            event_time: res.data[0].event_time,
          })
        })
        .catch(error => {
          this.loadingError = error?.res?.data?.detail || 'Error fetching timeline data'
          this.loading = false
        })
    },
    onBatchStatus(data) {
      if (this.batchId === data.batch_id) {
        this.logs.unshift({ ...data })
      }
    },
    onShowDetailsChange(showDetails = false) {
      this.showDetails = showDetails && this.logs[0].batch_id === this.batchId

      this.$emit('show-details-change', showDetails)
    },
    setActiveId(value) {
      this.showDetails = value === this.batchId
    },
    handleOutsideClick(event) {
      const triggerEl = document.getElementById(`view-timeline-${this.batchId}`)

      // Don't close if clicking on the trigger
      if (triggerEl && triggerEl.contains(event.target)) {
        return
      }

      // Ignore clicks from temporary anchor elements created by download libraries (e.g., downloadjs)
      // These anchors are typically appended to document.body and removed immediately
      if (event.target.tagName === 'A'
        && (event.target.hasAttribute('download') || !event.target.href || event.target.style.display === 'none')) {
        return
      }

      // Find all popovers with timeline-popover class
      const allPopovers = document.querySelectorAll('.timeline-popover')

      // Check each popover
      let isInsidePopover = false
      allPopovers.forEach(popover => {
        if (popover.contains(event.target)) {
          isInsidePopover = true
        }
      })

      if (isInsidePopover) {
        return
      }

      // Click is outside, close the popover
      this.showDetails = false
    },
  },
}
</script>

<style scoped>
.timeline-wrapper {
  display: inline-block;
}
.low-z-index-popover {
  z-index: 60 !important;
}
</style>
