import { ref, computed, watch } from '@vue/composition-api'

const normalize = value => (value || '').toString().toLowerCase()

export default function useAutoSuggest({ data = {}, searchLimit = 10 } = {}) {
  const pagesSource = computed(() => data.pages?.data || [])
  const searchQuery = ref('')
  const filteredData = ref({ pages: [] })

  const filterPages = query => {
    const normalizedQuery = normalize(query)

    if (!normalizedQuery) {
      return pagesSource.value.slice(0, searchLimit)
    }

    return pagesSource.value
      .filter(page => normalize(page.title).includes(normalizedQuery)
        || normalize(page.route?.name).includes(normalizedQuery)
        || normalize(page.route?.path).includes(normalizedQuery))
      .slice(0, searchLimit)
  }

  const recompute = () => {
    filteredData.value = {
      pages: filterPages(searchQuery.value),
    }
  }

  watch(pagesSource, recompute, { immediate: true })
  watch(searchQuery, recompute)

  const resetsearchQuery = () => {
    searchQuery.value = ''
  }

  return {
    searchQuery,
    resetsearchQuery,
    filteredData,
  }
}
