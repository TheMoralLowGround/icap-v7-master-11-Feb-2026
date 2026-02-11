<template>
  <div>
    <div class="d-flex justify-content-between align-items-center my-2">
      <h4 class="text-primary p-0 m-0">
        Timeline - {{ batchId }}
      </h4>

      <div class="d-flex align-items-center ml-auto">
        <h4
          v-if="getTotalProcessTime()"
          class="text-secondary p-0 m-0 mr-2"
        >
          RPT - {{ getTotalProcessTime() }}
        </h4>
        <div class="mb-50">
          <feather-icon
            icon="XIcon"
            size="20"
            class="cursor-pointer"
            @click="$emit('close')"
          />
        </div>
      </div>
    </div>

    <div
      v-if="loading"
      class="text-center my-1"
    >
      <b-spinner
        variant="primary"
        label="Small Spinner"
      />
    </div>

    <b-alert
      :variant="bAlertColor"
      :show="!loading && loadingError ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <template v-if="!loading && !loadingError">
      <div v-if="logs.length === 0">
        <p> No records to display </p>
      </div>

      <div
        v-if="logs.length > 0"
        class="timeline-content-div"
      >
        <app-timeline>
          <timeline-detail-item
            v-for="(item, index) in logsWithTimeDifference"
            :key="item.id"
            :batch-id="batchId"
            :item="item"
            :time-difference="item.timeDifference"
            :current-index="index"
          />
        </app-timeline>
      </div>
    </template>
  </div>
</template>

<script>
import AppTimeline from '@core/components/app-timeline/AppTimeline.vue'
import { BSpinner, BAlert } from 'bootstrap-vue'
import TimelineDetailItem from '@/components/UI/Timeline/TimelineDetailItem.vue'

export default {
  components: {
    AppTimeline,
    BSpinner,
    TimelineDetailItem,
    BAlert,
  },
  props: {
    batchId: {
      type: String,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    loadingError: {
      type: String,
      required: false,
      default: null,
    },
    logs: {
      type: Array,
      required: true,
    },
  },
  computed: {
    bAlertColor() {
      return this.logs?.length <= 1 ? 'warning' : 'danger'
    },
    logsWithTimeDifference() {
      return this.logs.map((currentItem, index) => {
        // For the first item, there is no previous item to compare
        if (index === this.logs.length - 1) {
          return {
            ...currentItem,
            timeDifference: null, // No time difference for the last item
          }
        }

        const nextItem = this.logs[index + 1]
        const timeDifferenceInMs = this.getTimeDifference(nextItem, currentItem)

        const formattedTimeDifference = this.formatTimeDifference(timeDifferenceInMs)

        // Return the current log item with the calculated time difference
        return {
          ...currentItem,
          timeDifference: formattedTimeDifference,
        }
      })
    },
  },
  methods: {
    parseDateTime(dateTimeString) {
      return new Date(dateTimeString).getTime() // Assuming your datetime strings are ISO formatted
    },
    getTimeDifference(currentItem, previousItem) {
      const currentTime = this.parseDateTime(currentItem.event_time)
      const previousTime = this.parseDateTime(previousItem.event_time)
      return previousTime - currentTime // Time difference in milliseconds
    },
    formatTimeDifference(ms) {
      const hours = Math.floor(ms / 3600000)
      const minutes = Math.floor((ms % 3600000) / 60000)
      const seconds = Math.floor((ms % 60000) / 1000)
      const milliseconds = ms % 1000

      let formattedTime = ''

      // Dynamically construct the format based on values
      if (hours > 0) {
        formattedTime += `${hours}h `
      }
      if (minutes > 0 || hours > 0) {
        formattedTime += `${minutes}m `
      }
      if (seconds > 0 || minutes > 0 || hours > 0) {
        formattedTime += `${seconds}s `
      }
      formattedTime += `${milliseconds}ms`

      return formattedTime.trim()
    },
    getTotalProcessTime() {
      if (!this.logs || this.logs.length === 0) return null

      // Find the most recent item with the message
      const reuploadItems = this.logs.filter(item => item.message === 'Re-uploading Existing Transaction' || item.message === 'Re-uploading Existing Training Batch' || item.message === 'Request Received for Processing Batch')

      let startTime

      if (reuploadItems.length > 0) {
        const mostRecentFilteredItem = reuploadItems[0]
        startTime = this.parseDateTime(mostRecentFilteredItem.event_time)
      } else {
        startTime = this.parseDateTime(this.logs[this.logs.length - 1].event_time)
      }

      const endTime = this.parseDateTime(this.logs[0].event_time)

      // Calculate the total time difference in milliseconds
      const totalTime = endTime - startTime

      const formattedTimeDifference = this.formatTimeDifference(totalTime)

      return formattedTimeDifference
    },
  },
}
</script>

<style scoped>
.timeline-content-div {
    padding: 5px;
    max-height: 50vh;
    overflow-y: scroll;
}
</style>
