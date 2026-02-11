<template>
  <span
    :class="[
      'chip',
      `text-${variant}`,
      `border-${variant}`,
      status === 'classification review' ? 'chip-hover' : '',
      status === 'classification error' ? 'error-chip' : ''
    ]"
  >
    <slot />
  </span>
</template>

<script>
export default {
  props: {
    variant: {
      type: String,
      required: true,
    },
    status: {
      type: String,
      required: false,
      default: '',
    },
  },
}
</script>

<style scoped>
.chip {
  text-transform: capitalize;
  border: thin solid grey;
  border-radius: 9999px;
  padding: 0px 10px;
  font-size: .8575rem;
  display: inline-block;
  vertical-align: middle;
  line-height: 22px;
  font-weight: 600;
  transition: background-color 0.3s, color 0.3s;
}

.chip-hover:hover {
  background-color: #e0a800;
  color: white !important;
}

.error-chip:hover {
  background-color: #ea5455;
  color: white !important;
}
</style>
