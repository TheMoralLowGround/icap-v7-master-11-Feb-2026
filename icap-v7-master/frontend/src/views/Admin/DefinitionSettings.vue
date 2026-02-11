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
          <h2>Definition Settings</h2>
        </div>
      </b-col>

      <b-col
        cols="12"
        md="6"
        class="d-flex align-items-center justify-content-end mb-1 mb-md-0"
      >
        <div
          v-if="project"
          class="project-selector-wrapper"
        >
          <project-selector
            v-model="project"
            :project-options="projectOptions"
          />
        </div>

        <b-button
          v-if="project"
          variant="primary"
          class="ml-1"
          @click="importDefinitionSettings = true"
        >
          Import
        </b-button>

        <b-button
          v-if="project"
          variant="outline-primary"
          class="ml-1"
          @click="exportDefinitionSettings"
        >
          Export
          <b-spinner
            v-if="exportingDefinitionSettings"
            small
            label="Small Spinner"
          />
        </b-button>
      </b-col>
    </b-row>

    <div
      v-if="loading"
      class="text-center"
    >
      <b-spinner
        variant="primary"
      />
    </div>

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

    <div v-if="project && !loading && !loadingError">
      <options />
      <key-qualifiers />
      <compound-keys />
    </div>

    <import-json
      v-if="importDefinitionSettings"
      title="Definition Settings"
      url="/import_definition_settings/"
      field="definition_settings"
      :project="project"
      @modal-closed="importDefinitionSettings = false"
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
import ProjectSelector from '@/components/Admin/DefinitionSettings/ProjectSelector.vue'
import ImportJson from '@/components/UI/ImportJson.vue'
import Options from '@/components/Admin/DefinitionSettings/Options/Options.vue'
import KeyQualifiers from '@/components/Admin/DefinitionSettings/KeyQualifiers/KeyQualifiers.vue'
import CompoundKeys from '@/components/Admin/DefinitionSettings/CompoundKeys/CompoundKeys.vue'

export default {
  components: {
    ProjectSelector,
    ImportJson,
    Options,
    BSpinner,
    BAlert,
    BButton,
    BRow,
    BCol,
    KeyQualifiers,
    CompoundKeys,
  },
  data() {
    return {
      loading: false,
      loadingError: null,
      exportingDefinitionSettings: false,
      importDefinitionSettings: false,
    }
  },
  computed: {
    projectOptions() {
      return this.$store.getters['definitionSettings/projectOptions']
    },
    project: {
      get() {
        return this.$store.getters['definitionSettings/project']
      },
      set(value) {
        this.$store.commit('definitionSettings/SET_PROJECT', value)
      },
    },
  },
  watch: {
    project(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.fetchData()
      }
    },
  },
  created() {
    this.fetchProjectList()
  },
  destroyed() {
    this.$store.dispatch('definitionSettings/reset')
  },
  methods: {
    async fetchProjectList() {
      this.loading = true

      try {
        const res = await axios.get('/dashboard/admin/projects/', {
          params: {
            no_pagination: true,
            sort_by: 'name',
          },
        })

        const projectOptions = res.data.map(e => e.name)

        this.$store.commit('definitionSettings/SET_PROJECT_OPTIONS', projectOptions)

        this.$store.commit('definitionSettings/SET_PROJECT', projectOptions[0] || null)

        if (!projectOptions.length) {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'No projects were found!',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        }

        this.loading = false
        this.loadingError = null
      } catch (error) {
        this.loading = false
        this.loadingError = error?.response?.data?.detail || 'Error fetching projects!'
      }
    },
    async fetchData() {
      this.loading = true

      try {
        if (!this.projectOptions.length) {
          await this.fetchProjectList()
        }

        await this.$store.dispatch('definitionSettings/fetchData')

        this.loading = false
        this.loadingError = null
      } catch (error) {
        this.loading = false
        this.loadingError = error?.response?.data?.detail || 'Error fetching definition settings!'
      }
    },
    exportDefinitionSettings() {
      this.exportingDefinitionSettings = true

      this.exportProjects(this.selectedRecords, `Definition_Settings_${this.project}`)
        .then(() => {
          this.exportingDefinitionSettings = false
        })
    },
    exportProjects(ids, fileName) {
      const params = {
        project: this.project,
      }

      return axios.get('/get_definition_settings/', { params })
        .then(res => {
          exportFromJSON({
            data: res.data, fileName, exportType: 'json',
          })
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Error exporting Definition Settings',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })
        })
    },
  },
}
</script>

<style scoped>
.wrapper {
    column-gap: 1rem;
}
.project-selector-wrapper {
  flex-basis: 300px;
}
</style>
