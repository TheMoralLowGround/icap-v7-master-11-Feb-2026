<template>
  <li
    v-if="canViewHorizontalNavMenuHeaderGroup(item)"
    class="dropdown nav-item"
    :class="{
      'sidebar-group-active active open': isActive,
      'show': isOpen,
    }"
    @mouseenter="() => updateGroupOpen(true)"
    @mouseleave="() => updateGroupOpen(false)"
  >
    <b-link
      :style="{
        ...(textColor && !isActive && { color: textColor })
      }"
      class="nav-link dropdown-toggle d-flex align-items-center"
    >
      <feather-icon
        :style="{
          ...(textColor && !isActive && { color: textColor })
        }"
        size="14"
        :icon="item.icon"
      />
      <span>{{ t(item.header) }}</span>
    </b-link>
    <ul class="dropdown-menu">
      <component
        :is="resolveHorizontalNavMenuItemComponent(child)"
        v-for="child in item.children"
        :key="child.title"
        :item="child"
      />
    </ul>
  </li>
</template>

<script>
import { BLink } from 'bootstrap-vue'
import { resolveHorizontalNavMenuItemComponent } from '@core/layouts/utils'
import { useUtils as useAclUtils } from '@core/libs/acl'
import { useUtils as useI18nUtils } from '@core/libs/i18n'
import useAppCustomizer from '@core/layouts/components/app-customizer/useAppCustomizer'
import useHorizontalNavMenuHeaderGroup from './useHorizontalNavMenuHeaderGroup'
import mixinHorizontalNavMenuHeaderGroup from './mixinHorizontalNavMenuHeaderGroup'

import HorizontalNavMenuGroup from '../horizontal-nav-menu-group/HorizontalNavMenuGroup.vue'
import HorizontalNavMenuLink from '../horizontal-nav-menu-link/HorizontalNavMenuLink.vue'

export default {
  components: {
    BLink,
    HorizontalNavMenuGroup,
    HorizontalNavMenuLink,
  },
  mixins: [mixinHorizontalNavMenuHeaderGroup],
  props: {
    item: {
      type: Object,
      required: true,
    },
  },
  computed: {
    textColor() {
      return this.$store.getters['theme/settings'][this.skin].headerTextColor
    },
  },
  setup(props) {
    const { skin } = useAppCustomizer()
    const {
      isActive,
      updateIsActive,
      isOpen,
      updateGroupOpen,
    } = useHorizontalNavMenuHeaderGroup(props.item)

    const { t } = useI18nUtils()
    const { canViewHorizontalNavMenuHeaderGroup } = useAclUtils()

    return {
      skin,
      isOpen,
      isActive,
      updateGroupOpen,
      updateIsActive,
      resolveHorizontalNavMenuItemComponent,

      // ACL
      canViewHorizontalNavMenuHeaderGroup,

      // i18n
      t,
    }
  },
}
</script>
