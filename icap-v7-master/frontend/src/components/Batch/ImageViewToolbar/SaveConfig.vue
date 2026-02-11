<template>
  <div>
    <!-- Tooltip wrapper for the save button -->
    <div
      v-b-tooltip.hover
      class="d-inline-block"
      title="Save Config"
    >
      <!-- Save button with conditional styling based on submitEnabled -->
      <feather-icon
        icon="SaveIcon"
        size="22"
        class="save-btn"
        :class="{
          disabled: !submitEnabled
        }"
        @click="saveConfig"
      />
    </div>
    <!-- Spinner displayed when savingConfig is true -->
    <div
      v-if="savingConfig"
      class="d-inline-block ml-25"
    >
      <b-spinner
        small
        label="Small Spinner"
      />
    </div>
  </div>
</template>

<script>
import { VBTooltip, BSpinner } from 'bootstrap-vue'
import axios from 'axios'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BSpinner, // Spinner component for loading indication
  },
  directives: {
    'b-tooltip': VBTooltip, // Tooltip directive for hover effect
  },
  data() {
    return {
      savingConfig: false, // Tracks whether the configuration is being saved
    }
  },
  computed: {
    // Determines if the save button should be enabled
    submitEnabled() {
      return this.configValueNode && !this.savingConfig
    },
    // Retrieves the first node configuration from the Vuex store
    configValueNode() {
      const configValues = this.$store.getters['batch/nodeConfig']

      const keys = Object.keys(configValues)
      if (keys.length === 0) {
        return null
      }

      const key = keys[0]
      const res = {}
      res[key] = configValues[key]
      return res
    },
    // Retrieves the batch ID from the Vuex store
    batchId() {
      return this.$store.getters['batch/batch']._id
    },
  },
  methods: {
    // Saves the configuration for the current node
    saveConfig() {
      // Prevents saving if submitEnabled is false
      if (!this.submitEnabled) {
        return
      }

      this.savingConfig = true // Indicates that saving is in progress
      const nodeId = Object.keys(this.configValueNode)[0] // Extracts the node ID
      const formData = { test: 'processed' } // Example payload to be sent

      axios.patch(`/document-node/${this.batchId}/${nodeId}`, formData)
        .then(res => {
          // Shows success toast notification
          this.$toast({
            component: ToastificationContent,
            props: {
              title: res.data.detail,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
          // Clears the node configuration in the Vuex store
          this.$store.commit('batch/CLEAR_NODE_CONFIG')
          this.savingConfig = false // Resets saving state
        })
        .catch(error => {
          // Extracts and displays error message in a toast notification
          let message = 'Somthing went wrong'
          if (
            error.response
            && error.response.data
            && error.response.data.detail
          ) {
            message = error.response.data.detail
          }

          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          this.savingConfig = false // Resets saving state
        })
    },
  },
}
</script>

<style lang="scss" scoped>
.save-btn {
  &.disabled {
    opacity: 0.5; // Reduces visibility for disabled state
    cursor: auto; // Removes pointer cursor for disabled state
  }
  cursor: pointer; // Default cursor for enabled state
}
</style>
