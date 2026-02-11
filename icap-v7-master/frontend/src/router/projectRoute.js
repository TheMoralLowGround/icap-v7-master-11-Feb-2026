import multiguard from 'vue-router-multiguard'
import adminUser from '../middleware/adminUser'
import auth from '../middleware/auth'

const projectRoute = [
  {
    path: '/projects',
    name: 'projects',
    component: () => import('@/views/Projects.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'Projects',
    },
  },
  {
    path: '/project/:id',
    name: 'projectDetails',
    component: () => import('@/views/ProjectDetails.vue'),
    beforeEnter: multiguard([auth, adminUser]),
    meta: {
      title: 'ProjectDetails',
    },
  },
]

export default projectRoute
