import getEnv from '@/utils/env'

const displayV6Navigation = getEnv('VUE_APP_DISPLAY_V6_NAVIGATION')
const displayDeveloperSettings = getEnv('VUE_APP_DISPLAY_DEVELOPER_SETTINGS') || 0
const defaultDefinitionVersion = getEnv('VUE_APP_DEFAULT_DEFINITION_VERSION')

const getNavMenuItemsV5 = isAdmin => {
  const items = [
    {
      title: 'Home',
      route: 'home',
      icon: 'HomeIcon',
    },
  ]

  if (isAdmin) {
    items.push({
      header: 'Admin',
      icon: 'SlidersIcon',
      children: [
        // {
        //   title: 'Definition Settings',
        //   route: 'admin-definition-settings',
        //   icon: 'CpuIcon',
        // },
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
}

const getNavMenuItemsV6 = (isAdmin, currentRouteName, batchType) => {
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

  if (isAdmin || defaultDefinitionVersion !== 'prod' || currentRouteName === 'batch') {
    items.push({
      header: 'Analyzer',
      icon: 'ActivityIcon',
      children: [],
    })
  }

  if (isAdmin || defaultDefinitionVersion !== 'prod') {
    items[1].children.push(
      {
        title: 'Training',
        route: 'training',
        icon: 'BookOpenIcon',
      },
    )
  }

  if (currentRouteName === 'batch') {
    items[1].children.push(
      {
        title: 'Automated Table Model',
        route: 'automated-table-model',
        icon: 'ZapIcon',
        trainingQuery: batchType === 'training' ? { 'transaction-type': 'training' } : null,
      },
    )
  }

  if (isAdmin) {
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
        {
          title: 'Definition Settings',
          route: 'admin-definition-settings',
          icon: 'CpuIcon',
        },
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
}

const getNavMenuItems = (isAdmin, currentRouteName, batchType) => {
  if (displayV6Navigation === '1') {
    return getNavMenuItemsV6(isAdmin, currentRouteName, batchType)
  }
  return getNavMenuItemsV5(isAdmin)
}

export default getNavMenuItems
