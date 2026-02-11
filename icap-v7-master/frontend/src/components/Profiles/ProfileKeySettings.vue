<template>
  <b-modal
    v-model="showModal"
    :title="title || 'Process Key Doc Types'"
    no-close-on-backdrop
    centered
    hide-footer
    @hidden="handleHidden"
  >
    <div
      class="checkbox-list-container"
      :class="{ 'dark-mode': isDark }"
    >
      <div class="rendered-items-list">
        <!-- {{ selectedKey }} -->
        <draggable
          v-model="renderItems"
          :options="{ handle: '.drag-handle, .list-item', animation: 200 }"
          class="draggable-container"
          @change="persistChanges"
        >
          <div
            v-for="(item, index) in renderItems"
            :key="item.id"
            class="list-item"
            :class="{ 'checked': item.checked }"
          >
            <div
              class="drag-handle"
              title="Drag to reorder"
            >
              ⋮⋮
            </div>

            <div class="item-content">
              <b-form-checkbox
                :id="'item-' + item.id"
                v-model="item.checked"
                class="item-checkbox"
                @change="persistChanges"
              >
                {{ item.text }}
              </b-form-checkbox>
            </div>

            <div class="item-controls">
              <b-button
                :disabled="index === 0"
                variant="outline-secondary"
                size="sm"
                title="Move up"
                class="control-btn"
                @click="moveUp(index)"
              >
                ↑
              </b-button>
              <b-button
                :disabled="index === renderItems.length - 1"
                variant="outline-secondary"
                size="sm"
                title="Move down"
                class="control-btn"
                @click="moveDown(index)"
              >
                ↓
              </b-button>
            </div>
          </div>
        </draggable>
      </div>
    </div>
  </b-modal>
</template>

<script>
import { cloneDeep } from 'lodash'
import {
  BButton,
  BFormCheckbox,
} from 'bootstrap-vue'
import draggable from 'vuedraggable'
import useAppConfig from '@core/app-config/useAppConfig'
import { computed } from '@vue/composition-api'

export default {
  name: 'ProfileKeySettings',
  setup() {
    const { skin } = useAppConfig()

    const isDark = computed(() => skin.value === 'dark')

    return { skin, isDark }
  },
  components: {
    BButton,
    BFormCheckbox,
    draggable,
  },
  props: {
    title: {
      type: String,
      default: '',
    },
    selectedKey: {
      type: Object,
      required: true,
      default: () => {},
    },
  },
  data() {
    return {
      showModal: true,
      items: [],
      renderItems: [],
    }
  },
  computed: {
    selectedKeyDocuments() {
      // Use precedence array (simple string array in saved order)
      return this.selectedKey.precedence || []
    },
    uniqueProfileDocuments() {
      // Get all document types from the profile, filtered by Processing category
      const allDocTypes = new Set(this.$store.state.profile.documents.filter(doc => doc.category === 'Processing').map(doc => doc.doc_type))

      // Get translated document types
      const translatedDocTypes = this.$store.state.profile.translated_documents.map(
        doc => doc.doc_type,
      )

      // Return only document types that haven't been translated yet
      return Array.from(allDocTypes).filter(
        docType => !translatedDocTypes.includes(docType),
      )
    },
    formattedItems() {
      const selectedDocs = this.selectedKeyDocuments
      const profileDocs = this.uniqueProfileDocuments

      const selectedItems = selectedDocs.filter(docType => this.uniqueProfileDocuments.includes(docType)).map(docType => ({
        id: docType,
        text: docType,
        checked: true,
      }))

      const unselectedItems = profileDocs
        .filter(docType => !selectedDocs.includes(docType))
        .map(docType => ({
          id: docType,
          text: docType,
          checked: false,
        }))

      return [...selectedItems, ...unselectedItems]
    },
    selectedDocumentTypes() {
      // Return simple array of doc_type strings in order
      return this.renderItems
        .filter(item => item.checked)
        .map(item => item.text)
    },
  },
  created() {
    this.items = this.formattedItems
    this.renderItems = cloneDeep(this.items)
  },
  methods: {
    persistChanges() {
      const payload = {
        keyValue: this.selectedKey.keyValue,
        precedence: this.selectedDocumentTypes,
      }
      this.$emit('save', payload)
    },
    handleHidden() {
      this.renderItems = cloneDeep(this.items)
      this.$emit('modal-closed')
    },
    moveUp(index) {
      if (index > 0) {
        const item = this.renderItems.splice(index, 1)[0]
        this.renderItems.splice(index - 1, 0, item)
        this.persistChanges()
      }
    },
    moveDown(index) {
      if (index < this.renderItems.length - 1) {
        const item = this.renderItems.splice(index, 1)[0]
        this.renderItems.splice(index + 1, 0, item)
        this.persistChanges()
      }
    },
  },
}
</script>

<style scoped>
.checkbox-list-container {
  max-width: 500px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
}

.rendered-items-list {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
}

.dark-mode .rendered-items-list {
  background: #161d31;
}

.draggable-container {
  min-height: 50px;
}

.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  transition: all 0.2s ease;
  cursor: move;
}

.list-item:last-child {
  margin-bottom: 0;
}

.dark-mode .list-item {
  background: #283046;
  border: 1px solid #283046;
}

.list-item:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.list-item.checked {
  background-color: #f0f8ff;
  border-color: #4CAF50;
}

.dark-mode .list-item.checked {
  background-color: #283046;
}

.drag-handle {
  color: #999;
  font-size: 16px;
  font-weight: bold;
  margin-right: 8px;
  cursor: grab;
  user-select: none;
  padding: 4px;
}

.drag-handle:hover {
  color: #666;
}

.drag-handle:active {
  cursor: grabbing;
}

.item-content {
  display: flex;
  align-items: center;
  flex: 1;
}

.item-checkbox {
  margin-right: 12px;
}

.item-checkbox >>> .custom-control-label {
  font-size: 14px;
  color: #333;
  user-select: none;
}

.dark-mode .item-checkbox >>> .custom-control-label {
  color: #b4b7bd;
}

.list-item.checked .item-checkbox >>> .custom-control-label {
  color: #4CAF50;
  font-weight: 500;
}

.item-controls {
  display: flex;
  gap: 4px;
}

.control-btn {
  margin-left: 4px;
}
</style>
