<template>
  <div>
    <div
      class="cursor-pointer icon-position rounded-left-lg d-flex align-items-center"
      @click="drawer = !drawer"
    >
      <ai-agent-icon :rendered-key-nodes="renderedKeyNodes" />
    </div>

    <b-sidebar
      id="sidebar-variant"
      v-model="drawer"
      right
      shadow
      width="600px"
      backdrop-variant="transparent"
      no-header-close
      class="custom-sidebar dark-sidebar"
      bg-variant="dark"
      text-variant="light"
    >
      <template #header>
        <div class="d-flex justify-content-between align-items-center w-100">
          <h5 class="mb-0 text-light">
            AIDB Agent {{ batchId ? `- ${batchId}` : '' }}
          </h5>
          <b-button
            variant="link"
            class="text-light"
            @click="drawer = false"
          >
            <feather-icon
              icon="XIcon"
              size="20"
            />
          </b-button>
        </div>
      </template>
      <hr class="m-0 border-secondary">

      <b-tabs
        v-model="currentTab"
        justified
        class="custom-tabs dark-tabs"
      >
        <b-tab title="Timeline" />
        <b-tab title="Reasoning" />
      </b-tabs>

      <div v-if="currentTab === 0">
        <ai-agent-timeline
          v-if="aiAgentConversations.length"
          :ai-agent-messages="aiAgentConversations.filter(e => e.type === 'timeline')"
          @close-drawer="drawer = false"
        />
      </div>
      <div v-if="currentTab === 1">
        <ai-agent-reasoning
          v-if="aiAgentConversations.length"
          :ai-agent-messages="aiAgentConversations.filter(e => e.type === 'reasoning')"
        />
      </div>
    </b-sidebar>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'
import {
  BSidebar,
  BButton,
  BTabs,
  BTab,
} from 'bootstrap-vue'
import WS from '@/utils/ws'
import bus from '@/bus'
import useAppConfig from '@core/app-config/useAppConfig'
import { computed } from '@vue/composition-api'
import AiAgentIcon from './AiAgentIcon.vue'
import AiAgentTimeline from './AiAgentTimeline.vue'
import AiAgentReasoning from './AiAgentReasoning.vue'

export default {
  setup() {
    const { skin } = useAppConfig()

    const isDark = computed(() => skin.value === 'dark')

    return { skin, isDark }
  },
  components: {
    BTabs,
    BTab,
    BSidebar,
    BButton,
    AiAgentIcon,
    AiAgentTimeline,
    AiAgentReasoning,
  },
  data() {
    return {
      loading: false,
      drawer: false,
      currentTab: 0,
      userInput: '',
      aiAgentConversations: [],
    }
  },
  computed: {
    ...mapState('batch', ['batch', 'keyNodes']),
    renderedKeyNodes() {
      let counts = 0
      for (let i = 0; i < this.keyNodes?.length; i += 1) {
        const keyNode = this.keyNodes[i]

        if (!keyNode.isProfileKeyFound) {
          counts += 1
        }
      }

      return counts
    },
    transactionId() {
      return this.$store.getters['batch/selectedTransactionId']
    },
    batchId() {
      const batch = this.$store.getters['batch/batch']
      return batch?.id
    },
  },
  watch: {
    batchId: {
      handler(newVal, oldVal) {
        if (oldVal) {
          this.aiAgentConversations = []
          WS.leaveRoom(`ai_agent_response_${oldVal}`)
        }

        if (newVal) {
          this.fetchAiAgentConversations()
          WS.joinRoom(`ai_agent_response_${this.batchId}`)
        }
      },
      deep: true,
      immediate: true,
    },
    drawer(newVal) {
      if (newVal) {
        document.body.classList.add('sidebar-open')
      } else {
        document.body.classList.remove('sidebar-open')
      }
    },
  },
  mounted() {
    bus.$on('wsData/aiAgentResponse', this.onAiAgentResponse)
    bus.$on('wsData/batchStatus', this.onBatchStatus)
  },
  beforeDestroy() {
    document.body.classList.remove('sidebar-open')

    if (this.batchId) {
      WS.leaveRoom(`ai_agent_response_${this.batchId}`)
    }

    bus.$off('wsData/aiAgentResponse', this.onAiAgentResponse)
    bus.$off('wsData/batchStatus', this.onBatchStatus)
  },
  methods: {
    async fetchAiAgentConversations() {
      this.loading = true
      try {
        const res = await axios.get(`/get_ai_agent_conversations/${this.transactionId}`)
        if (res.data.length) {
          this.aiAgentConversations = res.data
        }
      } catch (error) {
        // Handle error
      }
      this.loading = false
    },

    onAiAgentResponse(data) {
      if (data.transaction_id !== this.transactionId) return

      this.aiAgentConversations.push(data)
    },
    onBatchStatus(data) {
      if (this.batchId === data.batch_id && data.status !== 'completed') {
        this.aiAgentConversations = []
      }
    },
  },
}
</script>

<style scoped>
.bg-dark {
  background-color: #0c0c0c !important;
}
.icon-position {
  position: fixed;
  top: 50%;
  right: 0;
  z-index: 500;
  cursor: pointer;
}

.custom-sidebar {
  z-index: 1051;
}
/* Force dark mode for all text elements inside sidebar */
.dark-sidebar >>> * {
  color: #ffffff;
}

/* Override Bootstrap's default text colors */
.dark-sidebar >>> .text-dark {
  color: #ffffff !important;
}

/* Ensure proper contrast for interactive elements */
.dark-sidebar >>> .btn-link {
  color: #ffffff !important;
}

.dark-sidebar >>> .btn-link:hover {
  color: #e0e0e0 !important;
}

.fixed-input-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.single-line-textarea {
  resize: none;
  max-height: 38px;
  overflow-y: hidden !important;
}

textarea.form-control {
  padding: 0.5rem 1rem !important;
}

textarea {
  border: 1px solid #8a8989 !important;
}

textarea:focus {
  border: 1px solid #7367f0 !important;
}

.reset-button {
  z-index: 1100;
}

.dark-input {
  background-color: #4b4b4b !important;
  color: #ffffff !important;
  border-color: #6c757d !important;
}
/* Ensure hr elements are visible in dark mode */
.dark-sidebar >>> hr {
  border-color: #6c757d !important;
}

/* Handle feather icons in dark mode */
.dark-sidebar >>> .feather {
  color: #ffffff !important;
}

/* Option 2: Even darker than current */
.dark-sidebar {
  background-color: #0d0d0d !important; /* Much darker */
}
/* If you want to also darken the tabs area to match */
.dark-tabs >>> .nav-tabs {
  border-bottom: 1px solid #6c757d !important;
  background-color: #1a1a1a !important; /* Match sidebar */
}

/* And adjust active tab to be slightly lighter than sidebar */
.dark-tabs >>> .nav-tabs .nav-link.active {
  color: #ffffff !important;
  background-color: #2d2d2d !important; /* Slightly lighter than sidebar */
  border-color: #6c757d !important;
  border-bottom-color: #2d2d2d !important;
}
</style>
<style>
/* .bg-dark {
  background-color: #0c0c0c;
} */
/* #4b4b4b, #010628 #080b20 */
</style>
