// eslint-disable-next-line object-curly-newline
import { ref, watch, inject, computed } from '@vue/composition-api'
import store from '@/store'
import { isNavGroupActive } from '@core/layouts/utils'

export default function useVerticalNavMenuGroup(item) {
  // ------------------------------------------------
  // isOpen
  // ------------------------------------------------
  const isOpen = ref(false)

  // ------------------------------------------------
  // isActive
  // ------------------------------------------------
  const isActive = ref(false)

  // ------------------------------------------------
  // isVerticalMenuCollapsed
  // ------------------------------------------------
  const isVerticalMenuCollapsed = computed(() => store.state.verticalMenu.isVerticalMenuCollapsed)

  watch(isVerticalMenuCollapsed, val => {
    /* eslint-disable no-use-before-define */
    // * Handles case if routing is done outside of vertical menu
    // i.e. From Customizer Collapse or Using Link
    if (!isMouseHovered.value) {
      if (val) isOpen.value = false
      else if (!val && isActive.value) isOpen.value = true
    }
    /* eslint-enable */
  })

  // ------------------------------------------------
  // isMouseHovered (with default value)
  // ------------------------------------------------
  const isMouseHovered = inject('isMouseHovered', ref(false))

  // Safe watch for isMouseHovered
  if (isMouseHovered) {
    watch(() => isMouseHovered.value, val => {
      if (isVerticalMenuCollapsed.value) {
        isOpen.value = val && isActive.value
      }
    })
  }

  // ------------------------------------------------
  // Other Methods
  // ------------------------------------------------
  const doesHaveChild = title => item.children.some(child => child.title === title)

  // ------------------------------------------------
  // openGroups (with default value)
  // ------------------------------------------------
  const openGroups = inject('openGroups', ref([]))

  // Safe watch for openGroups
  if (openGroups) {
    watch(() => openGroups.value, currentOpenGroups => {
      const clickedGroup = currentOpenGroups[currentOpenGroups.length - 1]
      if (clickedGroup !== item.title && !isActive.value) {
        if (!doesHaveChild(clickedGroup)) isOpen.value = false
      }
    })
  }

  watch(isOpen, val => {
    if (val && openGroups?.value) {
      openGroups.value.push(item.title)
    }
  })

  const updateGroupOpen = val => {
    isOpen.value = val
  }

  watch(isActive, val => {
    if (val) {
      if (!isVerticalMenuCollapsed.value) isOpen.value = val
    } else {
      isOpen.value = val
    }
  })

  const updateIsActive = () => {
    isActive.value = isNavGroupActive(item.children)
  }

  return {
    isOpen,
    isActive,
    updateGroupOpen,
    updateIsActive,
  }
}
