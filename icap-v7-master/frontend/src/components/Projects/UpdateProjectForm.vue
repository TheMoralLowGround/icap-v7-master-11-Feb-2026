<template>

  <div class="update-project-form">

    <div v-if="!loading">
      <validation-observer
        ref="projectForm"
      >
        <b-form @submit.prevent="onSubmit">
          <b-row>
            <b-col
              md="8"
              offset-md="2"
            >
              <validation-provider
                #default="{ errors }"
                name="Project Name"
                vid="projectName"
                mode="eager"
                rules="required"
              >
                <b-form-group
                  label="Project Name"
                  label-for="project-name"
                  label-cols-md="3"
                  :state="errors.length > 0 ? false : null"
                >
                  <b-form-input
                    id="project-name"
                    v-model="projectName"
                    placeholder="Enter project name"
                    :state="errors.length > 0 ? false : null"
                    @input="onFieldChange"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>

              <b-alert
                variant="danger"
                :show="errorMessage !== null"
                class="my-3"
              >
                <div class="alert-body">
                  <p class="mb-0">
                    {{ errorMessage }}
                  </p>
                </div>
              </b-alert>

              <b-alert
                variant="success"
                :show="successMessage !== null"
                class="my-3"
              >
                <div class="alert-body">
                  <p class="mb-0">
                    {{ successMessage }}
                  </p>
                </div>
              </b-alert>
            </b-col>
          </b-row>
          <b-row>
            <b-col
              md="8"
              offset-md="2"
            >
              <b-form-group
                label="Project Id"
                label-for="project-id"
                label-cols-md="3"
              >
                <b-form-input
                  id="project-id"
                  v-model="uniqueProjectId"
                  placeholder="Project Id"
                  disabled
                />
              </b-form-group>
            </b-col>
          </b-row>
        </b-form>
      </validation-observer>
    </div>

    <div
      v-else
      class="text-center py-5"
    >
      <b-spinner
        variant="primary"
        label="Loading..."
      />
      <p class="mt-2 text-muted">
        Loading project details...
      </p>
    </div>
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BRow,
  BCol,
  BFormGroup,
  BForm,
  BSpinner,
  BAlert,
  BFormInput,
} from 'bootstrap-vue'
import axios from 'axios'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  name: 'UpdateProjectForm',
  components: {
    BRow,
    BCol,
    BFormGroup,
    BForm,
    BSpinner,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    BFormInput,
  },
  props: {
    project: {
      type: Object,
      required: true,
      default: () => ({}),
    },
  },
  data() {
    return {
      loading: false,
      submitting: false,
      errorMessage: null,
      successMessage: null,
      projectId: null,
      projectName: '',
      uniqueProjectId: '',
      originalProjectName: '',
      originalEmailBox: '',
    }
  },
  computed: {
    hasChanges() {
      return this.projectName !== this.originalProjectName
    },
    canSubmit() {
      const hasRequiredFields = this.projectName && this.projectName.trim()

      return hasRequiredFields && this.hasChanges && !this.submitting
    },
  },
  watch: {
    project: {
      handler(newProject) {
        if (newProject && newProject.id) {
          this.initializeFormData()
          this.loading = false
        }
      },
      immediate: true,
    },
    hasChanges: {
      handler(newValue) {
        this.$emit('form-state-changed', {
          hasChanges: newValue,
          canSubmit: this.canSubmit,
          submitting: this.submitting,
        })
      },
      immediate: true,
    },
    canSubmit: {
      handler(newValue) {
        this.$emit('form-state-changed', {
          hasChanges: this.hasChanges,
          canSubmit: newValue,
          submitting: this.submitting,
        })
      },
      immediate: true,
    },
    submitting: {
      handler(newValue) {
        this.$emit('form-state-changed', {
          hasChanges: this.hasChanges,
          canSubmit: this.canSubmit,
          submitting: newValue,
        })
      },
      immediate: true,
    },
  },
  created() {
    bus.$on('project:update-project', this.onSubmit)
    this.loading = false
  },

  beforeDestroy() {
    bus.$off('project:update-project', this.onSubmit)
  },
  methods: {
    initializeFormData() {
      if (this.project && this.project.id) {
        this.projectId = this.project.id
        this.projectName = this.project.name || ''
        this.uniqueProjectId = this.project.project_id || ''
        this.originalProjectName = this.project.name || ''
      }
    },

    onFieldChange() {
      this.errorMessage = null
      this.successMessage = null
    },

    async onSubmit(event) {
      if (event) {
        event.preventDefault()
      }

      this.errorMessage = null
      this.successMessage = null

      try {
        const success = await this.$refs.projectForm.validate()

        if (!success) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Please correct the form errors',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
          return
        }

        this.submitting = true

        const requestData = {
          name: this.projectName,
        }

        await axios.patch(`/dashboard/admin/projects/${this.projectId}/`, requestData)

        this.originalProjectName = this.projectName

        this.$emit('project-updated', {
          ...this.project,
          name: this.projectName,
        })

        this.successMessage = 'Project updated successfully!'

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Project Updated',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })

        setTimeout(() => {
          this.successMessage = null
        }, 3000)
      } catch (error) {
        const serverErrors = error?.response?.data

        if (serverErrors && serverErrors.non_field_errors) {
          [this.errorMessage] = serverErrors.non_field_errors
        } else {
          this.errorMessage = 'Something went wrong. Please try again.'
        }

        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Update Failed',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.update-project-form {
  .form-group {
    margin-bottom: 1.5rem;
  }

  .btn {
    min-width: 120px;
  }
}
</style>
