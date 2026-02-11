<template>
  <BModal
    :visible="value"
    :title="`Edit ${agent.title || 'Agent'}`"
    size="md"
    centered
    no-close-on-backdrop
    ok-title="Save"
    @ok="handleSave"
    @hidden="close"
  >
    <BForm @submit.prevent="handleSave">
      <BFormGroup
        label="Title"
        label-for="agent-title"
      >
        <BFormInput
          id="agent-title"
          v-model="editingAgent.title"
          type="text"
          placeholder="Enter agent title"
          required
        />
      </BFormGroup>

      <BFormGroup
        label="Type"
        label-for="agent-type"
      >
        <BFormInput
          id="agent-type"
          v-model="editingAgent.type"
          type="text"
          placeholder="Enter agent type"
          required
        />
      </BFormGroup>

      <BFormGroup
        label="Description"
        label-for="agent-description"
      >
        <BFormTextarea
          id="agent-description"
          v-model="editingAgent.description"
          placeholder="Enter agent description"
          rows="3"
          required
        />
      </BFormGroup>
    </BForm>
  </BModal>
</template>

<script>
import {
  BModal,
  BForm,
  BFormGroup,
  BFormInput,
  BFormTextarea,
} from 'bootstrap-vue'

export default {
  name: 'AgentSettingsDialog',
  components: {
    BModal,
    BForm,
    BFormGroup,
    BFormInput,
    BFormTextarea,
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    agent: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      editingAgent: {},
    }
  },
  watch: {
    agent: {
      handler(newAgent) {
        if (newAgent && Object.keys(newAgent).length > 0) {
          this.editingAgent = { ...newAgent }
        }
      },
      deep: true,
      immediate: true,
    },
    value(newVal) {
      if (newVal && this.agent) {
        this.editingAgent = { ...this.agent }
      }
    },
  },
  methods: {
    handleSave() {
      // Validate required fields
      if (!this.editingAgent.title || !this.editingAgent.type || !this.editingAgent.description) {
        return
      }

      // Emit save event with the edited agent data
      this.$emit('save', { ...this.editingAgent })
    },
    close() {
      // Reset editing data
      this.editingAgent = {}
      // Emit input event to close the dialog (v-model support)
      this.$emit('input', false)
      // Emit cancel event
      this.$emit('cancel')
    },
  },
}
</script>
