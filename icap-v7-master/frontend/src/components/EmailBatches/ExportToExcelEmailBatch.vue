<template>
  <b-modal
    v-model="showModal"
    centered
    title="Export Transactions to Excel"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <b-card-text>
      <div class="d-flex justify-content-center">
        <b-form-group class="pt-1">
          <b-form-radio-group
            v-model="exportType"
            size="small"
            button-variant="outline-primary"
            :options="[
              { text: 'Export All', value: 'all' },
              {
                text: 'Export Selected',
                value: 'selected',
                disabled: ids.length === 0 // Disable when ids length is 0
              },
            ]"
            buttons
          />
        </b-form-group>
      </div>
      <div v-if="ids.length && exportType != 'all'">
        <div
          v-for="(id, index) of ids"
          :key="index"
          class="text-primary"
        >
          {{ id }}
        </div>
      </div>

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
        :disabled="downloading"
        @click="ok()"
      >
        Export
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
import axios from 'axios'
import {
  BModal, BCardText, BButton, BSpinner, BFormRadioGroup, BFormGroup,
} from 'bootstrap-vue'
import download from 'downloadjs'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
    BFormRadioGroup,
    BFormGroup,
  },
  props: {
    ids: {
      type: Array,
      required: true,
    },
    totalRecords: {
      type: Number,
      required: true,
    },
    page: {
      type: Number,
      required: true,
    },
    sortBy: {
      type: String,
      required: true,
    },
    sortDesc: {
      type: Boolean,
      required: true,
    },
    searchBy: {
      type: Object,
      required: true,
    },
    filterBy: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      showModal: true,
      downloading: false,
      exportType: 'all',
    }
  },
  computed: {
    userTimezone() {
      return Intl.DateTimeFormat().resolvedOptions().timeZone // Retrieves user's timezone
    },
  },
  methods: {
    async confirmHandler(event) {
      event.preventDefault()

      this.downloading = true

      let data = null
      let params = null
      if (this.ids.length && this.exportType === 'selected') {
        data = {
          ids: this.ids,
          export_type: this.exportType,
        }
        params = {
          user_timezone: this.userTimezone,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
        }
      } else {
        data = {
          ...this.filterBy,
        }
        params = {
          user_timezone: this.userTimezone,
          page_size: this.totalRecords,
          sort_by: this.sortBy,
          sort_desc: this.sortDesc,
          ...this.searchBy,
        }
      }

      try {
        const res = await axios.post('/email-batches/download_excel/', data, { params, responseType: 'blob' })

        const contentType = res.headers['content-type']

        const path = ['Excel_email_batch'].join('___')

        download(res.data, `${path}.xlsx`, contentType)

        this.errorMessage = null
        this.downloading = false
        this.showModal = false
        this.$emit('completed')
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
