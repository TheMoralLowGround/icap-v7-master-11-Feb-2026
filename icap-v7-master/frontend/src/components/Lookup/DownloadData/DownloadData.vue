<template>
  <b-modal
    v-model="showModal"
    title="Download Data"
    @ok="onDownload"
    @hidden="$emit('modal-closed')"
  >
    <b-card-text>
      <b-form-group
        label="Table"
      >
        <v-select
          ref="vSelect"
          v-model="tableName"
          transition=""
          :clearable="false"
          :options="tableOptions"
          @open="scrollToSelected"
        />
      </b-form-group>

      <div class="my-1">
        Process: {{ profileName }}
      </div>

      <b-alert
        class="my-1"
        variant="danger"
        :show="errorMessage !== null ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ errorMessage }}
          </p>
        </div>
      </b-alert>
    </b-card-text>

    <template #modal-footer="{ ok, cancel }">
      <b-button
        variant="secondary"
        @click="cancel()"
      >
        Cancel
      </b-button>
      <b-button
        variant="primary"
        :disabled="downloading || !enableDownload"
        @click="ok()"
      >
        Download
        <b-spinner
          v-if="downloading"
          small
          label="Small Spinner"
        />
      </b-button>
    </template>
  </b-modal>
</template>

<script>
import {
  BButton, BModal, BSpinner, BCardText, BFormGroup, BAlert,
} from 'bootstrap-vue'
import axios from '@/rules-backend-axios'
import vSelect from 'vue-select'
import download from 'downloadjs'

export default {
  components: {
    BButton,
    BModal,
    BSpinner,
    BCardText,
    vSelect,
    BFormGroup,
    BAlert,
  },
  data() {
    return {
      showModal: true,
      downloading: false,
      tableName: null,
      errorMessage: null,
    }
  },
  computed: {
    enableDownload() {
      return this.tableName
    },
    tableOptions() {
      return this.$store.getters['lookup/tables']
    },
    selectedDefintionVersion() {
      return this.$store.getters['dataView/selectedDefinitionVersion']
    },
    profileName() {
      return this.$store.getters['dataView/selectedDefinition'].definition_id
    },
  },
  methods: {
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected() {
      this.$nextTick(() => {
        const dropdownMenuItems = this.$refs.vSelect.$refs.dropdownMenu
        const selectedIndex = this.tableOptions.indexOf(this.tableName)

        if (dropdownMenuItems && selectedIndex >= 0) {
          // Calculate scroll position by assuming each item has a uniform height
          const itemHeight = dropdownMenuItems.scrollHeight / this.tableOptions.length

          // Adjust scrollTop to bring selected item closer to the top
          const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
          dropdownMenuItems.scrollTop = scrollPosition
        }
      })
    },
    async onDownload(event) {
      event.preventDefault()

      this.downloading = true

      const params = {
        table_name: this.tableName,
        profile_name: this.profileName,
        definition_version: this.selectedDefintionVersion,
      }

      try {
        const res = await axios.get('/download_db_records/', { params, responseType: 'blob' })

        const contentType = res.headers['content-type']

        const path = [this.tableName, this.profileName, this.selectedDefintionVersion].join('___')

        download(res.data, `${path}.xlsx`, contentType)

        this.errorMessage = null
        this.downloading = false
      } catch (error) {
        // convert blob response to json
        let responseDataJSON = null
        if (error?.response?.data) {
          const responseData = await error?.response?.data.text()
          responseDataJSON = JSON.parse(responseData)
        }

        this.errorMessage = responseDataJSON?.detail || 'Error downloading requested data'
        this.downloading = false
      }
    },
  },
}
</script>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
