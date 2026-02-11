<template>
  <b-modal
    v-model="showModal"
    :title="`${projectId ? 'Update' : 'Create'} Project`"
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <div v-if="!loading">
      <validation-observer
        ref="projectForm"
      >
        <b-form @submit.prevent="onSubmit">
          <b-row>
            <b-col
              md="12"
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
                  label-cols-md="4"
                  :state="errors.length > 0 ? false:null"
                >
                  <b-form-input
                    id="project-name"
                    v-model="projectName"
                    placeholder="Project Name"
                    @input="errorMessage = null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </b-form-group>
              </validation-provider>
            </b-col>
          </b-row>
          <b-alert
            variant="danger"
            :show="errorMessage !== null ? true : false"
            class="my-1"
          >
            <div class="alert-body">
              <p>
                {{ errorMessage }}
              </p>
            </div>
          </b-alert>
        </b-form>
      </validation-observer>
    </div>
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        :variant="projectId && projectName === project.name ? 'outline-secondary' : 'primary'"
        type="submit"
        :disabled="submitting || loading"
        @click="ok()"
      >
        Create
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
    <div
      v-if="loading"
      class="text-center"
    >
      <b-spinner
        variant="primary"
      />
    </div>
  </b-modal>
</template>

<script>
import {
  BRow, BCol, BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormInput,
} from 'bootstrap-vue'
import axios from 'axios'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import bus from '@/bus'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    BRow,
    BCol,
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BAlert,
    ValidationProvider,
    ValidationObserver,
    BFormInput,
    BModal,
  },
  props: {
    project: {
      type: [Boolean, Object],
      required: false,
      default() {
        return null
      },
    },
  },
  data() {
    return {
      loading: false,
      submitting: false,
      errorMessage: null,
      showModal: true,
      projectId: null,
      projectName: null,
      // listedEmails: [],
    }
  },
  // created() {
  //   this.getExitingMailAdd()
  // },
  methods: {
    // async getExitingMailAdd() {
    //   const res = await axios.get('/pipeline/project_validation/')
    //   const resData = res.data
    //   this.listedEmails = resData.filter(value => value.name !== this.project?.name)
    // },
    onSubmit(event) {
      event.preventDefault()
      this.errorMessage = null
      this.submitting = true

      this.$refs.projectForm.validate().then(async success => {
        if (!success) {
          this.submitting = false

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

        const requestData = {
          name: this.projectName,
        }

        let message

        try {
          const response = await axios.post('/dashboard/admin/projects/', requestData)
          message = 'Project created successfully'

          this.$toast({
            component: ToastificationContent,
            props: {
              title: message,
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.submitting = false
          this.errorMessage = null
          this.showModal = false

          bus.$emit('onRefreshAuthData')
          setTimeout(() => {
            this.$router.push(`/project/${response.data.id}`)
          }, 100)
        } catch (error) {
          const serverErrors = error?.response?.data

          const errors = []

          if (serverErrors?.non_field_errors) {
            errors.push(...serverErrors.non_field_errors)
          }
          if (serverErrors?.name) {
            errors.push(...serverErrors.name)
          }

          this.errorMessage = errors.join(', ')

          this.submitting = false
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
