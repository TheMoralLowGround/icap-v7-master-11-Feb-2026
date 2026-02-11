<template>
  <div>
    <h2
      class="text-center mb-2"
    >{{ pageTitle }}
    </h2>
    <CreateTemplate
      :key="templateId"
      :template-id="templateId"
    />
  </div>
</template>

<script>
import CreateTemplate from '@/components/Template/CreateTemplate.vue'

export default {
  components: {
    CreateTemplate,
  },
  computed: {
    templateId() {
      return this.$route.params.id
    },
    pageTitle() {
      return this.$route.meta.title
    },
  },
}
</script>
