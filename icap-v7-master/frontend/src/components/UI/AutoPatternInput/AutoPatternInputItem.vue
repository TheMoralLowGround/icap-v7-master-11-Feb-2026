<template>
  <form-input
    :value="inputValue"
    readonly
    class="rounded cursor-pointer"
    @click="onClick"
  />
</template>

<script>
import {
  VBTooltip,
} from 'bootstrap-vue'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import FormInput from '../FormInput.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    FormInput,
  },
  props: {
    item: {
      type: [Object, Array],
      required: true,
    },
  },
  computed: {
    inputValue() {
      if (Array.isArray(this.item)) {
        return this.item.map(e => e.pattern).join('|')
      }

      return this.item.pattern
    },
    modelAutoPattern() {
      return this.$store.getters['dataView/modelAutoPattern']
    },
    chunkLineRecords() {
      return this.$store.getters['atm/chunkLineRecords']
    },
    batch() {
      return this.$store.getters['batch/batch']
    },
  },
  methods: {
    async onClick() {
      if (this.item?.length) {
        this.$emit('toggle-expanded')
      }

      if (!this.item?.pos) {
        return
      }

      if (!this.chunkLineRecords.length) {
        this.$store.dispatch('atm/fetchAtmChunkData')

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Auto Pattern Loading. Please try again after a while.',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })

        return
      }

      if (this.batch.id !== this.item.pos[6]) {
        const isBatchAvailable = await this.$store.dispatch('batch/checkBatchAvailability', this.item.pos[6])

        if (!isBatchAvailable) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: `This "${this.item.pos[6]}" batch is not available anymore.`,
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          return
        }
      }

      this.$store.dispatch('batch/scrollToPos', this.item.pos)
    },
  },
}
</script>

<style lang="scss" scoped>
.check-box {
  margin-left: -25px !important;
  z-index: 100;
}
</style>
