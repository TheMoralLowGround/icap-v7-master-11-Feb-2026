<template>
  <div class="d-flex flex-wrap gap-4 justify-center mt-8 cusCSS">
    <div class="d-flex ctmCSS">
      <span>
        <router-link to="/processes">
          <b-button variant="outline-secondary">
            Cancel
          </b-button>
        </router-link>
      </span>
      <b-button
        variant="outline-secondary"
        :disabled="currentStep === 0"
        @click="$emit('prev')"
      >
        <feather-icon
          icon="ArrowLeftIcon"
          class="mr-50 flip-in-rtl"
        />
        Previous
      </b-button>
    </div>

    <div class="d-flex ctmCSS">
      <b-button
        v-if="!hideSave"
        variant="success"
        type="submit"
        :disabled="loading"
        @click="$emit('submit')"
      >
        <b-spinner
          v-if="loading"
          small
          class="mr-50"
        />
        Save
      </b-button>
      <b-button
        v-if="currentStep < totalSteps - 1"
        type="button"
        @click="$emit('next')"
      >
        Next
        <feather-icon
          icon="ArrowRightIcon"
          class="ml-50 flip-in-rtl"
        />
      </b-button>
    </div>
  </div>
</template>

<script>
import { BButton, BSpinner } from 'bootstrap-vue'

export default {
  components: {
    BButton,
    BSpinner,
  },
  props: {
    currentStep: {
      type: Number,
      required: true,
    },
    totalSteps: {
      type: Number,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    hideSave: {
      type: Boolean,
      default: false,
    },
    hideCancel: {
      type: Boolean,
      default: false,
    },
    hidePrev: {
      type: Boolean,
      default: false,
    },
    hideNext: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    // Emits are automatically available in template via $emit
  },
}
</script>

<style lang="scss" scoped>
.cusCSS {
  justify-content: space-between;
}
.ctmCSS {
  gap: 1rem;
}
</style>
