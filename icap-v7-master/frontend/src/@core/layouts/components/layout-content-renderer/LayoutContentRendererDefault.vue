<template>
  <div
    class="app-content content "
    :class="[{'show-overlay': $store.state.app.shallShowOverlay}, $route.meta.contentClass, {'custom-top': togoleNavbar}]"
  >
    <div class="content-overlay" />
    <div class="header-navbar-shadow" />
    <div
      class="content-wrapper"
      :class="contentWidth === 'boxed' ? 'container p-0' : null"
    >
      <slot name="breadcrumb">
        <app-breadcrumb />
      </slot>
      <div class="content-body">
        <transition
          :name="routerTransition"
          mode="out-in"
        >
          <slot />
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import AppBreadcrumb from '@core/layouts/components/AppBreadcrumb.vue'
import useAppConfig from '@core/app-config/useAppConfig'
import bus from '@/bus'

export default {
  components: {
    AppBreadcrumb,
  },
  setup() {
    const { routerTransition, contentWidth } = useAppConfig()

    return {
      routerTransition, contentWidth,
    }
  },
  data() {
    return {
      togoleNavbar: false,
    }
  },
  created() {
    bus.$on('toggle-navbar', this.gettogoleNavbar)
  },
  destroyed() {
    bus.$off('toggle-navbar', this.gettogoleNavbar)
  },
  methods: {
    gettogoleNavbar() {
      this.togoleNavbar = !this.togoleNavbar
    },
  },
}
</script>

<style scoped>
html[dir] [data-col="1-column"].horizontal-layout .custom-top {
  padding-top: 4px !important;
}

</style>
