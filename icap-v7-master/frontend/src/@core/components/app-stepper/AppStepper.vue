<template>
  <div
    class="app-stepper"
    :class="`app-stepper-${align} ${items[0].icon ? 'app-stepper-icons' : ''}`"
  >
    <b-row
      v-if="direction === 'horizontal'"
      no-gutters
      class="flex-nowrap overflow-hidden"
    >
      <b-col
        v-for="(item, index) in items"
        :key="item.title"
        cols="auto"
        class="app-stepper-step px-2"
        :class="[
          (!isActiveStepValid && isValidationEnabled) && 'stepper-steps-invalid',
          activeOrCompletedStepsClasses(index),
        ]"
        @click="handleStepClick(index)"
      >
        <!-- Stepper step with icon -->
        <template v-if="item.icon">
          <div class="stepper-icon-step text-high-emphasis d-flex align-center">
            <div
              class="d-flex align-center step-wrapper mx-1"
              :class="{'flex-row': direction === 'horizontal'}"
            >
              <div
                class="stepper-icon m-right"
                :class="{ 'icon-active': index === internalStep }"
              >
                <component
                  :is="item.icon"
                  v-if="typeof item.icon === 'object'"
                />
                <feather-icon
                  v-else
                  :icon="item.icon"
                  :size="String(item.size || iconSize)"
                />
              </div>
              <div>
                <p
                  class="stepper-title font-weight-medium mb-0"
                  style="margin-top: 2px;"
                >
                  {{ item.title }}
                </p>
                <p
                  v-if="item.subtitle"
                  class="stepper-subtitle mb-0"
                >
                  {{ item.subtitle }}
                </p>
              </div>
            </div>
            <!-- <feather-icon
              v-if="isHorizontalAndNotLastStep(index)"
              class="flip-in-rtl stepper-chevron-indicator mx-3"
              icon="ChevronRightIcon"
              size="20"
            /> -->
          </div>
        </template>

        <!-- Stepper step without icon -->
        <template v-else>
          <div class="d-flex align-items-center gap-x-3">
            <!-- Avatar Container -->
            <div class="flex-shrink-0 pr-1">
              <b-avatar
                v-if="index >= internalStep && (!isValidationEnabled || isActiveStepValid || index !== internalStep)"
                :variant="index === internalStep ? null : undefined"
                :class="index === internalStep ? 'bg-primary' : 'bg-light-secondary'"
                size="38"
                rounded
              >
                <h5
                  class="mb-0"
                  :class="index === internalStep ? 'text-white' : ''"
                >
                  {{ index + 1 }}
                </h5>
              </b-avatar>
              <b-avatar
                v-else-if="index >= internalStep"
                variant="danger"
                size="38"
                rounded
              >
                <feather-icon
                  icon="AlertCircleIcon"
                  size="22"
                />
              </b-avatar>
              <b-avatar
                v-else
                variant="primary"
                size="38"
                rounded
                class="bg-light-primary"
              >
                <h5 class="mb-0 text-primary">
                  {{ index + 1 }}
                </h5>
              </b-avatar>
            </div>

            <!-- Title Container -->
            <div class="flex-grow-1 d-flex flex-column justify-content-center mx-2">
              <div class="stepper-title font-weight-medium mb-0">
                {{ item.title }}
              </div>
              <div
                v-if="item.subtitle"
                class="stepper-subtitle text-sm text-muted mt-1"
              >
                {{ item.subtitle }}
              </div>
            </div>

            <!-- Chevron Indicator -->
            <!-- <feather-icon
              v-if="isHorizontalAndNotLastStep(index)"
              class="flex-shrink-0 stepper-chevron-indicator mx-3"
              icon="ChevronRightIcon"
              size="20"
            /> -->
          </div>
        </template>
      </b-col>
    </b-row>

    <!-- Vertical stepper -->
    <div
      v-else
      class="app-stepper-vertical"
    >
      <div
        v-for="(item, index) in items"
        :key="item.title"
        class="app-stepper-step py-2"
        :class="[
          (!isActiveStepValid && isValidationEnabled) && 'stepper-steps-invalid',
          activeOrCompletedStepsClasses(index),
        ]"
        @click="!isValidationEnabled && $emit('update:currentStep', index)"
      >
        <div class="d-flex align-items-start">
          <div class="stepper-icon-container">
            <template v-if="item.icon">
              <div
                class="stepper-icon"
                :class="{ 'icon-active': index === internalStep }"
              >
                <component
                  :is="item.icon"
                  v-if="typeof item.icon === 'object'"
                />
                <feather-icon
                  v-else
                  :icon="item.icon"
                  :size="String(item.size || iconSize)"
                />
              </div>
            </template>
            <template v-else>
              <b-avatar
                v-if="index >= internalStep && (!isValidationEnabled || isActiveStepValid || index !== internalStep)"
                :variant="index === internalStep ? null : 'secondary'"
                :class="index === internalStep ? 'bg-primary text-white' : ''"
                size="38"
                rounded
              >
                <h5 class="mb-0">
                  {{ index + 1 }}
                </h5>
              </b-avatar>
              <b-avatar
                v-else-if="index >= internalStep"
                variant="danger"
                size="38"
                rounded
              >
                <feather-icon
                  icon="AlertCircleIcon"
                  size="22"
                />
              </b-avatar>
              <b-avatar
                v-else
                variant="primary"
                size="38"
                rounded
                class="bg-light-primary"
              >
                <h5 class="mb-0 text-primary">
                  {{ index + 1 }}
                </h5>
              </b-avatar>
            </template>
          </div>

          <div class="stepper-content ml-3">
            <div class="stepper-title font-weight-medium">
              {{ item.title }}
            </div>
            <div
              v-if="item.subtitle"
              class="stepper-subtitle text-sm text-muted"
            >
              {{ item.subtitle }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { BRow, BCol, BAvatar } from 'bootstrap-vue'

export default {
  components: {
    BRow,
    BCol,
    BAvatar,
  },
  props: {
    items: {
      type: Array,
      required: true,
    },
    value: { // Changed from currentStep to value for v-model compatibility
      type: Number,
      default: 0,
    },
    direction: {
      type: String,
      default: 'horizontal',
    },
    iconSize: {
      type: [String, Number],
      default: '16',
    },
    isActiveStepValid: {
      type: Boolean,
      default: undefined,
    },
    align: {
      type: String,
      default: 'default',
    },
  },
  data() {
    return {
      internalStep: this.value,
    }
  },
  computed: {
    activeOrCompletedStepsClasses() {
      return index => {
        if (index < this.internalStep) {
          return 'stepper-steps-completed'
        }
        if (index === this.internalStep) {
          return 'stepper-steps-active'
        }
        return ''
      }
    },
    isHorizontalAndNotLastStep() {
      return index => this.direction === 'horizontal' && this.items.length - 1 !== index
    },
    isValidationEnabled() {
      return this.isActiveStepValid !== undefined
    },
  },
  watch: {
    value(newVal) {
      if (newVal !== undefined && newVal < this.items.length && newVal >= 0) {
        this.internalStep = newVal
      }
    },
  },
  methods: {
    handleStepClick(index) {
      if (!this.isValidationEnabled) {
        this.internalStep = index
        this.$emit('input', index) // For v-model compatibility
        this.$emit('change', index) // Additional change event
      }
    },
  },
}
</script>

<style lang="scss">
.m-right {
  margin-right: 0.5rem;
}
.app-stepper {
  .app-stepper-step {
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0 !important;

    &.stepper-steps-active {
      .stepper-title {
        color: var(--primary) !important;
      }
      .stepper-subtitle {
        color: var(--primary) !important;
      }
    }

    &.stepper-steps-completed {
      // Removed opacity reduction - all tabs should look the same except active
    }

    &.stepper-steps-invalid.stepper-steps-active {
      .stepper-icon-step,
      .stepper-title,
      .stepper-subtitle {
        color: var(--danger) !important;
      }
    }
  }
  .icon-active {
  color: var(--primary) !important;

  svg {
    stroke: var(--primary) !important;
  }
}

  .stepper-title {
    color: var(--gray-800);
    font-size: 1rem;
    font-weight: 500;
  }

  .stepper-subtitle {
    color: var(--gray-600);
    font-size: 0.8125rem;
    line-height: 1.25rem;
  }

  .stepper-chevron-indicator {
    color: var(--gray-500);
  }

  // Alignment classes
  &.app-stepper-center {
    justify-content: center;
  }

  &.app-stepper-start {
    justify-content: flex-start;
  }

  &.app-stepper-end {
    justify-content: flex-end;
  }

  // Vertical stepper
  &.app-stepper-vertical {
    .app-stepper-step {
      position: relative;
      padding-left: 2rem;

      &:not(:last-child)::after {
        content: '';
        position: absolute;
        left: 1.25rem;
        top: 3rem;
        height: calc(100% - 3rem);
        width: 2px;
        background-color: var(--gray-300);
      }

      .stepper-icon-container {
        position: relative;
        z-index: 1;
      }
    }
  }
}
</style>
