<template>
  <b-modal
    :visible="value"
    :title="modalTitle"
    centered
    size="lg"
    no-close-on-backdrop
    ok-title="Add"
    @ok="handleSubmit"
    @hidden="close"
  >
    <b-row>
      <b-col cols="12">
        <validation-observer ref="formObserver">
          <b-form @submit.stop.prevent="handleSubmit">
            <!-- Document Type and Content Location in same row -->
            <b-row>
              <b-col md="6">
                <b-form-group
                  label="Document Type"
                  label-for="docType"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Document Type"
                    rules="required"
                  >
                    <v-select
                      id="docType"
                      ref="documentDocType"
                      v-model="form.docType"
                      :options="documentTypes"
                      :reduce="option => option.value || option"
                      :state="errors.length > 0 ? false : null"
                      @input="onDocumentTypeChange"
                      @open="scrollToSelected(documentTypes, form.docType)"
                    />
                    <small class="text-danger">
                      {{ errors[0] }}
                    </small>
                  </validation-provider>
                </b-form-group>
              </b-col>
              <b-col md="6">
                <b-form-group
                  label="Content Location"
                  label-for="contentLocation"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Content Location"
                    rules="required"
                  >
                    <v-select
                      id="contentLocation"
                      v-model="form.contentLocation"
                      :options="['Email Body', 'Email Attachment']"
                      :state="errors.length > 0 ? false : null"
                      @input="updateCategory"
                    />
                    <small class="text-danger">
                      {{ errors[0] }}
                    </small>
                  </validation-provider>
                </b-form-group>
              </b-col>
            </b-row>

            <!-- Name Matching -->
            <b-form-group
              label="Name Matching"
              label-for="nameMatching"
            >
              <div class="d-flex">
                <!-- Name Matching Option Dropdown -->
                <validation-provider
                  #default="{ errors }"
                  name="Name Matching Option"
                  :rules="!['Email Body', 'Additional Document'].includes(form.contentLocation) ? 'required' : ''"
                  style="flex: 1; margin-right: 10px;"
                  vid="nameMatchingOption"
                >
                  <v-select
                    id="nameMatchingOption"
                    v-model="form.nameMatchingOption"
                    :options="nameMatchingOptions"
                    :disabled="['Email Body', 'Additional Document'].includes(form.contentLocation)"
                    :state="errors.length > 0 ? false : null"
                    @input="onChangeMatchingOption"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </validation-provider>

                <!-- Name Matching Text Input -->
                <validation-provider
                  #default="{ errors }"
                  name="Name Matching Text"
                  :rules="!['Email Body', 'Additional Document'].includes(form.contentLocation) && !['None', 'Auto'].includes(form.nameMatchingOption) ? 'required' : ''"
                  vid="nameMatchingText"
                  style="flex: 1;"
                >
                  <b-form-input
                    id="nameMatchingText"
                    v-model="form.nameMatchingText"
                    :disabled="['Email Body', 'Additional Document'].includes(form.contentLocation) || ['None', 'Auto'].includes(form.nameMatchingOption)"
                    placeholder="Matching text"
                    :state="errors.length > 0 ? false : null"
                  />
                  <small class="text-danger">{{ errors[0] }}</small>
                </validation-provider>
              </div>
            </b-form-group>

            <!-- Category, Language and OCR Engine in same row -->
            <b-row>
              <b-col md="4">
                <b-form-group
                  label="Category"
                  label-for="category"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Category"
                    rules="required"
                  >
                    <v-select
                      id="category"
                      v-model="form.category"
                      :options="categoryOptions"
                      :state="errors.length > 0 ? false : null"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </validation-provider>
                </b-form-group>
              </b-col>
              <b-col md="4">
                <b-form-group
                  label="Language"
                  label-for="language"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="Language"
                    :rules="form.contentLocation !== 'Additional Document' ? 'required' : ''"
                  >
                    <v-select
                      id="language"
                      ref="documentLanguage"
                      v-model="form.language"
                      :options="languageOptions"
                      :disabled="form.contentLocation === 'Additional Document'"
                      :state="errors.length > 0 ? false : null"
                      @open="scrollToSelected(languageOptions, form.language)"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </validation-provider>
                </b-form-group>
              </b-col>
              <b-col md="4">
                <b-form-group
                  label="OCR Engine"
                  label-for="ocrEngine"
                >
                  <validation-provider
                    #default="{ errors }"
                    name="OCR Engine"
                    :rules="form.contentLocation !== 'Additional Document' ? 'required' : ''"
                  >
                    <v-select
                      id="ocrEngine"
                      v-model="form.OCREngine"
                      :options="ocrEngineOptions"
                      :disabled="form.contentLocation === 'Additional Document'"
                      :state="errors.length > 0 ? false : null"
                      :reduce="option => option.value"
                    />
                    <small class="text-danger">{{ errors[0] }}</small>
                  </validation-provider>
                </b-form-group>
              </b-col>
            </b-row>

            <!-- Template (moved after OCR Engine) -->
            <b-form-group
              label="Template"
              label-for="template"
            >
              <validation-provider
                #default="{ errors }"
                name="Template"
              >
                <v-select
                  id="template"
                  ref="documentTemplate"
                  v-model="form.template"
                  :options="templateNames"
                  :reduce="option => option.value || option"
                  :state="errors.length > 0 ? false : null"
                  @open="scrollToSelected(templateNames, form.template)"
                />
                <small class="text-danger">{{ errors[0] }}</small>
              </validation-provider>
            </b-form-group>

            <!-- Toggle buttons with labels left and switches right -->
            <b-row>
              <b-col md="4">
                <b-form-group
                  label-cols="8"
                  label="Show Embedded Img"
                  label-for="show_embedded_img"
                  class="d-flex align-items-center"
                >
                  <b-form-checkbox
                    id="show_embedded_img"
                    v-model="form.show_embedded_img"
                    switch
                    class="ml-auto"
                  />
                </b-form-group>
              </b-col>
              <b-col md="4">
                <b-form-group
                  label-cols="8"
                  label="Page Rotate"
                  label-for="pageRotate"
                  class="d-flex align-items-center"
                >
                  <b-form-checkbox
                    id="pageRotate"
                    v-model="form.pageRotate"
                    switch
                    class="ml-auto"
                  />
                </b-form-group>
              </b-col>
              <b-col md="4">
                <b-form-group
                  label-cols="8"
                  label="Barcode"
                  label-for="barcode"
                  class="d-flex align-items-center"
                >
                  <b-form-checkbox
                    id="barcode"
                    v-model="form.barcode"
                    switch
                    class="ml-auto"
                  />
                </b-form-group>
              </b-col>
            </b-row>
          </b-form>
        </validation-observer>
      </b-col>
    </b-row>

    <div
      v-if="errorMessage"
      class="my-4 px-4 py-2 bg-light-danger text-danger rounded"
    >
      {{ errorMessage }}
    </div>
  </b-modal>
</template>

<script>
import {
  BCol, BRow, BForm, BFormGroup, BFormInput, BFormCheckbox,
} from 'bootstrap-vue'
import vSelect from 'vue-select'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
// eslint-disable-next-line no-unused-vars
import { required } from '@validations'

export default {
  components: {
    BRow,
    BCol,
    BForm,
    BFormGroup,
    BFormInput,
    BFormCheckbox,
    vSelect,
    ValidationProvider,
    ValidationObserver,
  },
  props: {
    value: { type: Boolean, default: false },
    documentTypes: { type: Array, default: () => ['Bill of entry', 'Notes'] },
    templateNames: { type: Array, default: () => [] },
    languageOptions: { type: Array, default: () => ['English', 'Spanish', 'French'] },
    errorMessage: { type: String, default: '' },
    editingItem: { type: Object, default: null },
    editingId: { type: String, default: null },
  },
  data() {
    return {
      form: {
        docType: null,
        contentLocation: 'Email Attachment',
        template: null,
        nameMatchingOption: '',
        nameMatchingText: '',
        category: 'Processing',
        language: 'English',
        OCREngine: 'S',
        show_embedded_img: false,
        pageRotate: false,
        barcode: false,
      },
      ocrEngineOptions: [
        { label: 'S', value: 'S' },
        { label: 'P', value: 'P' },
        { label: 'A', value: 'A' },
      ],
    }
  },
  computed: {
    nameMatchingOptions() {
      const commonOptions = ['StartsWith', 'EndsWith', 'Contains', 'Regex']
      const docTypes = this.$store.state.profile.classifiableDocTypes
      return docTypes.includes(this.form?.docType?.toLowerCase()) ? [...commonOptions, 'Auto'] : commonOptions
    },
    modalTitle() {
      return this.editingItem ? 'Edit Document' : 'Add Document'
    },
    categoryOptions() {
      if (this.form.contentLocation === 'Additional Document') {
        return ['Supporting', 'Ignoring']
      }

      return ['Processing', 'Supporting']
    },
  },
  watch: {
    editingItem: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          // Map the item data to the form structure
          this.form = {
            docType: newVal.doc_type,
            contentLocation: newVal.content_location,
            template: newVal.template,
            nameMatchingOption: newVal.name_matching_option,
            nameMatchingText: newVal.name_matching_text,
            category: newVal.category,
            language: newVal.language,
            OCREngine: newVal.ocr_engine,
            show_embedded_img: newVal.show_embedded_img || false,
            pageRotate: newVal.page_rotate || false,
            barcode: newVal.barcode || false,
            id: newVal.id,
          }
        } else {
          this.resetForm()
        }
      },
    },
  },
  methods: {
    close() {
      this.$emit('close')
      this.resetForm()
    },
    onChangeMatchingOption() {
      if (this.form.nameMatchingOption === 'Auto') {
        this.form.nameMatchingText = ''
      }
    },
    onDocumentTypeChange(value) {
      // Trim whitespace from the docType value
      this.form.docType = typeof value === 'string' ? value.trim() : value
      this.form.nameMatchingOption = ''
      this.form.nameMatchingText = ''
    },
    async handleSubmit(bvModalEvt) {
      // Prevent modal from closing
      bvModalEvt.preventDefault()

      // Validate all fields using vee-validate
      const isValid = await this.$refs.formObserver.validate()

      if (!isValid) {
        // Validation failed - errors will be shown by vee-validate
        // Scroll to first error
        this.scrollToFirstError()
        return
      }

      // Then check for duplicate name_matching_text
      if (this.form.nameMatchingText && !['None', 'Auto'].includes(this.form.nameMatchingOption)) {
        const trimmedMatchingText = this.form.nameMatchingText.trim()
        const isDuplicate = this.$parent.items.some(item => {
          // Skip checking against the item we're currently editing
          if (this.editingId && item.id === this.editingId) return false
          return item.name_matching_text === trimmedMatchingText
        })

        if (isDuplicate) {
          // Manually set error for the field
          this.$refs.formObserver.setErrors({
            nameMatchingText: ['This name matching text must be unique'],
          })
          this.scrollToFirstError()
          return
        }
      }

      // Prepare data before resetting and trim docType
      const documentData = {
        ...this.form,
        docType: typeof this.form.docType === 'string' ? this.form.docType.trim() : this.form.docType,
        nameMatchingText: typeof this.form.nameMatchingText === 'string' ? this.form.nameMatchingText.trim() : this.form.nameMatchingText,
        ...(this.editingItem && { id: this.editingItem.id }),
      }

      // 1. Reset form FIRST (clears fields)
      if (!this.editingItem) this.resetForm()

      // 2. Clear validation errors
      this.$refs.formObserver.reset()

      // 3. Emit submit event
      this.$emit('submit', documentData)

      // Close the modal manually after successful submission
      this.$nextTick(() => {
        this.$bvModal.hide('modal-id') // Replace with your modal's ID
      })
    },

    scrollToFirstError() {
      this.$nextTick(() => {
        const firstErrorElement = document.querySelector('.is-invalid')
        if (firstErrorElement) {
          firstErrorElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
          })
        }
      })
    },
    resetForm() {
      this.form = {
        docType: null,
        contentLocation: 'Email Attachment',
        template: null,
        nameMatchingOption: '',
        nameMatchingText: '',
        category: 'Processing',
        language: 'English',
        OCREngine: 'S',
        show_embedded_img: false,
        pageRotate: false,
        barcode: false,
        id: null,
      }
    },
    updateCategory() {
      [this.form.category] = this.categoryOptions
      if (['Email Body', 'Additional Document'].includes(this.form.contentLocation)) {
        this.form.nameMatchingOption = ''
        this.form.nameMatchingText = ''
      }
    },
    // Scrolls the dropdown menu to bring the selected item into view.
    scrollToSelected(options, selectedValue) {
      this.$nextTick(() => {
        // Helper function to scroll a dropdown menu to the selected item
        const scrollDropdownToSelected = (dropdownMenu, selectedIndex) => {
          if (dropdownMenu && selectedIndex >= 0) {
            // Calculate scroll position by assuming each item has a uniform height
            const itemHeight = dropdownMenu.scrollHeight / options.length

            // Adjust scrollTop to bring the selected item closer to the top
            const scrollPosition = Math.max(0, selectedIndex * itemHeight - itemHeight * 2)
            // eslint-disable-next-line no-param-reassign
            dropdownMenu.scrollTop = scrollPosition
          }
        }

        // Get references to dropdown menus
        const documentDocTypeItems = this.$refs.documentDocType?.$refs?.dropdownMenu
        const languageItems = this.$refs.documentLanguage?.$refs?.dropdownMenu
        const templateItems = this.$refs.documentTemplate?.$refs?.dropdownMenu

        // Find the index of the selected value
        const selectedIndex = options.indexOf(selectedValue)
        // const findSelectedIndex = options.findIndex(option => option.value === selectedValue)

        // Scroll each dropdown menu if applicable
        if (documentDocTypeItems) scrollDropdownToSelected(documentDocTypeItems, selectedIndex)
        if (languageItems) scrollDropdownToSelected(languageItems, selectedIndex)
        if (templateItems) scrollDropdownToSelected(templateItems, selectedIndex)
      })
    },
  },
}
</script>

<style scoped>
.bg-light-danger {
  background-color: rgba(220, 53, 69, 0.1);
}
.d-flex {
  display: flex;
  gap: 10px;
}
.ml-auto {
  margin-left: auto;
}
</style>
