<template>
  <b-modal
    v-model="showModal"
    size="lg "
    title="Filter Options"
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form-group
      label-for="select-projects"
      label-class="font-1rem"
    >
      <template #label>
        <div class="d-flex">
          <span class="mr-auto">Projects</span>
          <span
            v-if="projects.length && projects.length !== selectedProjects.length"
            class="text-primary hover"
            @click="selectAllProjects"
          >
            select all
          </span>
          <span
            v-if="selectedProjects.length"
            class="text-danger hover ml-1"
            @click="clearProjects"
          >
            clear
          </span>
        </div>
      </template>

      <v-select
        v-model="selectedProjects"
        transition=""
        multiple
        :options="projects"
        @input="onChangeSelectedProjects"
      />
    </b-form-group>
    <b-form-group
      label-for="countries"
      label-class="font-1rem"
    >
      <template #label>
        <div class="d-flex">
          <span class="mr-auto">Countries</span>
          <span
            v-if="countries.length && countries.length !== selectedCountries.length"
            class="text-primary hover"
            @click="selectedCountries = countries"
          >
            select all
          </span>
          <span
            v-if="selectedCountries.length"
            class="text-danger hover ml-1"
            @click="selectedCountries = []"
          >
            clear
          </span>
        </div>
      </template>
      <v-select
        v-model="selectedCountries"
        transition=""
        multiple
        :options="countries"
      />
    </b-form-group>
    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>

      <b-button
        variant="primary"
        type="submit"
        :disabled="submitting || !enableSubmit"
        @click="ok()"
      >
        Submit
        <b-spinner
          v-if="submitting"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BFormGroup, BButton, BSpinner, BModal,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

export default {
  components: {
    BFormGroup,
    BButton,
    BSpinner,
    BModal,
    vSelect,
  },
  data() {
    return {
      submitting: false,
      showModal: true,
      projects: [],
      countries: [],
      selectedProjects: [],
      selectedCountries: [],
    }
  },
  computed: {
    enableSubmit() {
      return this.selectedProjects.length && this.selectedCountries.length
    },
    projectCountries() {
      return this.$store.getters['auth/projectCountries']
    },
    selectedProjectCountries() {
      return this.$store.getters['auth/selectedProjectCountries']
    },
  },
  created() {
    this.setInternalState()
  },
  methods: {
    setInternalState() {
      const projects = []
      const countries = []
      const selectedProjects = []
      const selectedCountries = []

      this.selectedProjectCountries.forEach(item => {
        if (!selectedProjects.includes(item.project)) {
          selectedProjects.push(item.project)
        }

        selectedCountries.push({
          label: `${item.country} - ${item.countryCode}_${item.project}`,
          value: item,
        })
      })

      this.projectCountries.forEach(item => {
        if (!projects.includes(item.project)) {
          projects.push(item.project)
        }

        if (selectedProjects.includes(item.project)) {
          countries.push({
            label: `${item.country} - ${item.countryCode}_${item.project}`,
            value: item,
          })
        }
      })

      this.projects = projects
      this.countries = countries
      this.selectedProjects = selectedProjects
      this.selectedCountries = selectedCountries
    },
    onChangeSelectedProjects(projects) {
      const countries = []
      const selectedCountries = []

      this.projectCountries.forEach(item => {
        if (projects.includes(item.project)) {
          countries.push({
            label: `${item.country} - ${item.countryCode}_${item.project}`,
            value: item,
          })
        }
      })

      this.selectedCountries.forEach(item => {
        if (projects.includes(item.value.project)) {
          selectedCountries.push(item)
        }
      })

      this.countries = countries
      this.selectedCountries = selectedCountries
    },
    selectAllProjects() {
      const countries = []

      this.projectCountries.forEach(item => {
        countries.push({
          label: `${item.country} - ${item.countryCode}_${item.project}`,
          value: item,
        })
      })

      this.selectedProjects = this.projects
      this.countries = countries
    },
    clearProjects() {
      this.countries = []
      this.selectedProjects = []
      this.selectedCountries = []
    },
    onSubmit() {
      this.$store.dispatch('auth/setSelectedProjectCountries', this.selectedCountries.map(e => e.value))
    },
  },
}
</script>

<style scoped>
.hover {
  transition: opacity 0.5s ease;
  opacity: 1;
  cursor: pointer;
}

.hover:hover {
  opacity: 0.5;
}
</style>
