<template>
  <div class="flex-grow-1">
    <div
      v-if="toggleNavbar"
      class="navbar-container d-flex content align-items-center"
      :style="{
        background: backgroundColor
      }"
    >
      <div
        v-if="layoutType === 'horizontal'"
        class="navbar-header d-xl-block d-none"
      >
        <ul class="nav navbar-nav">
          <li class="nav-item">
            <b-link
              class="navbar-brand"
              to="/"
            >
              <h2
                class="brand-text mb-0 pl-0"
                :style="{
                  color: appTitleColor
                }"
              >
                {{ appTitle }}
              </h2>
            </b-link>
          </li>
        </ul>
      </div>
      <!-- Nav Menu Toggler -->
      <ul class="nav navbar-nav d-xl-none">
        <li class="nav-item">
          <b-link
            class="nav-link"
            @click="toggleVerticalMenuActive"
          >
            <feather-icon
              icon="MenuIcon"
              size="21"
            />
          </b-link>
        </li>
      </ul>
      <div class="align-items-center flex-grow-1 d-none d-lg-flex">
        <b-link
          v-if="layoutType === 'horizontal'"
          class="navbar-brand d-xl-block d-none"
          to="/"
        >
          <logo />
        </b-link>
        <div
          v-if="isNavMenuHidden"
          class="custom-horizontal-nav header-navbar navbar-expand-sm navbar navbar-horizontal navbar-light menu-border d-none d-xl-block"
          :style="{
            background: backgroundColor
          }"
        >
          <horizontal-nav-menu />
        </div>
      </div>
      <b-navbar-nav class="nav align-items-center ml-auto">
        <b-nav-item
          v-if="$route.name === 'batch'"
          @click="onToggoleNavbar"
        >
          <feather-icon
            :style="{
              ...(textColor && { color: textColor })
            }"
            size="21"
            icon="ChevronsUpIcon"
          />
        </b-nav-item>
        <b-nav-item :to="{ name: 'documentation' }">
          <feather-icon
            :style="{
              ...(textColor && { color: textColor })
            }"
            size="21"
            icon="HelpCircleIcon"
          />
        </b-nav-item>
        <dark-toggler :text-color="textColor" />
        <b-nav-item-dropdown
          right
          toggle-class="d-flex align-items-center dropdown-user-link"
          class="dropdown-user"
        >
          <template #button-content>
            <div class="d-sm-flex d-none user-nav">
              <p
                :style="{
                  ...(textColor && { color: textColor })
                }"
                class="user-name font-weight-bolder mb-0 text-capitalize"
              >
                {{ userName }}
              </p>
              <span
                v-if="isAdmin"
                class="user-status"
                :style="{
                  ...(textColor && { color: textColor })
                }"
              >admin</span>
            </div>
            <CustomAvatar
              size="40"
              variant="light-primary"
              :text="userInitials"
              :text-color="textColor"
              background-color="rgba(115, 103, 240, 0.12)"
            />
          </template>
          <b-dropdown-item
            link-class="d-flex align-items-center"
            @click="logout"
          >
            <feather-icon
              size="16"
              icon="LogOutIcon"
              class="mr-50"
            />
            <span>Logout</span>
          </b-dropdown-item>
          <b-dropdown-item
            link-class="d-flex align-items-center"
            @click="logoutAll"
          >
            <feather-icon
              size="16"
              icon="PowerIcon"
              class="mr-50"
            />
            <span>Logout All</span>
          </b-dropdown-item>
        </b-nav-item-dropdown>
      </b-navbar-nav>
    </div>
    <div
      v-else
      class="app-auto-suggest"
    >
      <div
        class="expand-button badge badge-primary"
        variant="primary"
        @click="onToggoleNavbar"
      >
        <feather-icon
          class="text-white"
          size="24"
          icon="ChevronsDownIcon"
        />
      </div>
    </div>
  </div>
</template>

<script>
import {
  BLink, BNavbarNav, BNavItemDropdown, BDropdownItem, BNavItem,
} from 'bootstrap-vue'
import axios from 'axios'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import HorizontalNavMenu from '@core/layouts/layout-horizontal/components/horizontal-nav-menu/HorizontalNavMenu.vue'
import useAppCustomizer from '@core/layouts/components/app-customizer/useAppCustomizer'
import bus from '@/bus'
import CustomAvatar from '@core/layouts/components/app-navbar/components/CustomAvatar.vue'
import DarkToggler from '@core/layouts/components/app-navbar/components/DarkToggler.vue'
import Logo from './Logo.vue'

export default {
  components: {
    BLink,
    BNavbarNav,
    Logo,
    HorizontalNavMenu,
    CustomAvatar,
    DarkToggler,
    BNavItemDropdown,
    BDropdownItem,
    BNavItem,
  },
  props: {
    toggleVerticalMenuActive: {
      type: Function,
      default: () => {},
    },
  },
  data() {
    return {
      toggleNavbar: true,
    }
  },
  computed: {
    appTitle() {
      return this.$store.getters['theme/settings'].appTitle
    },
    userName() {
      return this.$store.getters['auth/userName']
    },
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    userInitials() {
      if (!this.userName) {
        return ''
      }
      return this.userName.split(' ').slice(0, 3).map(name => name.charAt(0)).join('')
    },
    backgroundColor() {
      return this.$store.getters['theme/settings'][this.skin].headerColor
    },
    textColor() {
      return this.$store.getters['theme/settings'][this.skin].headerTextColor
    },
    appTitleColor() {
      return this.$store.getters['theme/settings'][this.skin].appTitleColor
    },
  },
  setup() {
    const {
      isNavMenuHidden,
      layoutType,
      skin,
    } = useAppCustomizer()

    return {
      isNavMenuHidden,
      layoutType,
      skin,
    }
  },
  methods: {
    createNewTable() {
      bus.$emit('createNewTable')
    },
    logout() {
      // Server clears the HttpOnly cookie and invalidates Knox token on logout
      axios
        .post('/access_control/logout/')
        .then(() => {
          // Clear client-side auth state after successful logout
          this.$store.dispatch('auth/clearAuthData')
          this.$router.push({ name: 'login' })
        })
        .catch(error => {
          // Even if logout fails, clear client state and redirect
          this.$store.dispatch('auth/clearAuthData')
          this.$router.push({ name: 'login' })

          // Show error toast for genuine errors (network issues, server errors)
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Logout failed, but you have been signed out locally',
              icon: 'AlertTriangleIcon',
              variant: 'warning',
            },
          })
        })
    },
    logoutAll() {
      // Server clears the HttpOnly cookie and invalidates all Knox tokens
      axios
        .post('/access_control/logoutall/')
        .then(() => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Successfully logged out from all devices',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          // Clear client-side auth state after successful logout
          this.$store.dispatch('auth/clearAuthData')
          this.$router.push({ name: 'login' })
        })
        .catch(error => {
          // Even if logout fails, clear client state and redirect
          this.$store.dispatch('auth/clearAuthData')
          this.$router.push({ name: 'login' })

          // Show error toast for genuine errors (network issues, server errors)
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Logout failed, but you have been signed out locally',
              icon: 'AlertTriangleIcon',
              variant: 'warning',
            },
          })
        })
    },
    onToggoleNavbar() {
      this.toggleNavbar = !this.toggleNavbar
      bus.$emit('toggle-navbar', this.toggleNavbar)
    },
  },
}
</script>

<style lang="scss" scoped>
.expand-button {
  position: absolute;
  top: 10px;
  right: 8px;
  cursor: pointer;
}
</style>
