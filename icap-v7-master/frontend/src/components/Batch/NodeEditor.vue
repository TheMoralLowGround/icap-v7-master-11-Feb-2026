<template>
  <!-- Dynamic width for the container div -->
  <div :style="{ width: `${width}%` }">
    <!-- Input group displayed only when there is an editableNode with a defined value (v) -->
    <b-input-group v-if="editableNode && editableNode.v">
      <!-- Input field for editing node value, bound to nodeValue -->
      <b-form-input
        ref="nodeEditorInput"
        v-model="nodeValue"
        :placeholder="editableNode.v"
        autofocus
      />

      <!-- Append group with action buttons -->
      <b-input-group-append class="cursor-pointer">
        <!-- Save button: Visible only when the node value has changed -->
        <b-input-group-text
          v-if="editableNode.v !== nodeValue"
          style="margin-right: 1px"
          @click="save"
        >
          <!-- Check icon for saving changes -->
          <feather-icon
            icon="CheckIcon"
            size="12"
          />
        </b-input-group-text>

        <!-- Cancel button: Closes the editor without saving -->
        <b-input-group-text
          @click="close"
        >
          <!-- Cross icon for canceling -->
          <feather-icon
            icon="XIcon"
            size="12"
          />
        </b-input-group-text>
      </b-input-group-append>
    </b-input-group>
  </div>
</template>

<script>
import {
  BInputGroup, BInputGroupAppend, BInputGroupText, BFormInput,
} from 'bootstrap-vue'

export default {
  components: {
    BInputGroup, // Input group wrapper
    BInputGroupAppend, // Append area for action buttons
    BInputGroupText, // Text area for buttons or labels
    BFormInput, // Input field for editing
  },
  props: {
    width: {
      required: false, // The width prop is optional
      type: String, // Must be a string
      default() {
        return '100' // Default width is 100%
      },
    },
  },
  data() {
    return {
      nodeValue: '', // Local state for the editable node's value
    }
  },
  computed: {
    // Retrieves the currently editable node from the Vuex store
    editableNode() {
      return this.$store.getters['batch/editableNode']
    },
  },
  watch: {
    // Watcher to update the local nodeValue whenever the editableNode changes
    editableNode() {
      this.nodeValue = this.editableNode?.v || ''

      // Auto-focus the input field when editableNode changes
      if (this.$refs.nodeEditorInput) {
        this.$refs.nodeEditorInput.focus()
      }
    },
  },
  created() {
    // Initialize nodeValue when the component is created
    this.nodeValue = this.editableNode?.v || ''
  },
  methods: {
    // Save the updated node value
    async save() {
      const data = {
        id: this.editableNode.id, // Node ID for the update
        nodeValue: this.nodeValue, // Updated value
      }

      // Dispatch actions to update the node value and set the editableNode in the store
      await this.$store.dispatch('batch/updateNodeValue', data)
      await this.$store.dispatch('batch/setEditableNode', { ...this.editableNode, v: this.nodeValue })

      // Close the editor after saving
      this.close()
    },
    // Close the editor and reset the editableNode in the store
    close() {
      this.$store.dispatch('batch/setEditableNode', null)
    },
  },
}
</script>
