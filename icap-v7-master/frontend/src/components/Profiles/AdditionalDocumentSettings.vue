<template>
  <b-modal
    v-model="showModal"
    size="lg"
    :title="`Additional Document Settings (${document.docType})`"
    centered
    no-close-on-backdrop
    @hidden="$emit('modal-closed')"
    @ok="updatedDocument = document"
  >
    <div>
      <validation-provider
        name="TEMPLATE"
        vid="template"
        mode="eager"
      >
        <b-form-group
          label-cols="12"
          label="TEMPLATE"
          label-for="template"
          class="mb-0"
        >
          <template #description>
            <v-select
              id="template"
              ref="SelectedTemplate"
              v-model="document.template"
              :options="templateNames"
              label="label"
              style="font-size: 15px; margin-bottom: 1rem;"
              @open="scrollToSelected"
            />
          </template>
        </b-form-group>
      </validation-provider>
      <b-form-group
        v-if="document.contentLocation === 'Email Body'"
        label-cols="10"
        label="SHOW EMBEDDED IMG"
        class="mb-0"
      >
        <template #description>
          <div class="d-flex justify-content-end">
            <b-form-checkbox
              v-model="document.showEmbeddedImg"
              switch
            />
          </div>
        </template>
      </b-form-group>
      <b-form-group
        label-cols="10"
        label="PAGE ROTATE"
        class="mb-0"
      >
        <template #description>
          <div class="d-flex justify-content-end">
            <b-form-checkbox
              v-model="document.pageRotage"
              switch
            />
          </div>
        </template>
      </b-form-group>
      <b-form-group
        label-cols="10"
        label="BARCODE"
        class="mb-0"
      >
        <template #description>
          <div class="d-flex justify-content-end">
            <b-form-checkbox
              v-model="document.barcode"
              switch
            />
          </div>
        </template>
      </b-form-group>
    </div>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        variant="primary"
        type="submit"
        @click="ok()"
      >
        Update
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import { isEqual, cloneDeep } from 'lodash'
import {
  BFormGroup, BButton, BModal, BFormCheckbox,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { ValidationProvider } from 'vee-validate'

export default {
  components: {
    BFormGroup,
    BButton,
    BModal,
    BFormCheckbox,
    vSelect,
    ValidationProvider,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    templateNames: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      document: null,
      updatedDocument: null,
    }
  },
  computed: {
    out() {
      return cloneDeep(this.updatedDocument)
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
  },
  methods: {
    setInternalState() {
      this.document = cloneDeep(this.value)
      this.updatedDocument = cloneDeep(this.value)
    },
    scrollToSelected() {
      this.$nextTick(() => {
        setTimeout(() => {
          const dropdown = document.querySelector('.vs__dropdown-menu')
          if (!dropdown) return

          const dropdownItems = dropdown.querySelectorAll('.vs__dropdown-option')
          if (!dropdownItems.length) return

          // Get the selected index
          const selectedIndex = this.templateNames.indexOf(this.document?.template)
          if (selectedIndex === -1) return

          // Get the selected item
          const selectedItem = dropdownItems[selectedIndex]
          if (!selectedItem) return

          // Scroll into view smoothly
          selectedItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' })

          // Alternative: Manually set scrollTop
          dropdown.scrollTop = selectedItem.offsetTop - dropdown.offsetHeight / 2
        }, 200) // Delay ensures dropdown is rendered
      })
    },
  },
}
</script>
