<template>
  <div>
    <b-alert
      v-for="(message, messageIndex) of messages"
      :key="messageIndex"
      class="my-1"
      :variant="message.success ? 'primary': 'danger'"
      show
    >
      <div class="alert-body">
        <p>
          <span v-if="message.definition_version">
            {{ message.definition_version }}:
          </span>
          {{ message.success ? 'Completed' : message.error_message }}
        </p>
      </div>
    </b-alert>
  </div>
</template>

<script>
import { BAlert } from 'bootstrap-vue'

export default {
  components: {
    BAlert,
  },
  props: {
    messages: {
      type: Array,
      required: true,
    },
  },
}
</script>
