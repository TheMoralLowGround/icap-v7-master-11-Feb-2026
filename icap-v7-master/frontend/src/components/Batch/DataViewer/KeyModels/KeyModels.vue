<!--
 Organization: AIDocbuilder Inc.
 File: KeyModels.vue
 Version: 6.0

 Authors:
   - Vinay - Initial implementation
   - Ali - Code optimization

 Last Updated By: Ali
 Last Updated At: 2024-12-23

 Description:
   This component handles the dynamic creation and management of key models, displaying a set of fields
   for each model. It allows users to add, delete, and edit models while also supporting multiple field types
   (text, select, pipe-separated, and multiple-text inputs). The component ensures that the state of the models
   is synced with the Vuex store.

 Main Features:
   - Dynamically generates forms based on the model fields defined in the store.
   - Supports adding multiple models at once, with automatic scroll to the newly added model.
   - Each model can have different types of fields (e.g., text, select, pipe-separated, multiple-text).
   - Allows for deleting individual models from the list.
   - Utilizes Vuex for managing application settings, options, and key settings.

 Dependencies:
   - `BootstrapVue` for the layout components like `BFormGroup`, `BRow`, and `BCol`.
   - `vue-select` for the select input components.
   - `lodash` for deep cloning and equality checks.
   - Custom components: `FormInput`, `PipeSeparatedInput`, and `MultipleTextInput`.
   - `bus` (an event bus) for managing global event communication.

 Notes:
   - The models array is a reactive property that keeps track of the current state of all key models.
   - The component dynamically renders different types of form fields based on the type of each field in the model.
-->

<template>
  <div
    ref="keyModelsWrapper"
    class="key-models-wrapper"
  >
    <b-col md="12">
      <b-row
        v-for="(model, modelIndex) of models"
        :key="modelIndex"
        class="key-model-item"
      >
        <b-col
          cols="12"
        >
          <div class="d-flex align-items-center justify-content-between">
            <h5 class="mb-0">
              Model #{{ modelIndex + 1 }}
            </h5>
            <feather-icon
              v-b-tooltip.hover
              title="Delete Model"
              icon="Trash2Icon"
              class="cursor-pointer delete-model-btn"
              size="20"
              @click.stop="deleteModel(modelIndex)"
            />
          </div>
        </b-col>
        <b-col
          v-for="(field, fieldIndex) of modelFields"
          :key="fieldIndex"
          lg="3"
        >
          <b-form-group
            v-if="field.type === 'text'"
            :label="field.label ? field.label: field.key"
          >
            <form-input
              v-model="models[modelIndex][field.key]"
              type="text"

              :placeholder="field.key"
            />
          </b-form-group>
          <b-form-group
            v-if="field.type === 'select'"
            :label="field.label ? field.label: field.key"
          >
            <v-select
              v-model="models[modelIndex][field.key]"
              :label="options[field.optionsId].lableKey"
              :options="options[field.optionsId].items"
              :reduce="option => option[options[field.optionsId].valueKey]"
            />
          </b-form-group>
          <pipe-separated-input
            v-if="field.type === 'pipeSeparatedInput'"
            v-model="models[modelIndex][field.key]"
            :label="field.label ? field.label: field.key"
            selection-value-attr="text"
            listenable-input
          />

          <multiple-text-input
            v-if="field.type === 'multiple-text'"
            v-model="models[modelIndex][field.key]"
            :placeholder="field.label ? field.label: field.key"
            :input-field-placeholder="field.inputFieldPlaceholder"
          />
        </b-col>
      </b-row>
    </b-col>
  </div>
</template>

<script>
import {
  BFormGroup, VBTooltip, BRow, BCol,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { isEqual, cloneDeep } from 'lodash'
import bus from '@/bus'
import FormInput from '@/components/UI/FormInput.vue'
import PipeSeparatedInput from '@/components/UI/PipeSeparatedInput.vue'
import MultipleTextInput from '@/components/UI/MultipleTextInput/MultipleTextInput.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BFormGroup,
    vSelect,
    FormInput,
    BRow,
    BCol,
    PipeSeparatedInput,
    MultipleTextInput,
  },
  props: {
    value: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      models: [],
    }
  },
  computed: {
    modelFields() {
      return this.$store.getters['applicationSettings/keySettings'].model.fields
    },
    options() {
      return {
        ...this.$store.getters['applicationSettings/options'],
        ...this.$store.getters['definitionSettings/options'],
      }
    },
    out() {
      return cloneDeep(this.models)
    },
  },
  watch: {
    out: {
      handler(val) {
        if (!isEqual(val, this.value)) {
          this.$emit('input', val)
        }
      },
      deep: true,
    },
    value: {
      handler(val) {
        if (!isEqual(val, this.out)) {
          this.setInternalState()
        }
      },
      deep: true,
    },
  },
  created() {
    this.setInternalState()
    bus.$on('dataView/addKeyModels', this.addKeyModels)
  },
  destroyed() {
    bus.$off('dataView/addKeyModels', this.addKeyModels)
  },
  methods: {
    // Initializes the models array based on the incoming value and model fields.
    setInternalState() {
      const items = this.value.map(record => {
        const item = {}
        this.modelFields.forEach(modelField => {
          let value
          if (modelField.type === 'multiple-text') {
            value = record[modelField.key] || []
          } else {
            value = String(record[modelField.key] || '')
          }

          // Check for "trimAddressTillCountry" and update its value to "true" if it is "false"
          if (modelField.key === 'trimAddressTillCountry') {
            value = value === 'false' ? 'true' : value
          }

          item[modelField.key] = value
        })
        return item
      })
      this.models = items
    },
    // Adds a specified number of new key models with default values and scrolls to the last added model.
    addKeyModels(count) {
      const lastRowIndex = this.models.length - 1
      const expandStatus = []
      const cols = []
      for (let i = 0; i < count; i += 1) {
        const col = {}
        this.modelFields.forEach(modelField => {
          col[modelField.key] = modelField.defaultValue || ''
        })
        cols.push(col)
        expandStatus.push(false)
      }

      this.models = this.models.concat(cols)
      this.$nextTick(() => {
        this.scrollToIndex(lastRowIndex + 1)
      })
    },
    // Deletes a model from the list at the given index.
    deleteModel(index) {
      this.models.splice(index, 1)
    },
    // Scrolls to the model at the specified index in the list.
    scrollToIndex(index) {
      const { keyModelsWrapper } = this.$refs
      const keyModelItem = keyModelsWrapper.querySelectorAll('.key-model-item')[index]
      keyModelsWrapper.scrollTop = keyModelItem.offsetTop
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>

<style scoped>
.key-models-wrapper {
    height: 100%!important;
    overflow-y: scroll;
}
</style>
