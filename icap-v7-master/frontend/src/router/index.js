import Vue from 'vue'
import VueRouter from 'vue-router'
import multiguard from 'vue-router-multiguard'

import getEnv from '@/utils/env'
import store from '../store'

import adminUser from '../middleware/adminUser'
import auth from '../middleware/auth'
import developer from '../middleware/developer'
import guest from '../middleware/guest'
import projectRoute from './projectRoute'

const displayV6Navigation = getEnv('VUE_APP_DISPLAY_V6_NAVIGATION')

Vue.use(VueRouter)

const routesV5 = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    beforeEnter: multiguard([guest]),
    meta: {
      layout: 'full',
      resource: 'Auth',
      redirectIfLoggedIn: true,
    },
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Transactions',
    },
  },
  {
    path: '/batch/:id',
    name: 'batch',
    component: () => import('@/views/Batch.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Batch',
      contentClass: 'batch-page-wrapper',
    },
  },
  // {
  //   path: '/admin/definition-settings',
  //   name: 'admin-definition-settings',
  //   component: () => import('@/views/Admin/DefinitionSettings.vue'),
  //   beforeEnter: multiguard([auth, adminUser]),
  //   meta: {
  //     title: 'Definition Settings',
  //   },
  // },
  {
    path: '/admin/definitions',
    name: 'admin-definitions',
    component: () => import('@/views/Admin/Definitions.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Definitions',
    },
  },
  {
    path: '/admin/other-settings',
    name: 'admin-other-settings',
    component: () => import('@/views/Admin/OtherSettings.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Other Settings',
    },
  },
  {
    path: '/documentation',
    name: 'documentation',
    component: () => import('@/views/Documentation.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Documentation',
    },
  },
  {
    path: '/batches',
    name: 'batches',
    component: () => import('@/views/UploadBatch.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Batches',
    },
  },
  {
    path: '/error-404',
    name: 'error-404',
    component: () => import('@/views/error/Error404.vue'),
    meta: {
      title: 'Page Not Found',
      layout: 'full',
      resource: 'Auth',
      action: 'read',
    },
  },
  {
    path: '/error-403',
    name: 'error-403',
    component: () => import('@/views/error/Error403.vue'),
    meta: {
      title: 'Unauthorized',
      layout: 'full',
      resource: 'Auth',
      action: 'read',
    },
  },
  {
    path: '*',
    redirect: 'error-404',
  },
]

const routesV6 = [
  ...projectRoute,
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    beforeEnter: multiguard([guest]),
    meta: {
      layout: 'full',
      resource: 'Auth',
      redirectIfLoggedIn: true,
    },
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Emails.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Transactions',
    },
  },
  {
    path: '/verification/:id',
    name: 'verification',
    component: () => import('@/views/Batch.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Verification',
      contentClass: 'batch-page-wrapper',
    },
  },
  {
    path: '/batch/:id',
    name: 'batch',
    component: () => import('@/views/Batch.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Batch',
      contentClass: 'batch-page-wrapper',
    },
  },
  {
    path: '/classification/:id',
    name: 'classification',
    component: () => import('@/views/Classification.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Manual Classification',
      contentClass: 'batch-page-wrapper',
    },
  },
  // {
  //   path: '/projects',
  //   name: 'projects',
  //   component: () => import('@/views/Projects.vue'),
  //   beforeEnter: multiguard([auth, adminUser]),
  //   meta: {
  //     title: 'Projects',
  //   },
  // },
  {
    path: '/templates/create-template',
    name: 'create-template',
    component: () => import('@/views/CreateTemplete.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Create Template',
    },
  },
  {
    path: '/templates/edit-template/:id',
    name: 'edit-template',
    component: () => import('@/views/CreateTemplete.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Edit Template',
    },
  },
  {
    path: '/templates',
    name: 'templates',
    component: () => import('@/views/Templetes.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Templates',
    },
  },
  {
    path: '/templates/:id',
    name: 'template-batch',
    component: () => import('@/views/Batch.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Template Batch',
    },
  },
  {
    path: '/processes',
    name: 'processes',
    component: () => import('@/views/Profiles.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Process Management',
    },
  },
  {
    path: '/processes/create',
    name: 'create-process',
    component: () => import('@/views/ProfileForm.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Create Process',
    },
  },
  {
    path: '/processes/:id',
    name: 'edit-process',
    component: () => import('@/views/ProfileForm.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Process Configuration',
    },
  },
  {
    path: '/analyzer/training',
    name: 'training',
    component: () => import('@/views/Training.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Training',
    },
  },
  {
    path: '/analyzer/automated-table-model/:id',
    name: 'automated-table-model',
    component: () => import('@/views/Batch.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      contentClass: 'batch-page-wrapper',
    },
  },
  {
    path: '/admin/application-settings',
    name: 'admin-application-settings',
    component: () => import('@/views/Admin/ApplicationSettings.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Application Settings',
    },
  },
  {
    path: '/admin/developer-settings',
    name: 'admin-developer-settings',
    component: () => import('@/views/Admin/DeveloperSettings.vue'),
    beforeEnter: multiguard([auth, adminUser, developer]),
    meta: {
      title: 'Developer Settings',
    },
  },
  // {
  //   path: '/admin/definition-settings',
  //   name: 'admin-definition-settings',
  //   component: () => import('@/views/Admin/DefinitionSettings.vue'),
  //   beforeEnter: multiguard([auth, adminUser]),
  //   meta: {
  //     title: 'Definition Settings',
  //   },
  // },
  // {
  //   path: '/admin/other-settings',
  //   name: 'admin-other-settings',
  //   component: () => import('@/views/Admin/OtherSettings.vue'),
  //   beforeEnter: multiguard([auth, adminUser]),
  //   meta: {
  //     title: 'Other Settings',
  //   },
  // },
  {
    path: '/documentation',
    name: 'documentation',
    component: () => import('@/views/Documentation.vue'),
    beforeEnter: multiguard([auth]),
    meta: {
      title: 'Documentation',
    },
  },
  {
    path: '/batches',
    name: 'batches',
    component: () => import('@/views/UploadBatch.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Batches',
    },
  },
  {
    path: '/error-404',
    name: 'error-404',
    component: () => import('@/views/error/Error404.vue'),
    meta: {
      title: 'Page Not Found',
      layout: 'full',
      resource: 'Auth',
      action: 'read',
    },
  },
  {
    path: '/error-403',
    name: 'error-403',
    component: () => import('@/views/error/Error403.vue'),
    meta: {
      title: 'Unauthorized',
      layout: 'full',
      resource: 'Auth',
      action: 'read',
    },
  },
  {
    path: '*',
    redirect: 'error-404',
  },
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  scrollBehavior() {
    return { x: 0, y: 0 }
  },
  routes: displayV6Navigation === '1' ? routesV6 : routesV5,
})

router.beforeEach((to, from, next) => {
  if (!from.name) {
    localStorage.removeItem('home-last-active-page')
    localStorage.removeItem('email-batches-last-active-page')
  }

  next()
})

router.afterEach(to => {
  const pageTitle = to.meta?.title || null
  store.commit('app/SET_CURRENT_PAGE_TITLE', pageTitle)
})

export default router
