<template>
  <div>
    <div class="d-flex justify-content-between">
      <div style="max-width: 70%;">
        <h2 class="process-title-overflow">
        {{ selecedProcessName ? `${selecedProcessName} Configuration` : 'Process Configuration' }}
      </h2>
      </div>
      <div style="max-width: 29%;">
        <h2
        v-if="processId"
        class="text-nowrap mb-0"
      >
        Process Id: {{ processId }}
      </h2>
      </div>
    </div>
    <div>
      <profile-form
      :key="profileId"
      :profile-id="profileId"
    />
    </div>
  </div>
</template>

<script>
import ProfileForm from '@/components/Profiles/ProfileFormV7.vue'

export default {
  components: {
    ProfileForm,
  },
  computed: {
    selecedProcessName() {
      return this.$store.getters['profile/selecedProcessName']
    },
    profileId() {
      return this.$route.params.id
    },
    pageTitle() {
      return this.$route.meta.title
    },
    processId() {
      return this.$store.getters['profile/processId']
    },
  },
}
</script>
<style scoped>
.process-title-overflow {
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
}
</style>
