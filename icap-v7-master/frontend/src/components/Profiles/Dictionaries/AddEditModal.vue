<template>
  <b-modal
    v-model="isVisible"
    :title="isEdit ? 'Edit Entry' : 'Add New Entry'"
    :ok-title="isEdit ? 'Save' : 'Add'"
    cancel-title="Cancel"
    @ok="handleSubmit"
    @hidden="handleHidden"
  >
    <b-form>
      <b-form-group
        v-for="field in fields"
        :key="field.key"
        :label="field.label"
      >
        <b-form-input
          v-model="formData[field.key]"
          :placeholder="`Enter ${field.label}`"
        />
      </b-form-group>
    </b-form>
  </b-modal>
</template>

<script>
import {
  BModal,
  BForm,
  BFormGroup,
  BFormInput,
} from 'bootstrap-vue'

export default {
  name: 'AddEditModal',
  components: {
    BModal,
    BForm,
    BFormGroup,
    BFormInput,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    isEdit: {
      type: Boolean,
      default: false,
    },
    item: {
      type: Object,
      default: () => ({}),
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      formData: {},
    }
  },
  computed: {
    isVisible: {
      get() {
        return this.visible
      },
      set(val) {
        if (!val) {
          this.$emit('close')
        }
      },
    },
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadFormData()
      }
    },
    item: {
      handler() {
        if (this.visible) {
          this.loadFormData()
        }
      },
      deep: true,
    },
  },
  methods: {
    loadFormData() {
      if (this.isEdit && this.item) {
        this.formData = { ...this.item }
      } else {
        this.formData = {}
      }
    },
    handleSubmit() {
      this.$emit('submit', this.formData)
    },
    handleHidden() {
      this.formData = {}
      this.$emit('close')
    },
  },
}
</script>
