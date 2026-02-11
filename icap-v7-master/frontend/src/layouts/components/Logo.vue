<template>
  <div>
    <b-img
      v-if="logoUrl"
      :src="logoUrl"
      alt="logo"
      height="35"
    />
    <b-img
      v-if="!logoUrl && skin === 'dark'"
      :src="require('@/assets/images/logo/logo-ai-doc-builder-dark.png')"
      alt="logo"
      height="35"
    />
    <b-img
      v-if="!logoUrl && skin === 'light'"
      :src="require('@/assets/images/logo/logo-ai-doc-builder.png')"
      alt="logo"
      height="35"
    />
  </div>
</template>

<script>
import { BImg } from 'bootstrap-vue'
import useAppCustomizer from '@core/layouts/components/app-customizer/useAppCustomizer'

export default {
  components: {
    BImg,
  },
  setup() {
    const {
      skin,
    } = useAppCustomizer()

    return {
      skin,
    }
  },
  computed: {
    logoUrl() {
      const themeSettings = this.$store.getters['theme/settings']
      return themeSettings[this.skin].logo
    },
  },
}
</script>
