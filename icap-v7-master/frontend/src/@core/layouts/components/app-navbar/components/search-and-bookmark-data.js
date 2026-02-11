import router from '@/router'

const DEFAULT_ICON = 'CircleIcon'
const DEFAULT_BOOKMARKED_ROUTES = new Set([
  'home',
  'batches',
  'admin-definitions',
])

const transformRouteToBookmark = route => ({
  title: route.meta?.title || route.meta?.pageTitle || route.name,
  route: { name: route.name, params: route.meta?.params || {}, query: route.meta?.query || {} },
  path: route.path,
  icon: route.meta?.icon || DEFAULT_ICON,
  isBookmarked: DEFAULT_BOOKMARKED_ROUTES.has(route.name),
})

const buildPages = () => {
  const uniqueRoutesMap = new Map()

  router.getRoutes()
    .filter(route => route.name && (route.meta?.title || route.meta?.pageTitle))
    .forEach(route => {
      if (!uniqueRoutesMap.has(route.name)) {
        uniqueRoutesMap.set(route.name, transformRouteToBookmark(route))
      }
    })

  return Array.from(uniqueRoutesMap.values())
}

const pages = buildPages()

export default {
  pages: {
    label: 'Pages',
    data: pages,
  },
}
