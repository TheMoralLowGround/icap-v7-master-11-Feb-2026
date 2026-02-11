<template>
  <draggable
    v-if="children && children.length"
    class="drag-area"
    tag="ul"
    :list="children"
    :group="{ name: 'g1' }"
  >
    <li
      v-for="el in children"
      :key="el.id"
      :class="{ 'hidden-node': el.hidden }"
    >
      <div
        class="node-content"
        :class="{
          selected: isSelected(el.id),
          'text-danger':el.required
        }"
        @click="toggleSelect(el, !isSelected(el.id))"
        @contextmenu.prevent="handleRightClick($event, el)"
      >
        <!-- Checkbox for selection -->
        <input
          type="checkbox"
          :checked="isSelected(el.id)"
          class="node-checkbox mr-1"
        >
        <!-- Arrow icon for items with children (expandable) -->
        <feather-icon
          v-if="hasChildren(el)"
          :icon="isExpanded(el.id) ? 'ChevronDownIcon' : 'ChevronRightIcon'"
          size="20"
          class="toggle-icon mr-1"
          @click.stop="toggleExpand(el.id)"
        />
        <!-- Spacer for leaf nodes to align with parent nodes -->
        <span
          v-else
          class="toggle-spacer"
        />
        <span class="node-name">{{ el.name || '-' }}</span>
        <!-- Show maxLength if available -->
        <!-- <span
          v-if="el.maxLength !== undefined && el.maxLength !== null"
          class="node-meta text-muted ml-2"
        >
          [max: {{ el.maxLength }}]
        </span> -->
        <!-- Show example if available -->
        <!-- <span
          v-if="el.example !== undefined && el.example !== null && el.example !== ''"
          class="node-example text-muted ml-2"
        >
          e.g. "{{ el.example }}"
        </span> -->
      </div>

      <!-- Only render children if expanded -->
      <tree-item
        v-if="hasChildren(el) && isExpanded(el.id)"
        ref="childTree"
        :children="el.children"
        :selected-ids="localSelectedIds"
        @selection-changed="items => handleChildSelection(items, el)"
        @context-menu="$emit('context-menu', $event)"
      />
    </li>
  </draggable>
</template>

<script>
import draggable from 'vuedraggable'

export default {
  name: 'TreeItem',
  components: {
    draggable,
  },
  props: {
    children: {
      type: Array,
      default: () => [],
    },
    selectedIds: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      expandedIds: [],
      localSelectedIds: [],
    }
  },
  computed: {
    allSelectedIds() {
      // Use localSelectedIds as the source of truth
      return this.localSelectedIds
    },
  },
  watch: {
    selectedIds: {
      immediate: true,
      deep: true,
      handler(newVal) {
        // Sync with parent's selectedIds
        this.localSelectedIds = newVal ? [...newVal] : []
      },
    },
  },
  created() {
    // Expand all items by default
    this.expandAll()
  },
  methods: {
    hasChildren(item) {
      return item && item.children && item.children.length > 0
    },
    isExpanded(id) {
      return id !== undefined && id !== null && this.expandedIds.includes(id)
    },
    isSelected(id) {
      return id !== undefined && id !== null && this.localSelectedIds.includes(id)
    },
    toggleExpand(id) {
      if (id === undefined || id === null) return
      const index = this.expandedIds.indexOf(id)
      if (index > -1) {
        this.expandedIds.splice(index, 1)
      } else {
        this.expandedIds.push(id)
      }
    },
    toggleSelect(item, checked) {
      if (!item || item.id === undefined || item.id === null) return

      // Get all descendant IDs including the item itself
      const itemsToToggle = [item.id, ...this.getAllDescendantIds(item)]

      if (checked) {
        // Add all items that aren't already selected
        itemsToToggle.forEach(id => {
          if (!this.localSelectedIds.includes(id)) {
            this.localSelectedIds.push(id)
          }
        })
      } else {
        // Remove all items
        this.localSelectedIds = this.localSelectedIds.filter(id => !itemsToToggle.includes(id))
      }

      // Emit selected items (full objects) to parent
      this.emitSelectionChanged()
    },
    getAllDescendantIds(item) {
      const ids = []
      if (item && item.children && item.children.length) {
        item.children.forEach(child => {
          if (child.id !== undefined && child.id !== null && !child.hidden) {
            ids.push(child.id)
            ids.push(...this.getAllDescendantIds(child))
          }
        })
      }
      return ids
    },
    handleChildSelection(childSelectedItems, parentEl) {
      // When child emits selection change, update our local state
      // Get IDs from child's selection
      const childSelectedIds = childSelectedItems.map(item => item.id)

      // Get IDs only from the specific subtree that emitted the event (not all children)
      const subtreeIds = this.getSubtreeIds(parentEl)

      // Update localSelectedIds: keep selections outside this subtree, add child selections
      const nonSubtreeIds = this.localSelectedIds.filter(id => !subtreeIds.includes(id))
      this.localSelectedIds = [...nonSubtreeIds, ...childSelectedIds]

      // Emit upward
      this.emitSelectionChanged()
    },
    getSubtreeIds(item) {
      // Get all IDs from a specific item's subtree (children only, not the item itself)
      const ids = []
      const collectIds = items => {
        if (!items) return
        items.forEach(child => {
          if (child.id !== undefined && child.id !== null) {
            ids.push(child.id)
          }
          if (child.children && child.children.length) {
            collectIds(child.children)
          }
        })
      }
      if (item && item.children) {
        collectIds(item.children)
      }
      return ids
    },
    getAllChildDataIds() {
      // Get all IDs from the children tree data
      const ids = []
      const collectIds = items => {
        if (!items) return
        items.forEach(item => {
          if (item.id !== undefined && item.id !== null) {
            ids.push(item.id)
          }
          if (item.children && item.children.length) {
            collectIds(item.children)
          }
        })
      }
      collectIds(this.children)
      return ids
    },
    emitSelectionChanged() {
      const selectedItems = this.collectAllSelectedItems(this.children)
      this.$emit('selection-changed', selectedItems)
    },
    collectAllSelectedItems(items) {
      const selected = []
      if (!items) return selected

      items.forEach(item => {
        if (this.isSelected(item.id)) {
          selected.push(item)
        }
        if (item.children && item.children.length) {
          selected.push(...this.collectAllSelectedItems(item.children))
        }
      })
      return selected
    },
    expandAll() {
      // Expand all items that have children
      if (!this.children || !this.children.length) return
      this.expandedIds = this.children
        .filter(el => this.hasChildren(el) && el.id !== undefined && el.id !== null)
        .map(el => el.id)
    },
    clearSelection() {
      this.localSelectedIds = []
      this.$emit('selection-changed', [])
    },
    handleRightClick(event, item) {
      // Select the item if not already selected
      if (!this.isSelected(item.id)) {
        this.toggleSelect(item, true)
      }
      // Emit context menu event with position and item
      this.$emit('context-menu', {
        x: event.clientX,
        y: event.clientY,
        item,
      })
    },
  },
}
</script>

<style scoped>
.drag-area {
  min-height: 10px;
  list-style-type: none;
  padding-left: 20px;
  /* border-left: 1px dashed #ddd; */
}
.node-content {
  padding: 5px 8px;
  background: #f8f8f9;
  margin: 2px 0;
  border-radius: 4px;
  cursor: move;
  display: flex;
  align-items: center;
  transition: background-color 0.2s ease, border 0.2s ease;
}

/* when selected */
.node-content.selected {
  background: #e7e5ff;
  border-left: 4px solid #7367f0;
}
.node-checkbox {
  display: none;
}
.toggle-icon {
  cursor: pointer;
  transition: transform 0.2s ease;
}
.toggle-icon:hover {
  color: #7367f0;
}
.toggle-spacer {
  display: inline-block;
  width: 16px;
  margin-right: 0.25rem;
}
.node-name {
  font-weight: 500;
}
.node-meta {
  font-size: 0.8em;
  color: #6c757d;
}
.node-example {
  font-size: 0.8em;
  font-style: italic;
  color: #888;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.node-checkbox {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #7367f0;
}
.hidden-node {
  display: none;
}
</style>
