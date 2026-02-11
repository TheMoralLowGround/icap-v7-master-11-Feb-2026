<template>
  <b-modal
    :visible="value"
    :title="modalTitle"
    centered
    size="lg"
    no-close-on-backdrop
    hide-footer
    @hidden="close"
  >
    <b-card>
      <BRow
        class="justify-content-center mb-2"
      >
        <BCol
          cols="5"
        >
          <v-select
            id="docType"
            v-model="form.docType"
            :options="translationFormList"
            placeholder="Select Doc Type"
            @input="errorMessage = ''"
          />
        </BCol>
        <BCol
          cols="5"
        >
          <v-select
            id="docType"
            v-model="form.translatedDocType"
            :options="translationToList"
            placeholder="Select Translated Doc Type"
            @input="errorMessage = ''"
          />
        </BCol>
        <BCol
          cols="2"
        >
          <b-button
            variant="primary"
            class="ml-auto"
            @click="translate"
          >
            Translate
          </b-button>
        </BCol>
      </BRow>

      <!-- Error Message -->
      <div
        v-if="errorMessage"
        class="mb-2 px-4 py-2 bg-light-danger text-danger rounded"
      >
        {{ errorMessage }}
      </div>

      <b-table-simple
        responsive
        striped
        :busy="loading"
        :class="{ 'table-busy': loading }"
      >
        <b-thead>
          <b-tr>
            <b-th
              v-for="(field, index) in computedFields"
              :key="index"
            >
              {{ field.label }}
            </b-th>
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
              v-for="(item, index) in translatedDocuments"
              :key="`row-${index}`"
            >
              <b-td>{{ item.doc_type }}</b-td>
              <b-td>{{ item.translated_doc_type }}</b-td>
              <b-td>
                <div class="d-flex gap-3 justify-content-end">
                  <feather-icon
                    v-b-tooltip.hover
                    title="Delete Translation"
                    icon="Trash2Icon"
                    class="cursor-pointer text-danger"
                    size="16"
                    @click="deleteItem(index)"
                  />
                </div>
              </b-td>
            </b-tr>
          </template>
        </b-tbody>
      </b-table-simple>
      <div
        v-if="!loading && translatedDocuments.length === 0"
        class="text-center m-3"
      >
        No records found!
      </div>
    </b-card>
  </b-modal>
</template>

<script>
import { cloneDeep } from 'lodash'

import {
  VBTooltip,
  BCard,
  BButton,
  BTableSimple,
  BSpinner,
  BTr,
  BTbody,
  BThead,
  BTh,
  BTd,
  BRow,
  BCol,
} from 'bootstrap-vue'
import vSelect from 'vue-select'

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
    BSpinner,
    BRow,
    BCol,
    vSelect,
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    items: {
      type: Array,
      required: true,
    },
    modalTitle: {
      type: String,
      default: 'Translate Document',
    },
  },
  data() {
    return {
      loading: false,
      form: {
        docType: '',
        translatedDocType: '',
      },
      fields: [
        { key: 'doc_type', label: 'Doc Type', sortable: true },
        { key: 'translated_doc_type', label: 'Translated Doc Type', sortable: true },
        { key: 'action', label: 'Actions' },
      ],
      translatedDocumentsLocal: [],
      errorMessage: '',
    }
  },
  computed: {
    computedFields() {
      return this.fields
    },
    allDocTypes() {
      return this.items.map(e => e.doc_type)
    },
    translatedProfileDocuments() {
      return this.$store.getters['profile/translated_documents'] || []
    },
    translatedDocuments() {
      return this.translatedDocumentsLocal
    },
    translatedDocTypes() {
      return this.translatedDocuments.map(e => e.doc_type)
    },
    translatedDocTypesParent() {
      return this.translatedDocuments.map(e => e.translated_doc_type)
    },
    translationFormList() {
      return this.allDocTypes.filter(e => !this.translatedDocTypes.includes(e)).filter(e => !this.translatedDocTypesParent.includes(e))
    },
    translationToList() {
      return this.allDocTypes.filter(e => !this.translatedDocTypes.includes(e))
    },
  },
  watch: {
    translatedProfileDocuments: {
      handler(val) {
        this.translatedDocumentsLocal = cloneDeep(val)
      },
    },
  },
  created() {
    this.translatedDocumentsLocal = cloneDeep(this.translatedProfileDocuments)
  },
  methods: {
    translate() {
      const { docType, translatedDocType } = this.form
      this.errorMessage = ''

      // Validation with early returns
      if (!docType?.trim()) {
        this.errorMessage = 'Please choose a Doc Type'
        return
      }

      if (!translatedDocType?.trim()) {
        this.errorMessage = 'Please choose a Translated Doc Type'
        return
      }

      if (docType === translatedDocType) {
        this.errorMessage = 'Please choose a different Translated Doc Type'
        return
      }

      // Update documents in each profile key and adjust priorities
      this.$store.state.profile.keys = this.$store.state.profile.keys.map(key => {
        if (!key.documents?.length) return key

        // Filter out the document type and sort by priority
        const filteredDocs = key.documents
          .filter(doc => doc.doc_type !== docType)
          .sort((a, b) => a.priority - b.priority)
          .map((doc, index) => ({
            ...doc,
            priority: index + 1,
          }))

        return {
          ...key,
          documents: filteredDocs,
        }
      })

      // Add mapping and persist
      this.translatedDocumentsLocal.push({
        doc_type: docType,
        translated_doc_type: translatedDocType,
      })

      this.persistTranslations()
      this.clean()
    },
    deleteItem(index) {
      this.translatedDocumentsLocal.splice(index, 1)
      this.persistTranslations()
    },
    persistTranslations() {
      const translatedDocuments = cloneDeep(this.translatedDocumentsLocal)

      this.$store.commit('profile/SET_TRANSLATED_DOCUMENTS', translatedDocuments)
      this.$emit('save')
    },
    close() {
      this.clean()
      this.$emit('input', false)
      this.$emit('close')
    },
    clean() {
      this.form.docType = ''
      this.form.translatedDocType = ''
      this.errorMessage = ''
    },
  },
}
</script>

<style scoped>
.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.table-responsive {
  max-height: 300px;
  overflow-y: auto;
}

.bg-light-danger {
  background-color: #f8d7da;
}

.text-danger {
  color: #dc3545;
}
</style>
