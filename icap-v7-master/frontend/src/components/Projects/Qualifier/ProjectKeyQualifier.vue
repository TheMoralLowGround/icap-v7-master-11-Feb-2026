<template>
  <div>
    <b-card
      v-for="(item, idx) in items"
      :key="idx"
      no-body
      class="mb-2"
    >
      <b-card-header
        header-tag="header"
        class="d-flex justify-content-between align-items-center"
      >
        <b-button
          variant="link"
          class="text-left p-0 flex-grow-1 text-decoration-none"
          @click="toggleCollapse(idx)"
        >
          {{ item.name || `Qualifier ${idx + 1}` }}
        </b-button>

        <feather-icon
          v-b-tooltip.hover
          icon="TrashIcon"
          size="18"
          class="cursor-pointer"
          title="Delete Qualifier"
          @click="deleteItem(idx)"
        />
      </b-card-header>

      <b-collapse
        :id="`collapse-${idx}`"
        :visible="activeCollapse === idx"
      >
        <b-card-body>
          <b-form-group label="Qualifier Name">
            <b-form-input
              v-model="item.name"
              placeholder="Enter Qualifier Name"
              @blur="trimQualifierName(idx)"
            />
          </b-form-group>

          <project-key-qualifier-table :qualifier-name="item.name" />
        </b-card-body>
      </b-collapse>
    </b-card>
  </div>
</template>

<script>
import bus from '@/bus'
import {
  BButton,
  BCard,
  BCardBody,
  BCardHeader,
  BCollapse,
  BFormGroup,
  BFormInput,
  VBToggle,
  VBTooltip,
} from 'bootstrap-vue'
import ProjectKeyQualifierTable from './ProjectKeyQualifierTable.vue'

export default {
  name: 'ProjectKeyQualifier',
  components: {
    BCard,
    BCardBody,
    BCardHeader,
    BCollapse,
    BFormInput,
    BFormGroup,
    BButton,
    ProjectKeyQualifierTable,
  },

  directives: {
    'b-toggle': VBToggle,
    'b-tooltip': VBTooltip,
  },

  props: {
    tableHeight: {
      type: [String, Number],
      default: 500,
    },
  },

  data() {
    return {
      activeCollapse: null,
    }
  },
  computed: {
    items() {
      return this.$store.getters['project/keyQualifiers']
    },
  },

  created() {
    bus.$on('project:add-key-qualifier', this.addItem)
  },

  beforeDestroy() {
    bus.$off('project:add-key-qualifier', this.addItem)
  },

  methods: {
    toggleCollapse(idx) {
      this.activeCollapse = this.activeCollapse === idx ? null : idx
    },

    addItem() {
      const nextIndex = this.items.length + 1
      this.$store.dispatch('project/addKeyQualifier', nextIndex)
      this.activeCollapse = this.items.length - 1 // open the newly added item
    },

    deleteItem(index) {
      if (this.activeCollapse === index) this.activeCollapse = null
      this.$store.commit('project/REMOVE_KEY_QUALIFIER', index)
    },

    trimQualifierName(idx) {
      if (this.items[idx] && this.items[idx].name) {
        this.items[idx].name = this.items[idx].name.trim()
      }
    },
  },
}
</script>
