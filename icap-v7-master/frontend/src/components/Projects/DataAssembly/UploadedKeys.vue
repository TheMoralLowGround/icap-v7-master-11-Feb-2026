<template>
  <div>
    <section class="d-flex justify-content-end mb-4">
      <b-button
        v-if="selectedItems.length"
        variant="primary"
        class="mr-2"
        @click="showTypeModal = true"
      >
        Copy to Keys ({{ selectedItems.length }})
      </b-button>
      <b-button
        variant="outline-primary"
        class="mr-2"
        @click="showYamlModal = true"
      >
        Upload File
      </b-button>
      <b-button
        v-if="hiddenKeysCount"
        variant="outline-secondary"
        @click="restoreHiddenKeys"
      >
        <feather-icon
          icon="EyeIcon"
          size="14"
          class="mr-50"
        />
        Restore Hidden ({{ hiddenKeysCount }})
      </b-button>
    </section>
    <div class="row">

      <div class="col-5">
        <h3>Keys From File</h3>
        <div class="border rounded overflow-hidden tree-container">
          <tree-item
            v-if="treeData.length"
            ref="treeItemRef"
            :children="treeData"
            :selected-ids="selectedIds"
            @selection-changed="handleSelectionChanged"
            @context-menu="showContextMenu"
          />
          <div
            v-else
            class="p-3 text-center text-muted"
          >
            Upload a YAML/JSON file to see keys
          </div>
          <!-- <pre>
          {{ treeData.slice(0,4) }}
        </pre> -->
        </div>
      </div>
      <div class="col-7">
        <h3>Project Keys</h3>
        <data-assembly-project-keys
          :items="projectKeysList"
          :per-page="10"
          @update-item="handleUpdateItem"
          @delete-item="handleDeleteItem"
          @view-all="goToKeysTab"
        />
        <!-- <pre>
          {{ projectKeysList.slice(0,5) }}
        </pre> -->
      </div>
    </div>
    <ImportYamlJson
      v-if="showYamlModal"
      v-model="showYamlModal"
      :project-id="projectId"
      :parse-keys-only="true"
      @keys-parsed="handleKeysParsed"
      @imported="yamlImported"
    />

    <!-- Type Selection Modal -->
    <b-modal
      v-model="showTypeModal"
      title="Select Key Type"
      centered
      size="sm"
      :no-close-on-backdrop="true"
      @ok.prevent="copyToKeys"
      @hidden="duplicateError = ''"
    >
      <div class="mb-3">
        <label class="form-label fw-bold">Select type for selected keys:</label>
        <v-select
          v-model="selectedType"
          :options="typeOptions"
          :clearable="false"
          placeholder="Select Type"
          class="mt-2"
        />
      </div>
      <div class="text-muted small">
        {{ selectedItems.length }} item(s) will be copied to Project Keys
      </div>
      <b-alert
        v-if="duplicateError"
        variant="danger"
        show
        class="mt-2 mb-0"
      >
        {{ duplicateError }}
      </b-alert>
    </b-modal>

    <!-- Right-click Context Menu -->
    <div
      v-if="contextMenu.show"
      class="context-menu"
      :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
      @click.stop
    >
      <div
        class="context-menu-item"
        @click="openTypeModalFromContext"
      >
        <feather-icon
          icon="CopyIcon"
          size="14"
          class="mr-1"
        />
        Copy to Keys
      </div>
      <div
        class="context-menu-item text-danger"
        @click="removeSelectedKeys"
      >
        <feather-icon
          icon="EyeOffIcon"
          size="14"
          class="mr-1"
        />
        Hide Keys
      </div>
    </div>

    <!-- Overlay to close context menu -->
    <div
      v-if="contextMenu.show"
      class="context-menu-overlay"
      @click="hideContextMenu"
      @contextmenu.prevent="hideContextMenu"
    />
  </div>

</template>
<script>
import vSelect from 'vue-select'
import { v4 as uuidv4 } from 'uuid'
import { BButton, BModal, BAlert } from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
import TreeItem from './TreeItem.vue'
import ImportYamlJson from './ImportYamlJson.vue'
import DataAssemblyProjectKeys from './DataAssemblyProjectKeys.vue'

export default {
  components: {
    vSelect,
    BButton,
    BModal,
    BAlert,
    TreeItem,
    ImportYamlJson,
    DataAssemblyProjectKeys,
  },
  data() {
    return {
      requiredField: [],
      projectKeysList: [],
      treeData: [],
      showYamlModal: false,
      showTypeModal: false,
      selectedItems: [],
      selectedIds: [],
      selectedType: 'key',
      typeOptions: ['key', 'table', 'addressBlock', 'addressBlockPartial', 'lookupCode', 'compound'],
      contextMenu: {
        show: false,
        x: 0,
        y: 0,
        item: null,
      },
      duplicateError: '',
    }
  },
  computed: {
    keyItems() {
      return this.$store.getters['project/keyItems'] || []
    },
    projectId() {
      return this.$route?.params?.id
    },
    hiddenKeysCount() {
      // Count hidden keys in treeData recursively
      return this.countHiddenKeys(this.treeData)
    },
  },
  watch: {
    keyItems: {
      immediate: true,
      handler(newVal) {
        if (newVal && newVal.length) {
          this.projectKeysList = newVal.map(item => ({
            ...item,
            uid: item.uid || this.makeUID(),
          }))
        }
      },
    },
  },
  methods: {
    makeUID() {
      return uuidv4()
    || Date.now().toString(36) + Math.random().toString(36)
    },
    handleKeysParsed(keys) {
      // Keys are now in tree format with {name, id, children, ...}
      this.treeData = keys
      this.requiredField = []
      // Clear selection when new file is uploaded
      this.selectedItems = []
      this.selectedIds = []
    },
    yamlImported() {
      this.showYamlModal = false
    },
    handleSelectionChanged(items) {
      this.selectedItems = items || []
      this.selectedIds = this.selectedItems.map(item => item.id)
    },
    copyToKeys(bvModalEvt) {
      // Clear previous error
      this.duplicateError = ''

      // Get existing keyValues from projectKeysList (lowercase for case-insensitive comparison)
      const existingKeyValues = new Set(this.projectKeysList.map(k => (k.keyValue || '').toLowerCase()))

      // Check for duplicates within selected items using Set
      const selectedKeyValues = this.selectedItems.map(item => (item.name || '').toLowerCase())
      const uniqueSelectedKeys = new Set(selectedKeyValues)

      if (uniqueSelectedKeys.size !== selectedKeyValues.length) {
        // Find the duplicate key name for the error message
        const duplicateInSelection = this.selectedItems.find((item, index) => selectedKeyValues.indexOf((item.name || '').toLowerCase()) !== index)?.name || ''
        if (bvModalEvt) {
          bvModalEvt.preventDefault()
        }
        this.duplicateError = `Duplicate key "${duplicateInSelection}" found in selection`
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Duplicate Key',
            icon: 'AlertTriangleIcon',
            text: `Duplicate key "${duplicateInSelection}" found in selection`,
            variant: 'danger',
          },
        })
        return
      }

      // Check for duplicates against existing keys using reduce - stop at first duplicate found
      const duplicateKey = this.selectedItems.reduce((found, item) => {
        if (found) return found // Already found duplicate, skip rest
        const keyValue = item.name || ''
        if (existingKeyValues.has(keyValue.toLowerCase())) {
          return keyValue
        }
        return null
      }, null)

      if (duplicateKey) {
        // Prevent modal from closing so user can see the error
        if (bvModalEvt) {
          bvModalEvt.preventDefault()
        }
        this.duplicateError = `Key "${duplicateKey}" already exists in the list`
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Duplicate Key',
            icon: 'AlertTriangleIcon',
            text: `Key "${duplicateKey}" already exists`,
            variant: 'danger',
          },
        })
        return // Stop processing
      }

      // No duplicates found, proceed with copying
      const newKeys = this.selectedItems.map(item => ({
        uid: this.makeUID(),
        keyLabel: item.name || '-',
        keyValue: item.name || '',
        type: this.selectedType,
        modType: '',
        qualifier: '',
        required: item.required || false,
        addToProcess: item.required || false,
        compoundKeys: '',
        description: item.description || '',
        maxLength: item.maxLength || '',
        minLength: item.minLength || '',
        project_prompt: { DocClass: '', Field_Description: '', Rules_Description: '' },
      }))

      // Add new keys at the top so user can see them
      this.projectKeysList = [...newKeys, ...this.projectKeysList]

      // Sync to store so top save button will save the keys
      this.$store.dispatch('project/updateKeyItems', this.stripUiFields(this.projectKeysList))

      // Clear selection after copying
      this.selectedItems = []
      this.selectedIds = []
      this.clearTreeSelection()

      // Close modal and reset type
      this.showTypeModal = false
      this.selectedType = 'key'
    },
    stripUiFields(list) {
      return list.map(({ uid, ...rest }) => rest)
    },
    handleUpdateItem({ uid, item }) {
      const index = this.projectKeysList.findIndex(
        k => k.uid === uid,
      )

      if (index !== -1) {
        this.$set(this.projectKeysList, index, item)
        this.$store.dispatch(
          'project/updateKeyItems',
          this.stripUiFields(this.projectKeysList),
        )
      }
    },
    handleDeleteItem(uid) {
      this.projectKeysList = this.projectKeysList.filter(k => k.uid !== uid)
      this.$store.dispatch('project/updateKeyItems', this.stripUiFields(this.projectKeysList))
    },
    goToKeysTab() {
      // Navigate to Keys tab or emit event to parent
      this.$emit('view-all-keys')
    },
    showContextMenu(event) {
      this.contextMenu = {
        show: true,
        x: event.x,
        y: event.y,
        item: event.item,
      }
    },
    hideContextMenu() {
      this.contextMenu.show = false
    },
    openTypeModalFromContext() {
      this.hideContextMenu()
      this.showTypeModal = true
    },
    removeSelectedKeys() {
      this.hideContextMenu()
      // Get all selected IDs
      const selectedIds = this.selectedItems.map(item => item.id)
      // Set hidden flag on selected keys (they stay in place, just hidden via CSS)
      this.treeData = this.setHiddenFlag(this.treeData, selectedIds, true)
      // Clear selection
      this.selectedItems = []
      this.selectedIds = []
      this.clearTreeSelection()
    },
    clearTreeSelection() {
      const treeRef = this.$refs.treeItemRef
      if (Array.isArray(treeRef)) {
        treeRef.forEach(ref => {
          if (ref && ref.clearSelection) ref.clearSelection()
        })
      } else if (treeRef && treeRef.clearSelection) {
        treeRef.clearSelection()
      }
    },
    restoreHiddenKeys() {
      // Remove hidden flag from all keys
      this.treeData = this.setHiddenFlag(this.treeData, null, false)
    },
    setHiddenFlag(nodes, idsToHide, hidden) {
      // If idsToHide is null, apply to all hidden items (for restore)
      return nodes.map(node => {
        const shouldUpdate = idsToHide === null ? node.hidden : idsToHide.includes(node.id)
        return {
          ...node,
          hidden: shouldUpdate ? hidden : node.hidden,
          children: node.children ? this.setHiddenFlag(node.children, idsToHide, hidden) : [],
        }
      })
    },
    countHiddenKeys(nodes) {
      if (!nodes || !nodes.length) return 0
      return nodes.reduce((count, node) => {
        const nodeCount = node.hidden ? 1 : 0
        const childCount = node.children ? this.countHiddenKeys(node.children) : 0
        return count + nodeCount + childCount
      }, 0)
    },
  },
}
</script>

<style scoped>
.tree-container {
  min-height: 200px;
  max-height: auto;
  overflow-y: auto;
  padding: 10px;
}

/* Context Menu Styles */
.context-menu {
  position: fixed;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1050;
  min-width: 150px;
  padding: 4px 0;
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #333;
  transition: background-color 0.15s ease;
}

.context-menu-item:hover {
  background-color: #f5f5f5;
  color: #7367f0;
}

.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1049;
}
</style>

<style lang="scss">
@import '@core/scss/vue/libs/vue-select.scss';
</style>
