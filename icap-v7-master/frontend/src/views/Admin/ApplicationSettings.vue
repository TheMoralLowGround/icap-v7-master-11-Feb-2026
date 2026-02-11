<template>
  <div>
    <!-- Header -->
    <b-row class="mb-1">
      <b-col
        cols="12"
        md="6"
        class="d-flex align-items-center justify-content-start mb-1 mb-md-0"
      >
        <div class="mr-auto">
          <h2>Application Settings</h2>
        </div>
      </b-col>

      <b-col
        cols="12"
        md="6"
        class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
      >
        <b-button
          variant="primary"
          class="ml-1"
          @click="importApplicationSettings = true"
        >
          Import
        </b-button>

        <b-button
          variant="outline-primary"
          class="ml-1"
          @click="exportApplicationSettings"
        >
          Export
          <b-spinner
            v-if="exportingApplicationSettings"
            small
            label="Small Spinner"
          />
        </b-button>
      </b-col>
    </b-row>

    <b-alert
      variant="danger"
      :show="!loading && loadingError ? true : false"
    >
      <div class="alert-body">
        <p>
          {{ loadingError }}
        </p>
      </div>
    </b-alert>

    <div v-if="!loading && !loadingError">
      <options />
    </div>

    <import-json
      v-if="importApplicationSettings"
      title="Application Settings"
      url="/import_application_settings/"
      field="application_settings"
      @modal-closed="importApplicationSettings = false"
      @imported="fetchData"
    />
  </div>
</template>

<script>
import axios from 'axios'
import exportFromJSON from 'export-from-json'
import {
  BSpinner, BAlert, BButton, BRow, BCol,
} from 'bootstrap-vue'

import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import ImportJson from '@/components/UI/ImportJson.vue'
import Options from '@/components/Admin/ApplicationSettings/Options/Options.vue'

export default {
  components: {
    BSpinner,
    BAlert,
    BButton,
    BRow,
    BCol,
    ImportJson,
    Options,
  },
  data() {
    return {
      loading: false,
      loadingError: null,
      importApplicationSettings: false,
      exportingApplicationSettings: false,
    }
  },
  created() {
    this.fetchData()
  },
  destroyed() {
    this.$store.dispatch('applicationSettings/reset')
  },
  methods: {
    fetchData() {
      this.loading = true
      this.$store.dispatch('applicationSettings/fetchData').then(() => {
        this.loading = false
        this.loadingError = null
      })
        .catch(error => {
          this.loading = false
          this.loadingError = error?.response?.data?.detail || 'Error fetching application settings!'
        })
    },
    exportApplicationSettings() {
      this.exportingApplicationSettings = true

      this.exportProjects(this.selectedRecords, 'Application_Settings')
        .then(() => {
          this.exportingApplicationSettings = false
        })
    },
    exportProjects(ids, fileName) {
      return axios.get('/application-settings/')
        .then(res => {
          exportFromJSON({
            data: res.data?.data, fileName, exportType: 'json',
          })
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting Application Settings',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
    },
  },
}
</script>
