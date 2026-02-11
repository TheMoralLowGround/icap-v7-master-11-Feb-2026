<template>
  <!-- Wrapper for the authentication page -->
  <div class="auth-wrapper auth-v2">
    <b-row class="auth-inner m-0">

      <!-- Logo section -->
      <b-link class="brand-logo">
        <logo />
      </b-link>

      <!-- Left section: Image for larger screens -->
      <b-col
        lg="8"
        class="d-none d-lg-flex align-items-center p-5"
      >
        <div class="w-100 d-lg-flex align-items-center justify-content-center px-5">
          <b-img
            fluid
            :src="imgUrl"
            alt="Login V2"
          />
        </div>
      </b-col>

      <!-- Right section: Login form -->
      <b-col
        lg="4"
        class="d-flex align-items-center auth-bg px-2 p-lg-5"
      >
        <b-col
          sm="8"
          md="6"
          lg="12"
          class="px-xl-2 mx-auto"
        >
          <!-- Welcome message with dynamic application title -->
          <b-card-title
            class="mb-1 font-weight-bold"
            title-tag="h2"
          >
            Welcome to {{ appTitle }}
          </b-card-title>

          <!-- Error alert, visible if there is an error message -->
          <b-alert
            variant="danger"
            :show="errorMessage ? true : false"
          >
            <div class="alert-body">
              <p>
                {{ errorMessage }}
              </p>
            </div>
          </b-alert>

          <!-- Form validation observer to handle form validation -->
          <validation-observer
            ref="loginForm"
            #default="{ validated, invalid }"
          >
            <!-- Login form -->
            <b-form
              class="auth-login-form mt-2"
              @submit.prevent="login"
            >

              <!-- Username field -->
              <b-form-group
                label="Username"
                label-for="login-username"
              >
                <validation-provider
                  #default="{ errors }"
                  name="Username"
                  vid="username"
                  rules="required"
                  mode="eager"
                >
                  <b-form-input
                    id="login-username"
                    v-model="username"
                    :state="errors.length > 0 ? false:null"
                    name="username"
                    placeholder="Username"
                    autocomplete="off"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </validation-provider>
              </b-form-group>

              <!-- Password field -->
              <b-form-group>
                <div class="d-flex justify-content-between">
                  <label for="login-password">Password</label>
                </div>
                <validation-provider
                  #default="{ errors }"
                  name="Password"
                  vid="password"
                  rules="required"
                  mode="eager"
                >
                  <b-input-group
                    class="input-group-merge"
                    :class="errors.length > 0 ? 'is-invalid':null"
                  >
                    <b-form-input
                      id="login-password"
                      v-model="password"
                      :state="errors.length > 0 ? false:null"
                      class="form-control-merge"
                      :type="passwordFieldType"
                      name="login-password"
                      placeholder="Password"
                      autocomplete="off"
                    />
                    <b-input-group-append is-text>
                      <feather-icon
                        class="cursor-pointer"
                        :icon="passwordToggleIcon"
                        @click="togglePasswordVisibility"
                      />
                    </b-input-group-append>
                  </b-input-group>
                  <small class="text-danger">{{ errors[0] }}</small>
                </validation-provider>
              </b-form-group>

              <!-- Submit button -->
              <b-button
                type="submit"
                variant="primary"
                block
                :disabled="loading || (validated && invalid)"
              >
                Sign in <b-spinner
                  v-if="loading"
                  small
                />
              </b-button>
            </b-form>
          </validation-observer>

        </b-col>
      </b-col>
    </b-row>
  </div>
</template>

<script>
/* eslint-disable global-require */
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import {
  BRow, BCol, BLink, BFormGroup, BFormInput, BInputGroupAppend, BInputGroup, BCardTitle, BImg, BForm, BButton, BAlert, VBTooltip, BSpinner,
} from 'bootstrap-vue'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'
import { togglePasswordVisibility } from '@core/mixins/ui/forms'
import store from '@/store/index'
import Logo from '@/layouts/components/Logo.vue'

import axios from 'axios'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BRow,
    BCol,
    BLink,
    BFormGroup,
    BFormInput,
    BInputGroupAppend,
    BInputGroup,
    BCardTitle,
    BImg,
    BForm,
    BButton,
    BAlert,
    BSpinner,
    ValidationProvider,
    ValidationObserver,
    Logo,
  },
  mixins: [togglePasswordVisibility], // Mixin to handle password visibility toggle functionality
  data() {
    return {
      username: '', // Stores the username entered by the user
      password: '', // Stores the password entered by the user
      sideImg: require('@/assets/images/pages/login-v2.svg'), // Default image for the side panel
      loading: false, // Tracks the loading state during login
      errorMessage: null, // Stores error messages to display to the user
    }
  },
  computed: {
    // Dynamically fetches the application title from Vuex store
    appTitle() {
      return this.$store.getters['theme/settings'].appTitle
    },
    // Computes the appropriate icon for the password toggle button based on the field type
    passwordToggleIcon() {
      return this.passwordFieldType === 'password' ? 'EyeIcon' : 'EyeOffIcon'
    },
    // Computes the URL of the side image, switching to a dark theme version if necessary
    imgUrl() {
      if (store.state.appConfig.layout.skin === 'dark') {
        // eslint-disable-next-line vue/no-side-effects-in-computed-properties
        this.sideImg = require('@/assets/images/pages/login-v2-dark.svg')
        return this.sideImg
      }
      return this.sideImg
    },
  },
  methods: {
    // Handles the login process
    login() {
      // Validates the login form before submitting
      this.$refs.loginForm.validate().then(success => {
        if (success) { // If validation passes
          this.loading = true // Set loading state to true
          this.errorMessage = null

          const loginData = {
            username: this.username, // Prepare the username for API submission
            password: this.password, // Prepare the password for API submission
          }

          // Send login request to the server
          axios.post('/access_control/login/', loginData)
            .then(async res => {
              const { data } = res

              // Save authentication data in the Vuex store
              await this.$store.dispatch('auth/setAuthData', data)

              // Handle the redirect with recursive decoding
              const getFinalRedirectPath = redirectParam => {
                try {
                  const decoded = decodeURIComponent(redirectParam)

                  // Check if there's another nested redirect
                  const redirectMatch = decoded.match(/redirect=(.*)/i)
                  if (redirectMatch && redirectMatch[1]) {
                    return getFinalRedirectPath(redirectMatch[1])
                  }

                  // Return the final path if no more redirect params
                  return decoded.startsWith('/') ? decoded : '/'
                } catch (e) {
                  // eslint-disable-next-line no-console
                  console.error('Error decoding redirect URL:', e)
                  return '/' // Fallback to home
                }
              }

              let redirectPath = '/'
              if (this.$route.query.redirect) {
                redirectPath = getFinalRedirectPath(this.$route.query.redirect)
              }

              // Ensure the path is local and safe
              if (!redirectPath.startsWith('/')) {
                redirectPath = '/'
              }

              // Use router.replace() to avoid history issues
              this.$router.replace(redirectPath).catch(() => {
                // Fallback if redirect fails
                this.$router.replace('/')
              })
              this.loading = false // Reset loading state
            })
            .catch(error => {
              // Handle login error and set appropriate error message
              const errors = error?.response?.data?.non_field_errors
              this.errorMessage = errors ? errors[0] : 'Something went wrong'
              this.loading = false // Reset loading state
            })
        }
      })
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/pages/page-auth.scss';
</style>
