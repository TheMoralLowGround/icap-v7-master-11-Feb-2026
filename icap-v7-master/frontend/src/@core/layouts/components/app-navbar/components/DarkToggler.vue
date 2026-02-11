<template>
  <b-nav-item @click="skin = isDark ? 'light' : 'dark'">
    <feather-icon
      :style="{
        ...(textColor && { color: textColor })
      }"
      size="21"
      :icon="`${isDark ? 'Sun' : 'Moon'}Icon`"
    />
  </b-nav-item>
</template>

<script>
import useAppConfig from '@core/app-config/useAppConfig'
import { computed } from '@vue/composition-api'
import { BNavItem } from 'bootstrap-vue'

export default {
  components: {
    BNavItem,
  },
  props: {
    textColor: {
      type: [String, null],
      default: null,
    },
  },
  setup() {
    const { skin } = useAppConfig()

    const isDark = computed(() => skin.value === 'dark')

    return { skin, isDark }
  },
}
</script>
