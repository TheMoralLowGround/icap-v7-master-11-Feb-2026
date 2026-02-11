<template>
  <div class="agent-selector-container">
    <BCard class="shadow-sm main-card">
      <BCardText>
        <!-- Header with Selection Counter -->
        <div class="header-section">
          <h3>
            Select AI Agents for {{ selecedProcessName }}
          </h3>
          <div
            v-if="selectedCount > 0"
            class="selection-badge"
          >
            <feather-icon
              icon="CheckCircleIcon"
              size="20"
            />
            <span>{{ selectedCount }} Selected</span>
          </div>
        </div>

        <!-- Agents Grid -->
        <BRow class="justify-content-center agents-grid">
          <BCol
            v-for="agent in agents"
            :key="agent.id"
            class="mb-3 agent-col"
          >
            <div
              :class="[
                'agent-card',
                agent.selected ? 'selected' : '',
                agent.disabled ? 'disabled' : ''
              ]"
              :tabindex="agent.disabled ? -1 : 0"
              @click="!agent.disabled && toggleAgent(agent)"
              @keypress.enter="!agent.disabled && toggleAgent(agent)"
              @keypress.space.prevent="!agent.disabled && toggleAgent(agent)"
            >
              <!-- Selection Indicator -->
              <transition name="check-fade">
                <div
                  v-if="agent.selected"
                  class="selection-indicator"
                >
                  <feather-icon
                    icon="CheckIcon"
                    size="20"
                  />
                </div>
              </transition>

              <!-- Disabled Badge -->
              <div
                v-if="agent.disabled"
                class="disabled-badge"
              >
                <feather-icon
                  icon="LockIcon"
                  size="12"
                />
              </div>

              <!-- Card Content -->
              <div class="card-content">
                <div class="icon-wrapper">
                  <feather-icon
                    :icon="agent.icon"
                    size="28"
                  />
                </div>

                <h5 class="agent-title">
                  {{ agent.title }}
                </h5>

                <span class="agent-type-badge">
                  {{ agent.type }}
                </span>

                <p class="agent-description">
                  {{ agent.description }}
                </p>

                <!-- Status Text -->
                <div class="status-text">
                  <span v-if="agent.selected">Selected</span>
                  <span v-else-if="agent.disabled">Unavailable</span>
                  <span v-else>Click to select</span>
                </div>
              </div>

              <!-- Ripple Effect Container -->
              <span class="ripple" />
            </div>
          </BCol>
        </BRow>

        <!-- Action Buttons -->
        <div
          v-if="hasAgents"
          class="action-section"
        >
          <button
            class="btn-clear"
            :disabled="selectedCount === 0"
            @click="clearAll"
          >
            <feather-icon
              icon="XIcon"
              size="16"
            />
            Clear All
          </button>
          <button
            class="btn-select-all"
            :disabled="allAvailableSelected"
            @click="selectAll"
          >
            <feather-icon
              icon="CheckSquareIcon"
              size="16"
            />
            Select All Available
          </button>
        </div>
      </BCardText>
    </BCard>
  </div>
</template>

<script>
import {
  BCard,
  BCardText,
  BCol,
  BRow,
} from 'bootstrap-vue'
import storeHelper from '@/store/project/helper'

const defaultAgents = storeHelper.settings.aIAgents.filter(a => !a.disabled)

export default {
  name: 'ProcessAgentSelector',
  components: {
    BCard,
    BCardText,
    BCol,
    BRow,
  },
  props: {
    selectedAgentIds: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      selectedAgentIdsLocal: [],
    }
  },
  computed: {
    storeAgents() {
      const agents = this.$store.getters['definitionSettings/getAiAgents'] || []
      const enabledAgents = agents.filter(a => !a.disabled)

      return enabledAgents.length > 0 ? enabledAgents : defaultAgents
    },
    agents() {
      return this.storeAgents.map(agent => ({
        ...agent,
        selected: this.selectedAgentIdsLocal.includes(agent.id),
      }))
    },
    selecedProcessName() {
      return this.$store.getters['profile/selecedProcessName']
    },
    selectedCount() {
      return this.selectedAgentIdsLocal.length
    },
    allAvailableSelected() {
      const availableAgents = this.agents.filter(a => !a.disabled)
      if (availableAgents.length === 0) return false
      return availableAgents.every(a => a.selected)
    },
    hasAgents() {
      return this.agents.length > 0
    },
  },
  watch: {
    // agents: {
    //   immediate: true,
    //   handler(val) {
    //     this.localAgents = val.map(a => ({
    //       ...a,
    //       selected: false,
    //     }))
    //   },
    // },
    // selectedAgentIds: {
    //   immediate: true,
    //   handler(newIds = []) {
    //     if (!this.agents.length) return

    //     this.agents.forEach(agent => {
    //       agent.selected = newIds.includes(agent.id)
    //     })
    //   },
    // },
  },
  methods: {
    toggleAgent(agent) {
      if (agent.disabled) return

      const index = this.selectedAgentIdsLocal.indexOf(agent.id)
      if (index === -1) {
        this.selectedAgentIdsLocal.push(agent.id)
      } else {
        this.selectedAgentIdsLocal.splice(index, 1)
      }
      this.emitChange()
    },
    selectAll() {
      const availableIds = this.storeAgents
        .filter(a => !a.disabled)
        .map(a => a.id)
      this.selectedAgentIdsLocal = [...availableIds]
      this.emitChange()
    },
    clearAll() {
      this.selectedAgentIdsLocal = []
      this.emitChange()
    },
    emitChange() {
      this.$emit('agents-changed', [...this.selectedAgentIdsLocal])
    },
  },
}
</script>

<style scoped>
.agent-selector-container {
  padding: 12px;
}

.main-card {
  border: none;
  border-radius: 12px;
}

/* Header Section */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.selection-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Agents Grid */
.agents-grid {
  margin-bottom: 24px;
}

.agent-col {
  flex: 0 0 20%;
  max-width: 20%;
  padding: 0 8px;
}

/* Large tablets and small desktops - 4 cards per row */
@media (max-width: 1400px) {
  .agent-col {
    flex: 0 0 25%;
    max-width: 25%;
  }
}

/* Tablets - 3 cards per row */
@media (max-width: 992px) {
  .agent-col {
    flex: 0 0 33.333%;
    max-width: 33.333%;
  }
}

/* Small tablets - 2 cards per row */
@media (max-width: 768px) {
  .agent-col {
    flex: 0 0 50%;
    max-width: 50%;
  }
}

/* Mobile - 1 card per row */
@media (max-width: 576px) {
  .agent-col {
    flex: 0 0 100%;
    max-width: 100%;
  }
}

/* Agent Card */
.agent-card {
  position: relative;
  height: 100%;
  min-height: 200px;
  border: 2px solid #e0e7ff;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  outline: none;
}

.agent-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.agent-card:hover::before {
  transform: scaleX(1);
}

.agent-card:hover {
  border-color: #667eea;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
}

.agent-card:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.agent-card.selected {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  transform: translateY(-2px);
}

.agent-card.selected::before {
  transform: scaleX(1);
  background: rgba(255, 255, 255, 0.3);
}

.agent-card.selected:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
}

.agent-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f8f9fa;
  border-color: #dee2e6;
  border-style: dashed;
}

.agent-card.disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: #dee2e6;
}

/* Selection Indicator */
.selection-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

.check-fade-enter-active .check-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.check-fade-enter .check-fade-leave-to {
  opacity: 0;
  transform: scale(0) rotate(-180deg);
}

/* Disabled Badge */
.disabled-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  background: #6c757d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 2;
}

/* Card Content */
.card-content {
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  height: 100%;
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.agent-card:hover .icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.agent-card.selected .icon-wrapper {
  background: rgba(255, 255, 255, 0.2);
}

.agent-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.3;
  color: inherit;
}

.agent-type-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #e0e7ff;
  color: #667eea;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.agent-card.selected .agent-type-badge {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

.agent-description {
  font-size: 0.75rem;
  line-height: 1.5;
  opacity: 0.8;
  margin-bottom: 12px;
  flex-grow: 1;
}

.status-text {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
  margin-top: auto;
}

.agent-card.selected .status-text {
  opacity: 1;
}

/* Action Section */
.action-section {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
  flex-wrap: wrap;
}

.btn-clear
.btn-select-all {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 2px solid;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.btn-clear {
  border-color: #dc3545;
  color: #dc3545;
}

.btn-clear:hover:not(:disabled) {
  background: #dc3545;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.btn-select-all {
  border-color: #667eea;
  color: #667eea;
}

.btn-select-all:hover:not(:disabled) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-clear:disabled
.btn-select-all:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Ripple Effect */
.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  transform: scale(0);
  animation: ripple-animation 0.6s ease-out;
  pointer-events: none;
}

@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
</style>
