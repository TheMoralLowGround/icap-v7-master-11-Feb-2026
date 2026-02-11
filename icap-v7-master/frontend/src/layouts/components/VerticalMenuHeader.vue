<template>
  <ul class="nav navbar-nav flex-row">

    <li class="nav-item mr-auto">
      <b-link
        class="navbar-brand"
        to="/"
      >
        <logo />
      </b-link>
    </li>

    <!-- Toggler Button -->
    <li class="nav-item nav-toggle">
      <b-link
        class="nav-link modern-nav-toggle custom-nav-toggle"
      >
        <feather-icon
          icon="XIcon"
          size="20"
          class="d-block d-xl-none"
          @click="toggleVerticalMenuActive"
        />
      </b-link>
    </li>

    <!-- Logo & Text -->
    <li class="nav-item mr-auto">
      <b-link
        class="navbar-brand"
        to="/"
      >
        <h2 class="brand-text">
          {{ appName }}
        </h2>
      </b-link>
    </li>

  </ul>
</template>

<script>

import { $themeConfig } from '@themeConfig'
import { BLink } from 'bootstrap-vue'
import Logo from './Logo.vue'

export default {
  components: {
    BLink,
    Logo,
  },
  props: {
    toggleVerticalMenuActive: {
      type: Function,
      required: true,
    },
  },
  computed: {
    appName() {
      return $themeConfig.app.appName
    },
  },
}
</script>
