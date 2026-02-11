<template>
  <div class="p-1">
    <!-- Tabs -->
    <BTabs
      content-class="mt-2"
      vertical
    >
      <!-- Transaction Tab -->
      <BTab
        title="Transaction"
        active
      >
        <TransactionApiConfig />
      </BTab>

      <!-- Training Tab -->
      <BTab title="Training">
        <TrainingApiConfig />
      </BTab>
    </BTabs>
  </div>
</template>

<script>
import {
  BTab,
  BTabs,
} from 'bootstrap-vue'
import TrainingApiConfig from './TrainingApiConfig.vue'
import TransactionApiConfig from './TransactionApiConfig.vue'

export default {
  name: 'ApiInputChannel',
  components: {
    BTab,
    BTabs,
    TrainingApiConfig,
    TransactionApiConfig,
  },
  data() {
    return {
      // Static data - no store connections needed
    }
  },
  methods: {
    // No form submission or store methods needed
  },
}
</script>

<style scoped>
/* Tab styling */
.nav-tabs .nav-link {
  border: none;
  color: #6c757d;
  font-weight: 500;
}

.nav-tabs .nav-link.active {
  background-color: transparent;
  border-bottom: 2px solid #007bff;
  color: #007bff;
}
</style>
