<template>
  <div class="input-channels-container">
    <BCard class="shadow-sm">
      <BCardText>
        <!-- Header with back button when config is shown -->
        <div class="d-flex align-items-center mb-4">
          <BButton
            v-if="showConfig"
            variant="outline-secondary"
            size="sm"
            class="me-3"
            @click="goBack"
          >
            <feather-icon
              icon="ArrowLeftIcon"
              size="16"
              class="me-1"
            />
            Back
          </BButton>
          <h4 class="text-center flex-grow-1 mb-0">
            {{ showConfig ? `Configure ${selectedChannel.title}` : 'Input Channels' }}
          </h4>
        </div>

        <!-- Main channel selection view -->
        <div v-if="!showConfig">
          <p class="text-center text-muted mb-4">
            Select a data source to configure your input channel
          </p>

          <BRow class="justify-content-center">
            <BCol
              v-for="channel in inputChannels"
              :key="channel.id"
              cols="12"
              md="6"
              lg="3"
              class="mb-3"
            >
              <BButton
                :variant="getChannelVariant(channel)"
                size="md"
                block
                class="input-channel-btn h-100 d-flex flex-column align-items-center justify-content-center"
                @click="selectChannel(channel)"
              >
                <feather-icon
                  :icon="channel.icon"
                  size="24"
                  class="mb-1"
                />
                <span class="channel-title">{{ channel.title }}</span>
                <small class="channel-description text-muted">{{ channel.description }}</small>
              </BButton>
            </BCol>
          </BRow>
        </div>

        <!-- Configuration forms for each channel -->
        <div
          v-if="showConfig"
          class="config-container"
        >
          <!-- API Configuration -->
          <div
            v-if="selectedChannel.id === 'api'"
            class="config-form"
          >
            <ApiConfig
              @save="saveConfig"
              @cancel="goBack"
            />
          </div>

          <!-- Email Configuration -->
          <div
            v-if="selectedChannel.id === 'email'"
            class="config-form"
          >
            <EmailConfig
              @save="saveConfig"
              @cancel="goBack"
            />
          </div>

          <!-- SharePoint Configuration -->
          <div
            v-if="selectedChannel.id === 'sharepoint'"
            class="config-form"
          >
            <SharePointConfig
              @save="saveConfig"
              @cancel="goBack"
            />
          </div>

          <!-- OneDrive Configuration -->
          <div
            v-if="selectedChannel.id === 'onedrive'"
            class="config-form"
          >
            <OneDriveConfig
              @save="saveConfig"
              @cancel="goBack"
            />
          </div>
        </div>
      </BCardText>
    </BCard>
  </div>
</template>

<script>
import {
  BButton,
  BCard,
  BCardText,
  BCol,
  BRow,
} from 'bootstrap-vue'
import ApiConfig from './ApiConfig.vue'
import EmailConfig from './EmailConfig.vue'
import SharePointConfig from './SharePointConfig.vue'
import OneDriveConfig from './OneDriveConfig.vue'

export default {
  name: 'InputChannels',
  components: {
    BButton,
    BCard,
    BCardText,
    BCol,
    BRow,
    ApiConfig,
    EmailConfig,
    SharePointConfig,
    OneDriveConfig,
  },
  data() {
    return {
      selectedChannel: null,
      showConfig: false,
      configuredChannels: [], // Track which channels have been configured
      inputChannels: [
        {
          id: 'api',
          title: 'API',
          description: 'REST API integration',
          icon: 'ServerIcon',
          variant: 'outline-primary',
        },
        {
          id: 'email',
          title: 'Email',
          description: 'Email data source',
          icon: 'MailIcon',
          variant: 'outline-success',
        },
        {
          id: 'sharepoint',
          title: 'SharePoint',
          description: 'SharePoint documents',
          icon: 'FolderIcon',
          variant: 'outline-warning',
        },
        {
          id: 'onedrive',
          title: 'OneDrive',
          description: 'OneDrive files',
          icon: 'CloudIcon',
          variant: 'outline-info',
        },
      ],
    }
  },
  methods: {
    selectChannel(channel) {
      this.selectedChannel = channel
      this.showConfig = true
      this.$emit('channel-selected', channel)
    },
    goBack() {
      this.showConfig = false
      this.selectedChannel = null
    },
    saveConfig(configData) {
      // Handle saving configuration
      const channelId = this.selectedChannel.id

      // Add to configured channels if not already there
      if (!this.configuredChannels.includes(channelId)) {
        this.configuredChannels.push(channelId)
      }

      // Emit the configuration data
      this.$emit('config-saved', {
        channel: this.selectedChannel,
        config: configData,
      })

      // Optional: Go back to main view after saving
      this.goBack()
    },
    getChannelVariant(channel) {
      // Show solid variant if channel is configured
      if (this.configuredChannels.includes(channel.id)) {
        return channel.variant.replace('outline-', 'outline-')
      }
      return channel.variant
    },
  },
}
</script>

<style scoped>
.input-channels-container {
  max-width: 100%;
}

.input-channel-btn {
  min-height: 120px;
  border: 2px solid;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.input-channel-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.input-channel-btn:active {
  transform: translateY(0);
}

.channel-title {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 4px;
}

.channel-description {
  font-size: 0.85rem;
  opacity: 0.8;
}

.config-container {
  animation: slideIn 0.3s ease-in-out;
  min-height: 400px;
}

.config-form {
  width: 100%;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Configured channel styling */
.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
}

.btn-success {
  background-color: #28a745;
  border-color: #28a745;
}

.btn-warning {
  background-color: #ffc107;
  border-color: #ffc107;
  color: #212529;
}

.btn-info {
  background-color: #17a2b8;
  border-color: #17a2b8;
}
</style>
