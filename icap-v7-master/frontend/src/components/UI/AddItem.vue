<template>
  <b-form @submit.prevent="submit">
    <b-input-group>
      <b-input-group-prepend>
        <b-button
          :style="{
            'border-top-right-radius': noInputBox ? '0.358rem' : 0,
            'border-bottom-right-radius': noInputBox ? '0.358rem' : 0,
          }"
          :variant="buttonVariant"
          @click="submit"
        >
          <feather-icon
            icon="PlusIcon"
            class="mr-25"
          />
          <span>{{ addCount > 1 ? `${addCount} ${actualPluralLabel}` : label }}</span>
        </b-button>
      </b-input-group-prepend>
      <b-form-input
        v-if="!noInputBox"
        v-model.number="addCount"
        type="number"
        placeholder="1"
      />
    </b-input-group>
  </b-form>
</template>

<script>
import {
  BInputGroup, BInputGroupPrepend, BButton, BFormInput, BForm,
} from 'bootstrap-vue'

export default {
  components: {
    BInputGroup,
    BInputGroupPrepend,
    BButton,
    BFormInput,
    BForm,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    pluralLabel: {
      type: String,
      requird: false,
      default: null,
    },
    noInputBox: {
      type: Boolean,
      requird: false,
      default: false,
    },
    buttonVariant: {
      type: String,
      required: false,
      default() {
        return 'primary'
      },
    },
  },
  data() {
    return {
      addCount: '',
    }
  },
  computed: {
    actualPluralLabel() {
      return this.pluralLabel ? this.pluralLabel : `${this.label}s`
    },
  },
  methods: {
    submit() {
      const count = this.addCount > 1 ? this.addCount : 1
      this.$emit('add', count)
      this.addCount = ''
    },
  },
}
</script>

<style scoped>
.btn {
  padding: 0.75rem !important;
  font-size: 12px;
}
</style>
