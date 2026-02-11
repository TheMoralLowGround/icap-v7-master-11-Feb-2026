<template>
  <div class="input-channels-container">
    <BCard class="shadow-sm">
      <BCardText>
        <!-- Header with back button when config is shown -->
        <div class="d-flex align-items-center mb-2">
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
            {{ showConfig && selectedChannel ? `Configure ${selectedChannel.title}` : 'Output Channels' }}
          </h4>
        </div>

        <!-- Main channel selection view -->
        <div v-if="!showConfig">
          <p class="text-center text-muted mb-1">
            Select a data source to configure your output channel
          </p>
          <div class="d-flex justify-content-end mb-2">
            <BButton
              variant="primary"
              class="float-end"
              @click="openAddChannelModal"
            >
              <feather-icon
                icon="PlusIcon"
                size="16"
                class="me-1"
              />
              Add New Channel
            </BButton>
          </div>
          <draggable
            v-model="outputChannel"
            tag="div"
            class="row justify-content-center"
            handle=".drag-handle"
          >
            <BCol
              v-for="channel in outputChannel"
              :key="channel.output_id"
              cols="12"
              md="6"
              lg="3"
              class="mb-3"
            >
              <div class="position-relative">
                <BButton
                  :variant="getChannelVariant(channel)"
                  size="md"
                  block
                  class="input-channel-btn h-100 d-flex flex-column align-items-center justify-content-center"
                  @click="selectChannel(channel)"
                >
                  <div class="d-flex w-100 justify-content-center align-items-start">

                    <feather-icon
                      :icon="channel.icon"
                      size="28"
                    />
                  </div>
                  <span class="channel-title">{{ channel.title }}</span>
                  <small class="channel-description text-muted">{{ channel.description }}</small>
                </BButton>
                <div class="action-buttons d-flex justify-content-between">
                  <span>
                    <feather-icon
                      icon="GridIcon"
                      size="24"
                      class="drag-handle me-2"
                      style="cursor: move;"
                    />
                  </span>
                  <span>
                    <BButton
                      variant="link"
                      size="sm"
                      class="p-0 text-secondary"
                      @click="editChannel(channel)"
                    >
                      <feather-icon
                        icon="EditIcon"
                        size="18"
                      />
                    </BButton>
                    <BButton
                      variant="link"
                      size="sm"
                      class="p-0 text-danger ms-2"
                      @click="confirmDelete(channel)"
                    >
                      <feather-icon
                        icon="TrashIcon"
                        size="18"
                      />
                    </BButton>

                  </span>

                </div>
              </div>
            </BCol>
          </draggable>
        </div>

        <!-- Configuration forms for each channel -->
        <div
          v-if="showConfig && selectedChannel"
          class="config-container"
        >
          <div class="config-form">
            <OutputApiConfig
              :output-type="selectedChannel.output_type"
              :channel-id="selectedChannel.output_id"
              @save="saveConfig"
              @cancel="goBack"
            />
          </div>
        </div>
      </BCardText>
    </BCard>
    <!-- <pre>{{ outputChannelTypes }}</pre> -->

    <!-- Add/Edit Output Channel Modal -->
    <AddOutputChannel
      :model-value="showChannelModal"
      :mode="modalMode"
      :channel-data="selectedChannelForEdit"
      @channel-added="handleChannelAdded"
      @channel-updated="handleChannelUpdated"
      @update:modelValue="showChannelModal = $event"
    />

    <!-- Delete Confirmation Modal -->
    <b-modal
      v-model="showDeleteModal"
      centered
      title="Confirm Delete"
      ok-title="Delete"
      ok-variant="danger"
      cancel-title="Cancel"
      @ok="deleteChannel"
    >
      <p v-if="channelToDelete">
        Are you sure you want to delete <strong>{{ channelToDelete.title }}</strong>?
      </p>
      <p class="text-muted mb-0">
        This action cannot be undone.
      </p>
    </b-modal>
  </div>
</template>

<script>
import {
  BButton,
  BCard,
  BCardText,
  BCol,
  BModal,
} from 'bootstrap-vue'
import { mapGetters, mapActions } from 'vuex'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import draggable from 'vuedraggable'
import OutputApiConfig from './OutputApiConfig.vue'
import AddOutputChannel from './AddOutputChannel.vue'

export default {
  name: 'OutputChannels',
  components: {
    BButton,
    BCard,
    BCardText,
    BCol,
    BModal,
    OutputApiConfig,
    AddOutputChannel,
    draggable,
  },
  data() {
    return {
      selectedChannel: null,
      showConfig: false,
      showChannelModal: false,
      modalMode: 'add', // 'add' or 'edit'
      selectedChannelForEdit: null,
      showDeleteModal: false,
      channelToDelete: null,
      configuredChannels: [], // Track which channels have been configured
    }
  },
  computed: {
    ...mapGetters('project', ['outputChannelTypes']),
    outputChannel: {
      get() {
        return this.outputChannelTypes || []
      },
      set(newVal) {
        // Update orders based on new positions
        const updatedWithOrders = this.updateChannelOrders(newVal)
        this.$store.commit('project/SET_OUTPUT_CHANNEL_TYPES', updatedWithOrders)
        // Save the updated order to backend
        this.saveProject()
      },
    },
    projectId() {
      return this.$store.getters['project/project'].id
    },
  },
  methods: {
    ...mapActions('project', ['saveProject']),
    showToast(title, text = '', icon = 'InfoIcon', variant = 'info') {
      this.$toast({
        component: ToastificationContent,
        props: {
          title, text, icon, variant,
        },
      })
    },
    // Update order field for all channels based on their index (order starts at 1)
    updateChannelOrders(channels) {
      return channels.map((channel, index) => ({
        ...channel,
        order: index + 1,
      }))
    },
    generateChannelId(outputType) {
      const cryptoObj = window.crypto || window.msCrypto
      // Prefer native UUID when available
      if (cryptoObj && typeof cryptoObj.randomUUID === 'function') {
        return `${outputType}-${cryptoObj.randomUUID()}`
      }
      const bytes = new Uint8Array(16)
      if (cryptoObj && typeof cryptoObj.getRandomValues === 'function') {
        cryptoObj.getRandomValues(bytes)
        // Set version (4) and variant (10) nibbles without bitwise
        bytes[6] = 0x40 + (bytes[6] % 16)
        bytes[8] = 0x80 + (bytes[8] % 64)
        const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('')
        const uuid = `${hex.substr(0, 8)}-${hex.substr(8, 4)}-${hex.substr(12, 4)}-${hex.substr(16, 4)}-${hex.substr(20)}`
        return `${outputType}-${uuid}`
      }
      // Fallback for older environments without crypto
      const fallback = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.floor(Math.random() * 16)
        const v = c === 'x' ? r : (8 + (r % 4))
        return v.toString(16)
      })
      return `${outputType}-${fallback}`
    },
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
      if (!this.selectedChannel) return
      const channelId = this.selectedChannel.output_id
      if (!this.configuredChannels.includes(channelId)) {
        this.configuredChannels.push(channelId)
      }
      this.$emit('config-saved', {
        channel: this.selectedChannel,
        config: configData,
      })
    },
    getChannelVariant(channel) {
      return channel.variant
    },
    openAddChannelModal() {
      this.modalMode = 'add'
      this.selectedChannelForEdit = null
      this.showChannelModal = true
    },
    async handleChannelAdded(newChannel) {
      try {
        const channelId = this.generateChannelId(newChannel.output_type)
        // Calculate order based on current number of channels + 1
        const newOrder = this.outputChannelTypes.length + 1
        const channelWithId = {
          ...newChannel,
          output_id: channelId,
          order: newOrder,
        }

        // Get current channels and add new one
        const updatedChannels = [...this.outputChannelTypes, channelWithId]

        // Update store
        this.$store.commit('project/SET_OUTPUT_CHANNEL_TYPES', updatedChannels)

        // Save to backend

        this.showChannelModal = false
        this.saveProject()
        const payload = {
          project: this.projectId,
          is_active: false,
          endpoint_url: '',
          auth_type: 'none',
          request_type: 'POST',
          output_type: channelWithId.output_type,
          output_id: channelWithId.output_id,
        }
        await this.$store.dispatch('project/saveOutputApiConfig', { payload })
        this.showToast('Channel Added Successfully', `${newChannel.title} has been added to output channels`, 'CheckIcon', 'success')
      } catch (error) {
        this.showToast('Error', 'Failed to add channel', 'AlertCircleIcon', 'danger')
      }
    },
    editChannel(channel) {
      this.modalMode = 'edit'
      this.selectedChannelForEdit = channel
      this.showChannelModal = true
    },
    async handleChannelUpdated(updatedChannel) {
      try {
        // Find and update the channel in the array
        const updatedChannels = this.outputChannelTypes.map(ch => (ch.output_id === updatedChannel.output_id ? updatedChannel : ch))

        // Update store
        this.$store.commit('project/SET_OUTPUT_CHANNEL_TYPES', updatedChannels)

        this.showChannelModal = false
        this.saveProject()
        this.showToast('Channel Updated Successfully', `${updatedChannel.title} has been updated`, 'CheckIcon', 'success')
      } catch (error) {
        this.showToast('Error', 'Failed to update channel', 'AlertCircleIcon', 'danger')
      }
    },
    confirmDelete(channel) {
      this.channelToDelete = channel
      this.showDeleteModal = true
    },
    async deleteChannel() {
      if (!this.channelToDelete) return
      try {
        const deletedChannel = this.channelToDelete

        // Remove from array
        let updatedChannels = this.outputChannelTypes.filter(ch => ch.output_id !== deletedChannel.output_id)

        // Recalculate orders after deletion
        updatedChannels = this.updateChannelOrders(updatedChannels)

        // Update store
        this.$store.commit('project/SET_OUTPUT_CHANNEL_TYPES', updatedChannels)

        // Remove from configured channels if present
        const configIndex = this.configuredChannels.indexOf(deletedChannel.output_id)
        if (configIndex !== -1) {
          this.configuredChannels.splice(configIndex, 1)
        }
        this.saveProject()
        await this.$store.dispatch('project/DeleteOutputApiConfig', deletedChannel.output_id)
        this.showToast('Channel Deleted', `${deletedChannel.title} has been removed from output channels`, 'TrashIcon', 'success')
      } catch (error) {
        this.showToast('Error', 'Failed to delete channel', 'AlertCircleIcon', 'danger')
      } finally {
        this.channelToDelete = null
        this.showDeleteModal = false
      }
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
  overflow: visible;
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
  margin-bottom: 8px;
  margin-top: 0.5rem;
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

.action-buttons {
  position: absolute;
  width: 100%;
  top: 8px;
  right: 0px;
  padding: 0 5px 0 5px;
}

.drag-handle {
  cursor: move;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.drag-handle:hover {
  opacity: 1;
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
</style>
