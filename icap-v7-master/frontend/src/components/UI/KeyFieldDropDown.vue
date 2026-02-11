<template>
  <div>
    <validation-provider
      #default="{ errors }"
      :name="label"
      :rules="validationRules"
      :vid="`${validationKey}`"
    >
      <div class="d-flex align-items-center">
        <b-form-group
          class="mb-0 flex-grow-1"
          :state="errors.length > 0 ? false : null"
        >
          <v-select
            ref="keyOptionsForRules"
            v-model="items[0]"
            :options="keyOptionsForRules"
            :reduce="option => option.value"
            :placeholder="label"
            @open="handleDropdownOpen(items[0])"
          />
        </b-form-group>

        <div
          v-if="multipleDropDown"
        >
          <feather-icon
            v-if="expanded === false"
            icon="ChevronUpIcon"
            class="cursor-pointer mx-50"
            size="20"
            @click="expanded = true"
          />
          <feather-icon
            v-if="expanded === true"
            icon="ChevronDownIcon"
            class="cursor-pointer mx-50"
            size="20"
            @click="expanded = false"
          />
        </div>
      </div>
      <small class="text-danger">{{ errors[0] }}</small>
    </validation-provider>

    <div
      v-if="multipleDropDown && expanded"
      class="mt-50"
    >
      <validation-provider
        v-for="(item, index) of items.slice(1)"
        #default="{ errors }"
        :key="`item-${item.label}-${index}`"
        tag="div"
        :name="label"
        :rules="validationRules"
        :vid="`${validationKey}_${index + 1}`"
        class="mb-50"
      >
        <div class="d-flex align-items-center">
          <b-form-group
            class="mb-0 flex-grow-1"
            :state="errors.length > 0 ? false : null"
          >
            <v-select
              v-model="items[index + 1]"
              :options="keyOptionsForRules"
              :reduce="option => option.value"
              :placeholder="label"
            />
          </b-form-group>
          <div>
            <feather-icon
              icon="Trash2Icon"
              class="cursor-pointer mx-50"
              size="20"
              @click="deleteItem(index + 1)"
            />
          </div>
        </div>
        <small class="text-danger">{{ errors[0] }}</small>
      </validation-provider>

      <div class="mr-50">
        <add-item
          :label="label"
          @add="addItems"
        />
      </div>
    </div>

  </div>
</template>

<script>
import {
  BFormGroup,
} from 'bootstrap-vue'
import { ValidationProvider } from 'vee-validate'
import vSelect from 'vue-select'
import AddItem from './AddItem.vue'

export default {
  components: {
    vSelect,
    BFormGroup,
    AddItem,
    ValidationProvider,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    value: {
      type: [Object, Array, String],
      required: false,
      default() {
        return null
      },
    },
    validationRules: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    validationKey: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
    initializeExpanded: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    multipleDropDown: {
      type: Boolean,
      required: false,
      default() {
        return false
      },
    },
    ruleInputs: {
      type: Object,
      required: false,
      default() {
        return {}
      },
    },
    inputFieldKey: {
      type: String,
      required: false,
      default() {
        return ''
      },
    },
  },
  data() {
    return {
      items: [],
      expanded: false,
    }
  },
  computed: {
    out() {
      const items = this.items.map(e => e?.value || e)

      if (this.multipleDropDown) {
        return items || []
      }

      return items.length ? items[0] : []
    },
    batchView() {
      return this.$store.getters['batch/view'] // Current view of the batch
    },
    selectedDefinition() {
      return this.$store.getters['dataView/selectedDefinition']
    },
    keyOptionsForRules() {
      let options = this.$store.getters['definitionSettings/keyOptionsForRules']

      // if (this.selectedDefinition?.table[0]?.table_definition_data?.models?.type === 'multishipment') {
      if (this.batchView === 'table') {
        options = this.$store.getters['definitionSettings/keyOptionsForTableLookups']
      }
      const UniqeRuleoptions = options.filter((item, index) => options.findIndex(el => el.label === item.label) === index)
      return UniqeRuleoptions
    },
  },
  watch: {
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
    this.expanded = this.initializeExpanded
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      if (!this.value) {
        return
      }

      const items = Array.isArray(this.value) ? [...this.value] : [this.value]

      items.forEach((e, i) => {
        const item = {
          label: e.parent ? `${e.parent} - ${e.fieldInfo?.keyValue}` : e.fieldInfo?.keyValue,
          value: e,
        }

        const index = this.keyOptionsForRules.findIndex(elem => elem.label === item.label)

        items[i] = index === -1 ? item : this.keyOptionsForRules[index]
      })

      this.items = items
    },
    addItems(value) {
      let count = value

      if (!this.items.length) {
        count += 1
      }

      const items = []

      for (let i = 0; i < count; i += 1) {
        const item = ''
        items.push(item)
      }

      this.items = this.items.concat(items)
    },
    deleteItem(index) {
      this.items.splice(index, 1)
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    handleDropdownOpen(item) {
      this.$nextTick(() => {
        const dropdownMenu = this.$refs.keyOptionsForRules?.$refs.dropdownMenu
        if (!dropdownMenu || !this.items[0]) return // Ensure items[0] exists

        const selectedIndex = this.keyOptionsForRules.findIndex(option => option?.value?.fieldInfo?.keyValue === (item?.fieldInfo?.keyValue ? item?.fieldInfo?.keyValue : item?.value?.fieldInfo?.keyValue))

        if (selectedIndex >= 0) {
          const itemHeight = dropdownMenu.scrollHeight / this.keyOptionsForRules.length
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenu.scrollTop = scrollPosition
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
