<template>
  <div>
    <div class="d-flex justify-content-between align-items-center">
      <h2>Documents</h2>

      <div class="d-flex justify-content-between align-items-center">
        <b-button
          variant="outline-primary"
          @click="openDialog"
        >
          Add Document Types
        </b-button>
         <export-profile-documents-to-excel
          :documents="searchableItems"
          class="ml-1"
        />
        <b-button
          variant="outline-primary"
          class="ml-1"
          @click="importDialog = true"
        >
          Import
        </b-button>
        <b-button
          variant="primary"
          class="ml-1"
          @click="TranslateDialog = true"
        >
          Translate Document
        </b-button>
        <b-button
        variant="success"
        :disabled="submitting"
        @click="$emit('submit')"
        class="ml-1"
      >
        <b-spinner
          v-if="submitting"
          small
          class="mr-50"
        />
        Save
      </b-button>
      </div>
    </div>

    <b-card>
      <b-table-simple
        responsive
        striped
        :busy="loading"
        :class="{ 'table-busy': loading }"
      >
        <colgroup>
          <col
            v-for="field in computedFields"
            :key="field.key"
            :style="{ width: field.width }"
          >
        </colgroup>

        <b-thead>
          <b-tr>
            <template v-for="field in computedFields">
              <b-th
                v-if="field.key !== 'select' && field.sortable"
                :key="field.key"
                :aria-sort="sortField === field.key ? sortDesc ? 'descending' : 'ascending' : 'none'"
                @click="toggleSort(field)"
              >
                {{ field.label }}
              </b-th>

              <b-th
                v-if="field.key !== 'select' && !field.sortable"
                :key="field.key"
              >
                {{ field.label }}
              </b-th>
            </template>
          </b-tr>
          <b-tr>
            <template
              v-for="field of computedFields"
            >
              <b-th :key="`header-${field.key}`">
                <div
                  v-if="field.searchable"
                  class="d-flex flex-column"
                >
                  <b-form-input
                    v-model="searchFields[field.key]"
                    :placeholder="`Search ${field.label}`"
                    trim
                    :disabled="loading"
                  />
                </div>
              </b-th>
            </template>
          </b-tr>
        </b-thead>

        <b-tbody>
          <template v-if="loading">
            <b-tr>
              <b-td
                :colspan="computedFields.length"
                class="text-center text-primary my-2"
              >
                <b-spinner class="align-middle" />
                <strong>Loading...</strong>
              </b-td>
            </b-tr>
          </template>

          <template v-else>
            <b-tr
              v-for="(item, index) in renderedItems"
              :key="`row-${item.id || index}`"
              :class="{ 'has-error': hasRowErrors(item.id) }"
            >
              <template v-for="field in computedFields">
                <b-td :key="`cell-${field.key}-${index}`">
                  <template v-if="field.key === 'content_location'">
                    {{ item.content_location || '' }}
                    <b-form-invalid-feedback
                      v-if="getFieldError(item.id, 'content_location')"
                      :state="false"
                      class="d-block text-danger"
                    >
                      {{ getFieldError(item.id, 'content_location') }}
                    </b-form-invalid-feedback>
                  </template>

                  <template v-else-if="field.key === 'name_matching_option'">
                    {{ item.name_matching_option || '' }}
                    <b-form-invalid-feedback
                      v-if="getFieldError(item.id, 'name_matching_option')"
                      :state="false"
                      class="d-block text-danger"
                    >
                      {{ getFieldError(item.id, 'name_matching_option') }}
                    </b-form-invalid-feedback>
                  </template>

                  <template v-else-if="field.key === 'name_matching_text'">
                    {{ item.name_matching_text || '' }}
                    <b-form-invalid-feedback
                      v-if="getFieldError(item.id, 'name_matching_text')"
                      :state="false"
                      class="d-block text-danger"
                    >
                      {{ getFieldError(item.id, 'name_matching_text') }}
                    </b-form-invalid-feedback>
                  </template>

                  <template v-else-if="field.key === 'category'">
                    {{ item.category || '' }}
                  </template>

                  <template v-else-if="field.key === 'language'">
                    {{ item.language || '' }}
                  </template>

                  <template v-else-if="field.key === 'ocr_engine'">
                    {{ item.ocr_engine || '' }}
                  </template>

                  <template v-else-if="field.key === 'page_rotate'">
                    {{ item.page_rotate ? 'Yes' : 'No' }}
                  </template>

                  <template v-else-if="field.key === 'barcode'">
                    {{ item.barcode ? 'Yes' : 'No' }}
                  </template>

                  <template v-else-if="field.key === 'action'">
                    <div class="d-flex gap-3 justify-content-end">
                      <feather-icon
                        v-b-tooltip.hover
                        title="Edit Document"
                        icon="EditIcon"
                        class="cursor-pointer text-primary"
                        size="16"
                        @click="editItem(item)"
                      />
                      <feather-icon
                        v-b-tooltip.hover
                        title="Delete Document"
                        icon="Trash2Icon"
                        class="cursor-pointer text-danger"
                        size="16"
                        @click="deleteItem(item.id)"
                      />
                    </div>
                  </template>

                  <template v-else>
                    {{ item[field.key] || '' }}
                  </template>
                </b-td>
              </template>
            </b-tr>
          </template>
        </b-tbody>
      </b-table-simple>
      <div
        v-if="!loading && renderedItems.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>
      <!-- <div
        v-if="!loading"
        class="mx-2 mt-1 mb-2"
      >
        <detailed-pagination
          :per-page="perPage"
          :current-page="currentPage"
          :total-records="totalRecords"
          :local-records="renderedItems.length"
          @page-changed="pageChanged"
        />
      </div> -->
    </b-card>

    <documents-modal
      v-model="dialog"
      :options="options"
      :project="project"
      :document-types="documentTypes"
      :language-options="languageOptions"
      :template-names="templateNames"
      :selected-items="items.map(d => d.doc_type)"
      :editing-item="editingItem"
      :editing-id="editingId"
      @submit="handleSubmit"
      @close="closeDialog"
    />

    <translate-document-modal
      v-model="TranslateDialog"
      :items="renderedItems"
      @save="setInitialState"
      @close="TranslateDialog = false"
    />

    <import-profile-documents-from-excel
      :model-value="importDialog"
      :profile-id="profileId"
      @update:modelValue="importDialog = $event"
      @import-success="handleImportSuccess"
    />
  </div>
</template>

<script>
import { cloneDeep } from 'lodash'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'
// import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import {
  BCard,
  BButton,
  BTableSimple,
  BFormInput,
  VBTooltip,
  BSpinner,
  BTr,
  BTbody,
  BThead,
  BTh,
  BTd,
  BFormInvalidFeedback,
} from 'bootstrap-vue'
import DocumentsModal from './DocumentsModal.vue'
import TranslateDocumentModal from './TranslateDocumentModal.vue'
import ExportProfileDocumentsToExcel from './ExportProfileDocumentsToExcel.vue'
import ImportProfileDocumentsFromExcel from './ImportProfileDocumentsFromExcel.vue'

export default {
  directives: {
    'b-tooltip': VBTooltip,
  },
  components: {
    BTr,
    BThead,
    BTbody,
    BTh,
    BTd,
    BCard,
    BButton,
    BTableSimple,
    BFormInput,
    BSpinner,
    BFormInvalidFeedback,
    // DetailedPagination,
    DocumentsModal,
    TranslateDocumentModal,
    ExportProfileDocumentsToExcel,
    ImportProfileDocumentsFromExcel,
  },
  props: {
    project: {
      type: String,
      required: true,
    },
    profileId: {
      type: [String, Number],
      required: true,
    },
    documentErrors: {
      type: Object,
      default: () => ({}),
    },
    languageOptions: {
      type: Array,
      required: true,
      default: () => [],
    },
    submitting: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      form: {
        doc_types: [],
      },
      dialog: false,
      TranslateDialog: false,
      importDialog: false,
      loading: false,
      searchableItems: [],
      renderedItems: [],
      filteredItems: [],
      // currentPage: 1,
      // perPage: 10,
      searchFields: {
        doc_type: '',
        content_location: '',
        name_matching_option: '',
        name_matching_text: '',
        category: '',
        language: '',
        ocr_engine: '',
        page_rotate: '',
        barcode: '',
      },
      sortField: 'doc_type',
      sortDesc: false,
      errorMessage: '',
      fields: [
        {
          key: 'doc_type', label: 'Document Type', sortable: true, searchable: true,
        },
        {
          key: 'translated_doc_type', label: 'Translated Doc Type', sortable: true, searchable: true,
        },
        { key: 'content_location', label: 'Content Location', sortable: true },
        { key: 'name_matching_option', label: 'Name Matching Option', sortable: true },
        { key: 'name_matching_text', label: 'Name Matching Text', sortable: true },
        { key: 'category', label: 'Category', sortable: true },
        { key: 'language', label: 'Language', sortable: true },
        { key: 'ocr_engine', label: 'OCR Engine', sortable: true },
        { key: 'page_rotate', label: 'Page Rotate', sortable: true },
        { key: 'barcode', label: 'Barcode', sortable: true },
        { key: 'action', label: 'Actions' },
      ],
      templateNames: [],
      editingItem: null,
      editingId: null,
      localDocumentErrors: {},
    }
  },
  computed: {
    computedFields() {
      return this.fields
    },
    items() {
      return this.$store.state.profile.documents || []
    },
    options() {
      return this.$store.getters['definitionSettings/documentTypeOptions'] || []
    },
    documentTypes() {
      const docTypeSettings = this.$store.getters['definitionSettings/options']['options-meta-root-type']
      if (!docTypeSettings) return []
      const arr = docTypeSettings.items.map(item => item[docTypeSettings.valueKey])
      return [...new Set(arr)]
    },
    templateOptions() {
      return this.templates.map(t => ({
        label: t.name,
        value: t.id,
      }))
    },
    totalRecords() {
      return this.searchableItems.length
    },
    hasRowErrors() {
      return id => this.localDocumentErrors[id] && Object.keys(this.localDocumentErrors[id]).length > 0
    },
    translatedProfileDocuments() {
      return this.$store.getters['profile/translated_documents'] || []
    },
  },
  watch: {
    items: {
      handler() {
        this.setInitialState()
      },
      immediate: true,
      deep: true,
    },
    searchFields: {
      handler() {
        this.onColumnSearch()
      },
      deep: true,
    },
    documentErrors: {
      immediate: true,
      deep: true,
      handler(newVal) {
        // Convert index-based errors to ID-based errors
        const idBasedErrors = {}
        Object.entries(newVal || {}).forEach(([index, errors]) => {
          const doc = this.items[parseInt(index, 10)]
          if (doc && doc.id) {
            idBasedErrors[doc.id] = errors
          }
        })
        this.localDocumentErrors = idBasedErrors
      },
    },
  },
  created() {
    this.fetchTemplates()
  },

  methods: {
    toggleSort(header) {
      if (header.sortable) {
        if (this.sortField === header.key) {
          this.sortDesc = !this.sortDesc
        } else {
          this.sortField = header.key
          this.sortDesc = false
        }
        this.onColumnSearch()
      }
    },
    openDialog() {
      this.dialog = true
      this.form.doc_types = [...this.items.map(d => d.doc_type)]
    },
    addDocuments(newDocument) {
      const transformedDoc = {
        id: uuidv4(),
        doc_type: newDocument.docType,
        content_location: newDocument.contentLocation,
        template: newDocument.template,
        name_matching_option: newDocument.nameMatchingOption,
        name_matching_text: newDocument.nameMatchingText,
        category: newDocument.category,
        language: newDocument.language,
        ocr_engine: newDocument.OCREngine,
        page_rotate: newDocument.pageRotate || false,
        barcode: newDocument.barcode || false,
      }

      this.$store.commit('profile/ADD_DOCUMENT', transformedDoc)
      this.setInitialState()
      this.dialog = false
    },
    editItem(item) {
      // Clear errors for this document
      this.clearDocumentErrors(item.id)

      this.dialog = true
      this.editingId = item.id
      this.editingItem = cloneDeep(item)
      this.localDocumentErrors = {}
    },
    updateTransatedDocTypes(docType) {
      const profileDocTypes = this.items.map(e => e.doc_type)
      if (profileDocTypes.includes(docType)) {
        return
      }

      const translatedDocuments = this.translatedProfileDocuments
        .filter(e => e.doc_type !== docType)
        .filter(e => e.translated_doc_type !== docType)
      this.$store.commit('profile/SET_TRANSLATED_DOCUMENTS', translatedDocuments)
    },
    handleSubmit(newDocument) {
      const transformedDoc = {
        doc_type: newDocument.docType,
        content_location: newDocument.contentLocation,
        template: newDocument.template,
        name_matching_option: newDocument.nameMatchingOption,
        name_matching_text: newDocument.nameMatchingText,
        category: newDocument.category,
        language: newDocument.language,
        ocr_engine: newDocument.OCREngine,
        page_rotate: newDocument.pageRotate || false,
        barcode: newDocument.barcode || false,
      }

      if (this.editingId) {
        // Update existing document by ID
        transformedDoc.id = this.editingId
        this.$store.commit('profile/UPDATE_DOCUMENT', {
          id: this.editingId,
          updatedDoc: transformedDoc,
        })

        // Update Translated Documents
        if (this.editingItem.doc_type !== transformedDoc.doc_type) {
          this.updateTransatedDocTypes(this.editingItem.doc_type)
        }

        // Update Document Hierarchy for Keys to filter supporting documents
        if (transformedDoc.category === 'Supporting') {
          this.updateDocumentHierarchyForKeys(this.editingItem.doc_type)
        }
      } else {
        // Add new document with unique ID
        transformedDoc.id = uuidv4()
        this.$store.commit('profile/ADD_DOCUMENT', transformedDoc)
      }

      this.setInitialState()
      this.closeDialog()
    },

    updateDocumentHierarchyForKeys(docType) {
      // Get all keys from the profile store
      const keys = this.$store.state.profile.keys || []

      // Loop through each key and remove the doc_type if it exists in their documents array
      const updatedKeys = keys.map(key => {
        if (key.documents && Array.isArray(key.documents)) {
          // Filter out the document with the matching doc_type
          const filteredDocuments = key.documents.filter(doc => doc.doc_type !== docType)

          // Reorganize priorities sequentially starting from 1
          const reorganizedDocuments = filteredDocuments
            .sort((a, b) => a.priority - b.priority) // Sort by existing priority
            .map((doc, index) => ({
              ...doc,
              priority: index + 1, // Reassign priorities starting from 1
            }))

          // Return the key with updated documents array
          return {
            ...key,
            documents: reorganizedDocuments,
          }
        }
        return key
      })

      // Update the keys in the store
      this.$store.commit('profile/SET_SELECTED_KEYS', updatedKeys)
    },

    getFieldError(documentId, fieldName) {
      // documentErrors structure: { [documentId]: { [fieldName]: errorMessage } }
      return this.localDocumentErrors[documentId]?.[fieldName] || ''
    },

    // Clear errors for specific document
    clearDocumentErrors(documentId) {
      if (this.localDocumentErrors[documentId]) {
        // Create new object to maintain reactivity
        const newErrors = { ...this.localDocumentErrors }
        delete newErrors[documentId]
        this.localDocumentErrors = newErrors
        // Emit changes to parent (convert back to index-based for parent compatibility)
        const indexBasedErrors = {}
        Object.entries(newErrors).forEach(([id, errors]) => {
          const index = this.items.findIndex(doc => doc.id === id)
          if (index !== -1) {
            indexBasedErrors[index] = errors
          }
        })
        this.$emit('update-errors', indexBasedErrors)
      }
    },

    closeDialog() {
      this.dialog = false
      this.editingItem = null
      this.editingId = null
    },
    deleteItem(documentId) {
      // Find the document by ID
      const deletedItem = this.items.find(doc => doc.id === documentId)
      const deletedDocType = deletedItem?.doc_type

      this.$store.commit('profile/REMOVE_DOCUMENT_BY_ID', documentId)

      // Update Translated Documents
      if (deletedDocType) {
        this.updateTransatedDocTypes(deletedDocType)
      }

      this.setInitialState()
      this.localDocumentErrors = {}
    },
    fetchTemplates() {
      this.loading = true
      const params = {
        page_size: 100,
        page: 1,
      }
      axios.get('/dashboard/template/', { params })
        .then(res => {
          this.templateNames = res.data.results.map(item => item.template_name)
        })
        .catch(error => {
          this.error = error?.response?.data?.detail || 'Error fetching Template'
        })
        .finally(() => {
          this.loading = false
        })
    },
    onColumnSearch() {
      this.loading = true
      const filteredItems = cloneDeep(this.searchableItems)
      const activeSearches = Object.entries(this.searchFields)?.filter(
        // eslint-disable-next-line no-unused-vars
        ([_, value]) => value !== '' && value !== null && value !== undefined,
      )

      let result = filteredItems?.filter(item => activeSearches.every(([key, searchValue]) => {
        const itemValue = item[key]?.toString().toLowerCase()
        return itemValue && itemValue.includes(searchValue.toLowerCase())
      }))

      // Apply sorting
      if (this.sortField) {
        result = result.sort((a, b) => {
          const aValue = a[this.sortField]?.toString().toLowerCase()
          const bValue = b[this.sortField]?.toString().toLowerCase()
          if (aValue < bValue) return this.sortDesc ? 1 : -1
          if (aValue > bValue) return this.sortDesc ? -1 : 1
          return 0
        })
      }

      // Store all filtered items
      this.filteredItems = result
      this.renderedItems = this.filteredItems
      this.loading = false
    },

    // applyPagination() {
    //   const start = (this.currentPage - 1) * this.perPage
    //   const end = start + this.perPage
    //   this.renderedItems = this.filteredItems.slice(start, end)
    // },

    // pageChanged(page) {
    //   this.currentPage = page
    //   this.applyPagination()
    // },

    setInitialState() {
      // Create a mapping of document types to their translated versions
      const translatedDocTypesMap = this.$store.state.profile.translated_documents
        .reduce((mapping, document) => ({
          ...mapping,
          [document.doc_type]: document.translated_doc_type,
        }), {})

      this.searchableItems = this.items.map(item => ({
        doc_type: item.doc_type || '',
        content_location: item.content_location || '',
        template: item.template || null,
        name_matching_option: item.name_matching_option || '',
        name_matching_text: item.name_matching_text || '',
        category: item.category || '',
        language: item.language || '',
        ocr_engine: item.ocr_engine || '',
        page_rotate: item.page_rotate || false,
        barcode: item.barcode || false,
        show_embedded_img: item.show_embedded_img || false,
        id: item.id || uuidv4(), // Generate ID if it doesn't exist
        translated_doc_type: translatedDocTypesMap[item.doc_type] || '',
      }))

      // Update store to ensure all documents have IDs
      const documentsNeedingIds = this.searchableItems.filter((item, index) => !this.items[index].id)
      if (documentsNeedingIds.length > 0) {
        this.$store.commit('profile/UPDATE_DOCUMENTS', this.searchableItems.map(item => ({
          ...this.items.find(doc => doc.doc_type === item.doc_type && doc.category === item.category) || item,
          id: item.id,
        })))
      }

      this.filteredItems = [...this.searchableItems]
      this.renderedItems = this.filteredItems
      this.onColumnSearch()
    },

    handleImportSuccess() {
      // Reload the profile data after successful import
      this.$emit('reload-profile')
      this.importDialog = false
      this.localDocumentErrors = {}
    },
  },
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.bg-light-danger {
  background-color: rgba(220, 53, 69, 0.1);
}
.table-busy {
  opacity: 0.55;
  pointer-events: none;
}
.table-busy-spinner {
 opacity: 0.55;
}
.profiles-table td {
  padding: 0.4rem 0.5rem;
  vertical-align: baseline;
}

.profiles-table th {
  padding: 0.8rem 0.5rem;
}

.profiles-table tr.has-row-details {
  border-bottom: none; /* or "none" instead of "hidden" */
}
.table-responsive {
  overflow-x: auto;
  white-space: normal;
}
.text-danger {
  font-size: 0.8rem;
}
tr.has-error {
  background-color: rgba(220, 53, 69, 0.05);
}
tr.has-error:hover {
  background-color: rgba(220, 53, 69, 0.1);
}
</style>
