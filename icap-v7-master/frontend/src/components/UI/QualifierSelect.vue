<template>
  <validation-provider
    #default="{ errors }"
    :name="label"
    :rules="qualifier && !isQualifierValueEmpty ? validationRules : ''"
    :vid="validationKey"
  >
    <b-form-group
      class="mb-0 bg-transparent"
      :state="errors.length > 0 ? false:null"
    >
      <v-select
        ref="vSelect"
        v-model="qualifierValue"
        :options="options"
        label="label"
        :disabled="!qualifier || isQualifierValueEmpty"
        :reduce="option => option.value"
        @open="handleDropdownOpen"
      />
      <small class="text-danger">{{ errors[0] }}</small>
    </b-form-group>
  </validation-provider>
</template>

<script>
import { BFormGroup } from 'bootstrap-vue'
import vSelect from 'vue-select'
import { ValidationProvider } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    vSelect,
    BFormGroup,
    ValidationProvider,
  },
  props: {
    value: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    keyValue: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    label: {
      type: String,
      required: true,
    },
    validationKey: {
      type: String,
      required: false,
      default() {
        return null
      },
    },
    isQualifierValueEmpty: {
      type: Boolean,
      default: () => false,
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    keyOptions: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      qualifierValue: null,
    }
  },
  computed: {
    qualifiers() {
      return this.$store.getters['definitionSettings/keyQualifiers']
    },
    qualifier() {
      if (!this.keyValue) {
        return null
      }
      const keyOptionItem = this.keyOptions.find(item => item.keyValue === this.keyValue)
      if (!keyOptionItem?.qualifier) {
        return null
      }
      return this.qualifiers.find((qualifier => qualifier.name === keyOptionItem.qualifier))
    },
    out() {
      return this.qualifierValue
    },
    options() {
      if (this.qualifier) {
        return this.qualifier.options
      }
      return []
    },
  },
  watch: {
    // qualifier: {
    //   deep: true,
    //   handler() {
    //     this.qualifierValue = null
    //   },
    // },
    keyValue: {
      deep: true,
      handler(val, oldVal) {
        if (val !== oldVal) {
          this.qualifierValue = null
        }
      },
    },
    out: {
      handler(val) {
        if (val !== this.value) {
          this.$emit('input', val)
        }
      },
    },
    value: {
      handler(val) {
        if (val !== this.out) {
          this.setInternalState()
        }
      },
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      this.qualifierValue = this.value
    },

    // Scrolls the dropdown menu to bring the selected item into view.
    handleDropdownOpen() {
      this.$nextTick(() => {
        // Emits an event when a dropdown is opened
        this.$emit('dropdownOpen')

        const dropdownMenuItems = this.$refs.vSelect.$el.querySelector('.vs__dropdown-menu')
        if (!dropdownMenuItems) return // Ensure the dropdown exists before proceeding

        const selectedIndex = this.options.findIndex(option => option.value === this.qualifierValue)
        if (selectedIndex >= 0) {
          const itemHeight = dropdownMenuItems.scrollHeight / this.options.length
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';.red-200 .v-select.vs--disabled .vs__dropdown-toggle {
  background-color: rgb(247, 207, 207) !important;
  color: rgb(63, 61, 61) !important;
  opacity: 1 !important;
}

.red-200 .v-select .vs--disabled .vs__selected {
  color: rgb(63, 61, 61) !important;
}

.red-200 .v-select .vs--disabled {
  .vs__dropdown-toggle {
    background-color: rgb(247, 207, 207) !important;
    color: rgb(63, 61, 61) !important;
    opacity: 1 !important;
  }

  .vs__search{
    background-color: rgb(247, 207, 207) !important;
  }
 .vs__selected {
  color: rgb(63, 61, 61) !important;
  background-color: rgb(247, 207, 207) !important;
}
  .vs__open-indicator {
    background-color: rgb(247, 207, 207) !important;
  }
  .vs--single {
    border: 1px solid #a1a1a3;
  }
  .vs__dropdown-toggle {
    border: 1px solid #a1a1a3;
  }
}
</style>
