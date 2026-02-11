<template>
  <layout-vertical>

    <router-view />

    <template #navbar="{ toggleVerticalMenuActive }">
      <navbar :toggle-vertical-menu-active="toggleVerticalMenuActive" />
    </template>

    <template #vertical-menu-header="{toggleVerticalMenuActive}">
      <vertical-menu-header :toggle-vertical-menu-active="toggleVerticalMenuActive" />
    </template>

    <template #footer>
      <Footer />
    </template>
  </layout-vertical>
</template>

<script>
// import AppCustomizer from '@core/layouts/components/app-customizer/AppCustomizer.vue'
// import { $themeConfig } from '@themeConfig'
import Navbar from '../components/Navbar.vue'
import VerticalMenuHeader from '../components/VerticalMenuHeader.vue'
import Footer from '../components/Footer.vue'

export default {
  components: {
    // AppCustomizer,
    Navbar,
    VerticalMenuHeader,
    Footer,
  },
  data() {
    return {
      // showCustomizer: $themeConfig.layout.customizer,
    }
  },
}
</script>
