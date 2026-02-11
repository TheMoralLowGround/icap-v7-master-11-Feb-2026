<template>
  <layout-horizontal>

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
  </layout-horizontal>
</template>

<script>
import LayoutHorizontal from '@core/layouts/layout-horizontal/LayoutHorizontal.vue'
import Navbar from '../components/Navbar.vue'
import VerticalMenuHeader from '../components/VerticalMenuHeader.vue'
import Footer from '../components/Footer.vue'

export default {
  components: {
    LayoutHorizontal,
    Navbar,
    VerticalMenuHeader,
    Footer,
  },
}
</script>
