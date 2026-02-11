<template>
  <span>
    <feather-icon
      :id="uniqueId"
      v-b-tooltip.hover
      icon="EyeIcon"
      size="18"
      class="cursor-pointer"
      style="margin-bottom: 3px;"
      title="View Options"
    />
    <b-popover
      :target="uniqueId"
      placement="center"
      boundary="scrollParent"
      custom-class=""
    >
      <div class="popover-content">
        <!-- Export Button and Close Icon -->
        <div class="header-container">
          <b-button
            variant="outline-primary"
            size="sm"
            class="export-button"
            @click="exportToCSV"
          >
            Export to CSV
          </b-button>
          <feather-icon
            icon="XIcon"
            size="16"
            class="cursor-pointer close-icon"
            @click="closePopover"
          />
        </div>

        <!-- Table Content -->
        <div class="table-container">
          <table class="data-table">
            <tbody>
              <tr
                v-for="(value, key) in filteredItem"
                :key="key"
                class="table-row"
              >
                <td class="label-column">{{ formatLabel(key) }}</td>
                <td class="value-column">{{ formatValue(value) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </b-popover>
  </span>
</template>

<script>
import { VBTooltip, BPopover, BButton } from 'bootstrap-vue'
import _ from 'lodash'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BPopover,
    BButton,
  },
  props: {
    id: {
      type: String,
      default: '123444',
    },
    item: {
      type: Object,
      default: () => ({}),
    },
    excludeFields: {
      type: Array,
      default: () => [
        // Success notification fields
        'success_notification_with_same_subject',
        'success_notification_subject',
        // 'success_notify_email_sender',
        'success_notify_email_recipients',
        'success_notify_cc_users',
        // 'success_notify_additional_emails',
        // Failure notification fields
        'failure_notification_with_same_subject',
        'failure_notification_subject',
        // 'failure_notify_email_sender',
        'failure_notify_email_recipients',
        'failure_notify_cc_users',
        // 'failure_notify_additional_emails',
        // Display notification fields (flattened versions)
        'display_success_notification_with_same_subject',
        'display_success_notification_subject',
        'display_success_notify_email_sender',
        'display_success_notify_email_recipients',
        'display_success_notify_cc_users',
        'display_success_notify_additional_emails',
        'display_failure_notification_with_same_subject',
        'display_failure_notification_subject',
        'display_failure_notify_email_sender',
        'display_failure_notify_email_recipients',
        'display_failure_notify_cc_users',
        'display_failure_notify_additional_emails',
        'created_at',
        'updated_at',
        'id',
      ],
    },
  },
  computed: {
    // Generate a unique ID to avoid conflicts when multiple components use same address_id
    uniqueId() {
      return `${this.id}_${_.uniqueId()}`
    },
    flattenedItem() {
      // Flatten the nested display_options object
      const flattened = { ...this.item }
      if (flattened.display_options) {
        Object.entries(flattened.display_options).forEach(([key, value]) => {
          flattened[`display_${key}`] = value
        })
        delete flattened.display_options
      }
      return flattened
    },
    filteredItem() {
      // Filter out unwanted fields - more conservative approach
      const filtered = {}
      Object.entries(this.flattenedItem).forEach(([key, value]) => {
        // Only exclude if it's an exact match to our exclude list
        const shouldExclude = this.excludeFields.includes(key.toLowerCase())
                              || this.excludeFields.includes(key)

        if (!shouldExclude) {
          filtered[key] = value
        }
      })
      return filtered
    },
  },
  methods: {
    closePopover() {
      this.$root.$emit('bv::hide::popover', this.uniqueId)
    },
    formatLabel(key) {
      // Convert snake_case to Title Case
      return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },
    formatValue(value) {
      // Handle null/undefined values and objects
      if (value === null || value === undefined) {
        return 'N/A'
      }
      return value.toString()
    },
    exportToCSV() {
      // Convert filteredItem to CSV (using filtered data for export too)
      const headers = Object.keys(this.filteredItem)
      const values = Object.values(this.filteredItem).map(value => (this.formatValue(value).includes(',') ? `"${value}"` : value))

      const csvContent = [
        headers.join(','),
        values.join(','),
      ].join('\n')

      // Create and trigger download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `address_${this.id}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    },
  },
}
</script>

<style scoped>
.low-z-index-popover {
  z-index: 50 !important;
}

.popover-content {
  position: relative;
  padding: 8px;
  min-width: 300px;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.export-button {
  font-size: 12px;
  padding: 4px 8px;
}

.close-icon {
  transition: color 0.2s ease;
}

.table-container {
  margin-top: 8px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table-row {
  border-bottom: 1px solid #e9ecef;
}

.table-row:last-child {
  border-bottom: none;
}

.label-column {
  padding: 8px 12px 8px 0;
  font-weight: 600;
  vertical-align: top;
  width: 40%;
  word-wrap: break-word;
}

.value-column {
  padding: 8px 0;
  /* color: #212529; */
  vertical-align: top;
  word-wrap: break-word;
  max-width: 200px;
}
/* Responsive adjustments */
@media (max-width: 576px) {
  .popover-content {
    min-width: 250px;
  }

  .data-table {
    font-size: 12px;
  }

  .label-column,
  .value-column {
    padding: 6px 8px 6px 0;
  }

  .export-button {
    font-size: 10px;
    padding: 3px 6px;
  }
}
</style>
