<template>
  <div>
    <b-card
      v-for="(item, idx) in compoundKeys"
      :key="idx"
      no-body
      class="mb-2"
    >
      <b-card-header class="d-flex justify-content-between align-items-center">
        <b-button
          variant="link"
          class="text-left p-0 flex-grow-1 text-decoration-none"
          @click="toggleCollapse(idx)"
        >
          {{ item.name || `Compound Key ${idx + 1}` }}
        </b-button>

        <feather-icon
          v-b-tooltip.hover
          icon="TrashIcon"
          size="18"
          class="cursor-pointer"
          title="Delete Compound Key"
          @click="deleteItem(idx)"
        />
      </b-card-header>

      <b-collapse
        :id="`collapse-${idx}`"
        :visible="activeCollapse === idx"
      >
        <b-card-body>
          <b-form-group label="Compound Key Name">
            <b-form-input
              v-model="item.name"
              placeholder="Enter Compound Key Name"
              @blur="trimCompoundKeyName(idx)"
            />
          </b-form-group>

          <project-compound-table :compound-key-name="item.name" />
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
  VBTooltip,
} from 'bootstrap-vue'
import ProjectCompoundTable from './ProjectCompoundTable.vue'

export default {
  name: 'ProjectCompoundKeys',

  components: {
    BCard,
    BCardBody,
    BCardHeader,
    BCollapse,
    BFormInput,
    BFormGroup,
    BButton,
    ProjectCompoundTable,
  },

  directives: {
    'b-tooltip': VBTooltip,
  },

  data() {
    return {
      activeCollapse: null,
    }
  },

  computed: {
    compoundKeys() {
      return this.$store.getters['project/compoundKeys']
    },
  },
  created() {
    bus.$on('project:add-compound-key', this.addItem)
  },

  beforeDestroy() {
    bus.$off('project:add-compound-key', this.addItem)
  },
  methods: {
    toggleCollapse(idx) {
      this.activeCollapse = this.activeCollapse === idx ? null : idx
    },

    addItem() {
      const nextIndex = this.compoundKeys.length + 1
      this.$store.dispatch('project/addCompoundKeys', nextIndex)
      this.activeCollapse = this.compoundKeys.length // open the newly added item
    },

    deleteItem(index) {
      if (this.activeCollapse === index) {
        this.activeCollapse = null
      }
      this.$store.commit('project/REMOVE_COMPOUND_KEYS', index)
    },

    trimCompoundKeyName(idx) {
      if (this.compoundKeys[idx] && this.compoundKeys[idx].name) {
        this.compoundKeys[idx].name = this.compoundKeys[idx].name.trim()
      }
    },
  },
}
</script>
