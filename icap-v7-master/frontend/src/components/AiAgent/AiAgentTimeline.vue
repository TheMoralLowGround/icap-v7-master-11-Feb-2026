<template>
  <div class="timeline-container">
    <app-timeline
      ref="timelineListRef"
      class="mx-2"
    >
      <app-timeline-item
        v-for="(item, index) in aiAgentMessages"
        :key="index"
        :variant="apptimeColorVarient(item.message)"
      >
        <div class="d-flex flex-sm-row flex-column flex-wrap justify-content-between mb-sm-0">
          <h6
            :class="[
              { 'cursor-pointer': hoveredItemIndex === index && hasValidPosition(item) },
              { [`text-${apptimeColorVarient(item.message)}`]: hoveredItemIndex === index && hasValidPosition(item) }
            ]"
            @mouseenter="hoveredItemIndex = index"
            @mouseleave="hoveredItemIndex = null"
            @click="navigateToPosition(item.message.position_data)"
          >
            {{ item.message.agent_name }}
          </h6>
          <small class="text-muted">{{ formattedDate(item.event_time) }}</small>
        </div>

        <section
          v-if="item.message.message"
          show
          class="p-1 rounded message-bg"
          :class="{ 'cursor-pointer': hoveredItemIndex === index && hasValidPosition(item) }"
          @mouseenter="hoveredItemIndex = index"
          @mouseleave="hoveredItemIndex = null"
          @click="navigateToPosition(item.message.position_data)"
        >
          <span
            style="white-space: pre-wrap"
            :class="`text-${apptimeColorVarient(item.message)}`"
          >
            {{ item.message.message }}
          </span>
        </section>
      </app-timeline-item>
    </app-timeline>
  </div>
</template>

<script>
import AppTimeline from '@core/components/app-timeline/AppTimeline.vue'
import AppTimelineItem from '@core/components/app-timeline/AppTimelineItem.vue'

export default {
  components: {
    AppTimeline,
    AppTimelineItem,
  },
  props: {
    aiAgentMessages: {
      type: Array,
      required: true,
      default: () => [],
    },
  },
  data() {
    return {
      hoveredItemIndex: null,
    }
  },
  watch: {
    aiAgentMessages: {
      handler() {
        this.$nextTick(() => {
          this.$nextTick(this.scrollToBottom)
        })
      },
      deep: true,
    },
  },
  mounted() {
    this.$nextTick(this.scrollToBottom)
  },
  methods: {
    scrollToBottom() {
      const container = this.$refs.timelineListRef?.$el
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    hasValidPosition(item) {
      return item.message.position_data && Object.keys(item.message.position_data).length > 0
    },
    apptimeColorVarient(message) {
      switch (message?.color_code) {
        case 'green':
          return 'success'
        case 'yellow':
          return 'warning'
        case 'red':
          return 'danger'
        default:
          return 'primary'
      }
    },
    formattedDate(dateString) {
      const date = new Date(dateString)
      return `${date.toLocaleDateString('en-GB')} ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`
    },
    navigateToPosition(positionData) {
      if (!positionData || Object.keys(positionData).length === 0) return

      const [left, top, right, bottom] = (positionData.position || '0,0,0,0').split(',')
      const pageId = positionData.page_id
      const documentId = positionData.document_id
      const batchId = positionData.batch_id

      this.$store.dispatch('batch/scrollToPos', [left, top, right, bottom, pageId, documentId, batchId])
      this.$emit('close-drawer')
    },
  },
}
</script>
<style scoped>
.timeline-container {
  padding: 5px;
  max-height: 85vh;
  overflow-y: auto;
}

.text-muted {
  color: #b9b9c3 !important
}

.message-bg {
  background-color: #0c0c0c;
  font-weight: 600;
  font-size: 1rem;
}

/* Scrollbar Customization Starts */
.timeline-container {
  /* Firefox */
  scrollbar-color: #b9b9c3 #0c0c0c; /* thumb-color track-color */
}

.timeline-container::-webkit-scrollbar {
  width: 8px; /* Scrollbar width */
}

.timeline-container::-webkit-scrollbar-track {
  background: #0c0c0c;
  border-radius: 4px;
}

.timeline-container::-webkit-scrollbar-thumb {
  background: #b9b9c3;
  border-radius: 4px;
}

.timeline-container::-webkit-scrollbar-thumb:hover {
  background: #b9b9c3;
}
/* Scrollbar Customization Ends */

@media only screen and (min-width: 1600px) {
  .timeline-container {
    max-height: 87vh;
  }
}
</style>
