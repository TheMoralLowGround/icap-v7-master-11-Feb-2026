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
        :class="eyeColor"
        @click="onShowDetailsChange(!showDetails)"
      />
      <b-popover
        :show.sync="showDetails"
        :target="`view-timeline-${batchId}`"
        :placement="placement"
        boundary="window"
        custom-class="timeline-popover"
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
      type: [String, Number],
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
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
    eyeColor() {
      let colorClass = ''
      if (this.logs.length) {
        if (this.logs[0].status === 'failed') {
          colorClass = 'text-danger'
        } else if (this.logs[0].status === 'completed') {
          colorClass = 'text-success'
        } else if (this.logs[0].status === 'inprogress') {
          colorClass = 'text-primary'
        } else if (this.logs[0].status === 'upload') {
          colorClass = 'text-info'
        }
      } else {
        colorClass = 'text-warning'
      }
      return colorClass
    },
  },
  watch: {
    batchId(_, oldValue) {
      if (this.autoInitialize) {
        this.cleanup(oldValue)
        this.initialize()
      }
    },

    showDetails() {
      if (!this.autoInitialize) {
        if (this.showDetails) {
          this.initialize()
        } else {
          this.cleanup()
        }
      }
    },
  },
  created() {
    this.initialize()
    bus.$on('setTimelineID', this.setActiveId)
    bus.$on('onHideTimelineModal', this.onHideTimelineModal)
  },
  destroyed() {
    this.cleanup()
    bus.$off('setTimelineID', this.setActiveId)
    bus.$on('onHideTimelineModal', this.onHideTimelineModal)
  },
  methods: {
    initialize() {
      this.fetchTimelineData()
      const rommName = this.convertGroupName(this.batchId)
      WS.joinRoom(`timeline_${rommName}`)
      bus.$on('wsData/timelineStatus', this.onBatchStatus)
    },
    cleanup(batchId = null) {
      const rommName = this.convertGroupName(batchId || this.batchId)
      WS.leaveRoom(`timeline_${rommName}`)
      bus.$off('wsData/timelineStatus', this.onBatchStatus)
      // this.logs = []
    },
    convertGroupName(groupName) {
      const cleanedName = groupName.replace(/[^\w.-]/g, '-')
      return cleanedName
    },
    fetchTimelineData() {
      this.loading = true
      this.loadingError = null
      axios.get(`/dashboard/timeline/${this.batchId}`)
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
          this.loadingError = error?.res?.data?.detail || 'No timeline data found'
          this.loading = false
        })
    },
    onBatchStatus(data) {
      if (this.batchId === data.timeline_id && data.message) {
        this.logs.unshift({ ...data })
      }
    },
    onShowDetailsChange(showDetails = false) {
      this.showDetails = showDetails

      this.$emit('show-details-change', showDetails)
    },
    setActiveId(value) {
      this.showDetails = value === this.batchId
    },
    onHideTimelineModal(value) {
      if (value === true) {
        this.showDetails = false
      }
    },
  },
}
</script>

<style scoped>
.timeline-wrapper {
  display: inline-block;
}
</style>
