<template>
  <b-modal
    v-model="showModal"
    centered
    title="Delete Template"
    @hidden="$emit('modal-closed')"
    @ok="confirmHandler"
  >
    <!-- <b-card-text>
      <div>
        Are you sure you want to delete the template <span class="text-primary">{{ id }}</span>?
      </div>

    </b-card-text> -->
    <b-card-text>
      <div v-if="list.length === 1">
        Are you sure you want to delete the template <span class="text-primary">{{ list[0].template_name }}</span>?
      </div>
      <div v-else>
        Are you sure you want to delete the following templates?
        <div
          v-for="(id, index) of list"
          :key="index"
          class="text-primary"
        >
          {{ id.name }}
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
        variant="danger"
        :disabled="isDeleting"
        @click="ok()"
      >
        Delete
        <b-spinner
          v-if="isDeleting"
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
  BModal, BCardText, BButton, BSpinner,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

export default {
  components: {
    BModal,
    BCardText,
    BButton,
    BSpinner,
  },
  props: {
    list: {
      type: Array,
      required: true,
    },
    // showModal: {
    //   type: Boolean,
    //   required: false,
    // },
  },
  data() {
    return {
      showModal: true,
      isDeleting: false,
    }
  },
  methods: {
    confirmHandler(event) {
      event.preventDefault()
      this.isDeleting = true
      const ids = this.list.map(item => item.id)
      axios.delete('/dashboard/template', {
        data: {
          ids,
        },
      })
        .then(() => {
          this.$emit('deleted')

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Template deleted sucessfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })

          this.showModal = false
        })
        .catch(error => {
          this.$toast({
            component: ToastificationContent,
            props: {
              title: error?.response?.data?.detail || 'Somthing went wrong',
              icon: 'AlertTriangleIcon',
              variant: 'danger',
            },
          })

          this.isDeleting = false
        })
    },
  },
}

</script>
