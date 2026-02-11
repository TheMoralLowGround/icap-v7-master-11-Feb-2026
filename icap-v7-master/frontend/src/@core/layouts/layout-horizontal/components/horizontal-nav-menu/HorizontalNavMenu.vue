<template>
  <div class="navbar-container main-menu-content">
    <horizontal-nav-menu-items :items="navMenuItems" />
  </div>
</template>

<script>
import getEnv from '@/utils/env'
import HorizontalNavMenuItems from './components/horizontal-nav-menu-items/HorizontalNavMenuItems.vue'

const displayV6Navigation = getEnv('VUE_APP_DISPLAY_V6_NAVIGATION')
const displayDeveloperSettings = getEnv('VUE_APP_DISPLAY_DEVELOPER_SETTINGS') || 0
const defaultDefinitionVersion = getEnv('VUE_APP_DEFAULT_DEFINITION_VERSION')

export default {
  components: {
    HorizontalNavMenuItems,
  },
  computed: {
    isAdmin() {
      return this.$store.getters['auth/isAdmin']
    },
    batchType() {
      return this.$route.query['transaction-type']
    },
    navMenuItems() {
      if (displayV6Navigation === '1') {
        return this.navMenuItemsV6
      }
      return this.navMenuItemsV5
    },
    navMenuItemsV5() {
      const items = [
        {
          title: 'Home',
          route: 'home',
          icon: 'HomeIcon',
        },
      ]

      if (this.isAdmin) {
        items.push({
          header: 'Admin',
          icon: 'SlidersIcon',
          children: [
            {
              title: 'Definition Settings',
              route: 'admin-definition-settings',
              icon: 'CpuIcon',
            },
            {
              title: 'Definitions',
              route: 'admin-definitions',
              icon: 'ListIcon',
            },
            {
              title: 'Other Settings',
              route: 'admin-other-settings',
              icon: 'SettingsIcon',
            },
          ],
        })

        items.push({
          title: 'Batches',
          route: 'batches',
          icon: 'ListIcon',
        })
      }

      return items
    },
    navMenuItemsV6() {
      const items = [
        {
          header: 'Home',
          icon: 'HomeIcon',
          children: [
            {
              title: 'Transactions',
              route: 'home',
              icon: 'BarChart2Icon',
            },
            {
              title: 'Create Process',
              route: 'create-process',
              icon: 'PlusIcon',
            },
            {
              title: 'Process Management',
              route: 'processes',
              icon: 'ListIcon',
            },
          ],
        },
      ]
      if (this.isAdmin || defaultDefinitionVersion !== 'prod' || this.$route.name === 'batch') {
        items.push({
          header: 'Analyzer',
          icon: 'ActivityIcon',
          children: [],
        })
      }
      if (this.isAdmin || defaultDefinitionVersion !== 'prod') {
        items[1].children.push(
          {
            title: 'Training',
            route: 'training',
            icon: 'BookOpenIcon',
          },
        )
      }
      if (this.$route.name === 'batch') {
        items[1].children.push(
          {
            title: 'Automated Table Model',
            route: 'automated-table-model',
            icon: 'ZapIcon',
            trainingQuery: this.batchType === 'training' ? { 'transaction-type': 'training' } : null,
          },
        )
      }

      if (this.isAdmin) {
        items.push({
          header: 'Admin',
          icon: 'SlidersIcon',
          children: [
            {
              title: 'Batches',
              route: 'batches',
              icon: 'ServerIcon',
            },
            {
              title: 'Projects',
              route: 'projects',
              icon: 'FileTextIcon',
            },
            {
              title: 'Templates',
              route: 'templates',
              icon: 'ClipboardIcon',
            },
            {
              title: 'Application Settings',
              route: 'admin-application-settings',
              icon: 'ToolIcon',
            },
            // {
            //   title: 'Definition Settings',
            //   route: 'admin-definition-settings',
            //   icon: 'CpuIcon',
            // },
            // {
            //   title: 'Other Settings',
            //   route: 'admin-other-settings',
            //   icon: 'SettingsIcon',
            // },
          ],
        })
      }

      // Check if developer settings should be added
      if (displayDeveloperSettings === '1') {
        const adminMenu = items.find(item => item.header === 'Admin')
        if (adminMenu) {
          adminMenu.children.push({
            title: 'Developer Settings',
            route: 'admin-developer-settings',
            icon: 'CodeIcon',
          })
        }
      }
      return items
    },
  },
}
</script>

<style lang="scss">
@import "~@core/scss/base/core/menu/menu-types/horizontal-menu.scss";
</style>
