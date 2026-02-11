<!--
 Organization: AIDocbuilder Inc.
 File: training.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-08-22

 Description:
   The training.vue component provides a dedicated interface for initiating and managing
   training-related processes. This component acts as a wrapper for the `TrainBatches`
   subcomponent, focusing specifically on batch training functionalities.

 Dependencies:
   - Vue: JavaScript framework for building UI.
   - TrainBatches Component: Manages and displays batch data in training mode.

 Main Features:
   - Displays a header titled "Training" for better section visibility.
   - Integrates the `TrainBatches` component with training mode enabled via `training-mode` prop.

 Core Components:
   - `<TrainBatches>`: Handles the display and functionality of batch management for training purposes.

 Props (passed to subcomponents):
   - `training-mode`: Boolean flag enabling training-specific behavior within the `TrainBatches` component.

 Notes:
   - Previously, the `Batches` component was considered for usage, but it has been commented out in favor of `TrainBatches`.
   - This file is intentionally simple to maintain focus on its role as a parent container.
-->

<template>
  <div>
    <template v-if="showProfileTraining">
      <div class="tab-menu">
        <!-- Render tab items dynamically -->
        <div
          v-for="(tab, index) in visibleTabs"
          ref="tabItems"
          :key="tab.name"
          class="tab-item"
          :class="{ active: activeTab === tab.name }"
          @click="setView(tab.name, index)"
        >
          {{ tab.label }}
        </div>
        <!-- Highlighter Bar -->
        <div
          class="tab-highlighter"
          :style="{
            width: highlighterWidth,
            left: highlighterLeft,
          }"
        />
      </div>

      <!-- Render active tab's component -->
      <div class="component-container">
        <component
          :is="activeComponent"
          :training-mode="true"
        />
      </div>
    </template>

    <template v-else>
      <h2>Training</h2>
      <TrainBatches :training-mode="true" />
    </template>
  </div>
</template>

<script>
import TrainBatches from '@/components/Batches/TrainBatches.vue'
import ProfileTrainBatches from '@/components/Batches/ProfileTrainBatches.vue'

export default {
  components: {
    TrainBatches,
    ProfileTrainBatches,
  },
  data() {
    return {
      tabs: [
        { name: 'training', label: 'Training', component: 'TrainBatches' },
        {
          name: 'profileTraining',
          label: 'Process Training',
          component: 'ProfileTrainBatches',
        },
      ],
      activeTab: 'training',
      activeIndex: 0,
      highlighterWidth: '0px',
      highlighterLeft: '0px',
    }
  },
  computed: {
    activeComponent() {
      return this.visibleTabs.find(tab => tab.name === this.activeTab)?.component
    },
    showProfileTraining() {
      return this.$store.getters['developerSettings/showProfileTraining']
    },
    visibleTabs() {
      return this.tabs.filter(tab => tab.name !== 'profileTraining' || this.showProfileTraining)
    },
  },
  watch: {
    // Watch for route changes to update the active tab
    $route() {
      this.initializeTabFromRoute()
    },
    showProfileTraining() {
      // Reinitialize tabs if `showProfileTraining` changes
      this.initializeTabFromRoute()
    },
  },
  mounted() {
    this.updateHighlighter()
    window.addEventListener('resize', this.updateHighlighter)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.updateHighlighter)
  },
  async created() {
    try {
      const isDeveloper = this.$store.getters['developerSettings/isDeveloper']
      if (isDeveloper) {
        await this.$store.dispatch('developerSettings/fetchDeveloperSettings')
      }
    } catch (error) {
      // console.error('Error in created hook:', error)
    }
    this.initializeTabFromRoute()
  },
  methods: {
    setView(tabName, index) {
      this.activeTab = tabName
      this.activeIndex = index
      this.updateHighlighter()
      // Update the route with the active tab
      this.$router.push({ query: { tab: tabName } })
    },
    updateHighlighter() {
      // Ensure DOM updates before accessing refs
      this.$nextTick(() => {
        const tab = this.$refs.tabItems?.[this.activeIndex]
        if (tab) {
          this.highlighterWidth = `${tab.offsetWidth}px`
          this.highlighterLeft = `${tab.offsetLeft}px`
        }
      })
    },
    initializeTabFromRoute() {
      const defaultTab = 'training'
      const tabName = this.$route.query.tab || defaultTab
      const visibleTabIndex = this.visibleTabs.findIndex(tab => tab.name === tabName)

      if (visibleTabIndex !== -1) {
        this.activeTab = tabName
        this.activeIndex = visibleTabIndex
      } else {
        // Fallback to default tab if invalid or hidden
        this.activeTab = defaultTab
        this.activeIndex = 0
        this.$router.replace({ query: { tab: defaultTab } })
      }

      this.updateHighlighter()
    },
  },
}
</script>

<style scoped>
/* Tab menu styles */
.tab-menu {
  position: relative;
  display: flex;
  justify-content: flex-start;
}

.tab-item {
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 500;
  font-size: 18px;
  transition: color 0.3s ease;
}

.tab-item.active {
  color: #7367f0;
  background-color: #fff;
}

.tab-highlighter {
  position: absolute;
  bottom: 0;
  height: 3px;
  background-color: #5e50ee;
  transition: all 0.3s ease;
}

.component-container {
  padding-top: 20px;
  background: #fff;
}
</style>
