<template>
  <b-modal
    v-model="showModal"
    size="xl"
    title="Train Documents"
    centered
    @hidden="$emit('modal-closed')"
    @ok="onSubmit"
  >
    <b-form @submit.prevent="onSubmit">
      <div
        v-if="loading"
        class="text-center my-1"
      >
        <b-spinner
          variant="primary"
          label="Spinner"
        />
      </div>

      <b-alert
        variant="danger"
        :show="loadingError !== null ? true : false"
      >
        <div class="alert-body">
          <p>
            {{ loadingError }}
          </p>
        </div>
      </b-alert>

      <div v-if="!loading && !loadingError">
        <div class="mb-1">
          Process: {{ profile.name }}
        </div>

        <div class="mb-1">
          <div>Document Types to Train:</div>
          <div>
            <b-table-simple class="custom-table">
              <b-thead>
                <b-tr>
                  <b-th>Select</b-th>
                  <b-th>Document Type</b-th>
                  <b-th>Content Location</b-th>
                  <b-th>Name Matching</b-th>
                  <b-th>Category</b-th>
                  <b-th>Language</b-th>
                  <b-th>OCR Engine</b-th>
                  <b-th>Page Rotate</b-th>
                  <b-th>Barcode</b-th>
                </b-tr>
              </b-thead>
              <b-tbody>
                <b-tr
                  v-for="(document, index) of documents"
                  :key="index"
                >
                  <b-td>
                    <b-form-checkbox
                      v-model="selectedDocumentIds"
                      :value="document.id"
                    />
                  </b-td>
                  <b-td>{{ document.doc_type }}</b-td>
                  <b-td>{{ document.content_location }}</b-td>
                  <b-td>
                    {{ document.name_matching_option }} {{ document.name_matching_text }}
                  </b-td>
                  <b-td>{{ document.category }}</b-td>
                  <b-td>{{ document.language }}</b-td>
                  <b-td>{{ document.ocr_engine }}</b-td>
                  <b-td>
                    {{ document.page_rotate ? 'Yes': 'No' }}
                  </b-td>
                  <b-td>
                    {{ document.barcode ? 'Yes': 'No' }}
                  </b-td>
                </b-tr>
              </b-tbody>
            </b-table-simple>
          </div>
        </div>

        <b-row>
          <b-col cols="3">
            <b-form-group
              label="Upload Type"
              label-for="upload-type"
              label-class="font-1rem"
            >
              <v-select
                id="upload-type"
                v-model="uploadType"
                transition=""
                style="padding-top: .3rem;"
                :options="['pdf', 'email', 'excel document', 'word']"
                @input="uploadedFiles = null"
              />
            </b-form-group>
          </b-col>
            <b-col cols="9">
            <b-form-group
              :label="getUploadedType.message"
            >
              <b-form-file
                v-model="uploadedFiles"
                multiple
                :accept="getUploadedType.extension"
              />
            </b-form-group>
          </b-col>
        </b-row>
        <b-row>
          <b-col cols="6">
            <b-form-group
              label="Selection Type"
              label-class="font-1rem"
            >
              <b-form-radio-group
                v-model="customerType"
                :options="customerTypeOptions"
                button-variant="outline-primary"
                buttons
                size="sm"
              />
            </b-form-group>
             <b-form-group
              v-if="customerType === 'customer'"
              label="Select Customer"
              label-for="customer"
              label-class="font-1rem"
            >
              <v-select
                id="customer"
                v-model="customer"
                transition=""
                style="padding-top: .3rem;"
                :options="customerOptions"
              />
            </b-form-group>
            <b-form-group
              v-else
              label="Custom Data"
              label-for="customData"
              label-class="font-1rem"
            >
              <b-form-textarea
                id="customData"
                v-model="customData"
                placeholder="Enter custom data..."
                rows="2"
              />
            </b-form-group>
          </b-col>
        </b-row>
      </div>

      <b-alert
        :show="submitResult.display"
        :variant="submitResult.error ? 'danger': 'success'"
      >
        <div class="alert-body">
          <p>
            {{ submitResult.message }}
          </p>
          <p v-if="submitResult.createdBatches">
            Created Train Batch:
            <b-link
              :to="{ name: 'training' }"
              class="font-weight-bold d-inline text-nowrap batch-link"
              @click="clearSearchDataTrainPage"
            > {{ submitResult.createdBatches }}</b-link>
          </p>
        </div>
      </b-alert>
    </b-form>

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
  BFormGroup, BButton, BForm, BSpinner, BAlert, BModal, BFormFile, BFormCheckbox, BTableSimple, BThead, BTbody, BTr, BTh, BTd, BRow, BCol, BLink, BFormRadioGroup, BFormTextarea,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import axios from 'axios'

export default {
  components: {
    BFormGroup,
    BButton,
    BForm,
    BSpinner,
    BAlert,
    BModal,
    BFormFile,
    BFormCheckbox,
    BTableSimple,
    BThead,
    BTbody,
    BTr,
    BTh,
    BTd,
    BRow,
    BCol,
    BLink,
    BFormRadioGroup,
    BFormTextarea,
    vSelect,
  },
  props: {
    profileId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      profile: null,
      selectedDocumentIds: [],
      uploadType: 'email',
      customerType: 'customer',
      customerTypeOptions: [
        { text: 'Customer', value: 'customer' },
        { text: 'Custom', value: 'custom' },
      ],
      customer: '',
      customData: '',
      uploadedFiles: null,
      loading: true,
      loadingError: null,
      submitting: false,
      showModal: true,
      submitResult: {
        display: false,
        error: false,
        message: null,
        createdBatches: '',
      },
    }
  },
  computed: {
    enableSubmit() {
      return this.selectedDocumentIds.length > 0 && this.uploadedFiles?.length > 0
    },
    customerOptions() {
      const processCustomers = this.profile?.process_customers || []
      return processCustomers.map(c => c.name)
    },
    documents() {
      const allDocuments = this.profile?.documents || []
      const processingDocuments = allDocuments.filter(doc => doc?.category === 'Processing')
      const translatedDocuments = this.profile?.translated_documents || []

      // Create a Set of source doc_types that are already translated
      const translatedSourceDocTypes = new Set(
        translatedDocuments.map(td => td.doc_type),
      )

      // Filter out source documents that have been translated
      return processingDocuments.filter(doc => !translatedSourceDocTypes.has(doc.doc_type))
    },
    getUploadedType() {
      switch (this.uploadType) {
        case 'email':
          return {
            message: 'Email Files (.eml or .msg):',
            extension: '.eml,.msg',
          }
        case 'pdf':
          return {
            message: 'Pdf Files (.pdf):',
            extension: '.pdf',
          }
        case 'excel document':
          return {
            message: 'Excel Files (.xls or .xlsx):',
            extension: '.xls, .xlsx',
          }
        case 'word':
          return {
            message: 'Word Files (.doc or docx):',
            extension: '.doc, .docx',
          }
        default:
          return {
            message: '',
            extension: '',
          }
      }
    },
  },
  created() {
    this.fetchProfile()
  },
  methods: {
    fetchProfile() {
      this.loading = true
      axios.get(`/dashboard/profiles/${this.profileId}/`)
        .then(res => {
          this.profile = res.data
          this.loadingError = null
          this.loading = false
        }).catch(error => {
          this.loadingError = error?.response?.data?.detail || 'Error fetching process'
          this.loading = false
        })
    },
    onSubmit(event) {
      event.preventDefault()

      this.submitResult = {
        display: false,
        error: false,
        message: null,
        createdBatches: [],
      }

      this.submitting = true

      const formData = new FormData()

      // Get all document IDs including associated source documents
      const allDocumentIds = this.getAllAssociatedDocumentIds()

      formData.append('doc_ids', JSON.stringify(allDocumentIds))
      formData.append('upload_type', this.uploadType === 'excel document' ? 'excel' : this.uploadType)
      formData.append('customer', this.customer || '')
      formData.append('custom_data', this.customData || '')

      this.uploadedFiles.forEach(uploadedFile => {
        const fileType = `${this.uploadType === 'excel document' ? 'excel' : this.uploadType}_files`

        formData.append(fileType, uploadedFile)
      })

      axios.post('/pipeline/train_documents/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
        .then(res => {
          this.submitResult = {
            display: true,
            error: false,
            message: res.data.detail,
            createdBatches: res.data.train_batch_id,
          }
          this.$store.commit('classifications/SET_NEW_CREATED_TRAIN_ID', res.data.train_batch_id)
          this.submitting = false
        })
        .catch(error => {
          this.submitResult = {
            display: true,
            error: true,
            message: error?.response?.data?.detail || 'Error submitting training documents',
            createdBatches: error?.response?.data?.train_batch_id || '',
          }
          this.submitting = false
        })
    },
    clearSearchDataTrainPage() {
      localStorage.removeItem('train-batches-filter')
    },
    getAllAssociatedDocumentIds() {
      const allDocuments = this.profile?.documents || []
      const translatedDocuments = this.profile?.translated_documents || []
      if (!this.selectedDocumentIds?.length) return []

      // Build translated_doc_type → [original_doc_types]
      const translatedToOriginalsMap = new Map()
      translatedDocuments.forEach(td => {
        translatedToOriginalsMap.set(
          td.translated_doc_type,
          [...(translatedToOriginalsMap.get(td.translated_doc_type) || []), td.doc_type],
        )
      })

      // Build quick lookups
      const docTypeToIdMap = new Map()
      const idToDocMap = new Map()
      allDocuments.forEach(doc => {
        docTypeToIdMap.set(doc.doc_type, doc.id)
        idToDocMap.set(doc.id, doc)
      })

      const allIds = new Set()

      this.selectedDocumentIds.forEach(selectedId => {
        allIds.add(selectedId)

        const selectedDoc = idToDocMap.get(selectedId)
        if (!selectedDoc) return

        const originalDocTypes = translatedToOriginalsMap.get(selectedDoc.doc_type)
        if (!originalDocTypes) return

        originalDocTypes.forEach(type => {
          const originalId = docTypeToIdMap.get(type)
          if (originalId) allIds.add(originalId)
        })
      })

      return Array.from(allIds)
    },
  },
}
</script>
