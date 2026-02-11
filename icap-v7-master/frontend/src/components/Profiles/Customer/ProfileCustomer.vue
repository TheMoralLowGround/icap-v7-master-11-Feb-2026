<template>
  <div>
    <div class="mb-2 d-flex justify-content-between">
      <h3
        class="cursor-pointer align-items-center"
        @click="showSearch = !showSearch"
      >
        <span> Search Organizations
          <feather-icon
            :icon="showSearch ? 'ChevronDownIcon' : 'ChevronUpIcon'"
            size="16"
            class="me-1"
          /></span>

      </h3>
      <span
        @click.stop
      >
        <b-form-checkbox
          v-model="useSemanticDataSearch"
          switch
          size="md"
          title="Use Semantic Data Search"
        >
          <span>Use Semantic Data Search</span>
        </b-form-checkbox>

      </span>
    </div>

    <b-collapse
      v-model="showSearch"
      class="mb-3"
    >
      <PartiesSearch @items-selected="addFromDb" />
      <hr>
    </b-collapse>
    <div class="mb-4">
      <h3
        class="cursor-pointer"
        @click="newParties = !newParties"
      >
        Party List
        <feather-icon
          :icon="newParties ? 'ChevronDownIcon' : 'ChevronUpIcon'"
          size="16"
          class="me-1"
        />
      </h3>
      <b-collapse
        v-model="newParties"
        class="mb-3"
      >
        <SearchTemplate />
      </b-collapse>

    </div>
  </div>
</template>

<script>
import { cloneDeep } from 'lodash'
import {
  BCollapse,
  BFormCheckbox,
} from 'bootstrap-vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'

import PartiesSearch from './PartiesSearch.vue'
import SearchTemplate from './SearchTemplate.vue'

export default {
  directives: {
    'b-tooltip': {
      bind(el, binding) {
        el.setAttribute('title', binding.value)
      },
    },
  },
  components: {
    PartiesSearch,
    BCollapse,
    BFormCheckbox,
    SearchTemplate,
  },
  data() {
    return {
      newParties: false,
      showSearch: false,
      useSemanticDataSearch: false,
      loading: false,
      searchableItems: [],
      renderedItems: [],
      currentPage: 1,
      perPage: 10,
      searchFields: {
        name: '',
        account_number: '',
        short_code: '',
        address_line1: '',
        address_line2: '',
        city: '',
      },
      isEdit: false,
      currentParty: {},
      showUpdateParty: false,
      sortField: 'name',
      sortDesc: false,
      showEmailSettings: false,
      currentCustomer: {},
      filteredItems: [],
    }
  },
  computed: {
    items() {
      return this.$store.state.profile.customers || []
    },
    totalRecords() {
      return this.searchableItems.length
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
  },
  methods: {
    addFromDb(parties) {
      if (!parties || !Array.isArray(parties) || parties.length === 0) {
        this.$bvToast.toast('No parties selected', {
          variant: 'warning',
          solid: true,
        })
        return
      }

      let addedCount = 0
      let duplicateCount = 0

      parties.forEach(party => {
        const isDuplicate = this.items.some(existingItem => existingItem.name?.trim().toLowerCase() === party.org_name?.trim().toLowerCase())

        if (isDuplicate) {
          duplicateCount += 1
          return
        }

        const otherPartyData = { ...party }
        delete otherPartyData.cw1_code
        delete otherPartyData.country_code_dup

        const partyData = {
          name: party.org_name || '',
          account_number: party.cw1_code || '',
          address_line1: party.address_line1 || '',
          address_line2: party.address_line2 || '',
          city: party.city || '',
          org_name: party.org_name || '',
          success_notification_with_same_subject: party.success_notification_with_same_subject || false,
          success_notification_subject: party.success_notification_subject || '',
          success_notify_email_sender: party.success_notify_email_sender || false,
          success_notify_email_recipients: party.success_notify_email_recipients || false,
          success_notify_cc_users: party.success_notify_cc_users || false,
          success_notify_additional_emails: party.email || '',
          failure_notification_with_same_subject: party.failure_notification_with_same_subject || false,
          failure_notification_subject: party.failure_notification_subject || '',
          failure_notify_email_sender: party.failure_notify_email_sender || false,
          failure_notify_email_recipients: party.failure_notify_email_recipients || false,
          failure_notify_cc_users: party.failure_notify_cc_users || false,
          failure_notify_additional_emails: party.email || '',
          ...otherPartyData,
        }
        this.$store.commit('profile/addCustomer', partyData)
        addedCount += 1
      })

      this.setInitialState()

      if (addedCount > 0) {
        this.$bvToast.toast(`${addedCount} ${addedCount === 1 ? 'party' : 'parties'} added successfully`, {
          variant: 'success',
          title: 'Success',
          solid: true,
        })
      }

      if (duplicateCount > 0) {
        this.$bvToast.toast(`${duplicateCount} ${duplicateCount === 1 ? 'party was' : 'parties were'} skipped (already exists)`, {
          variant: 'warning',
          title: 'Warning',
          solid: true,
        })
      }

      if (addedCount === 0 && duplicateCount === 0) {
        this.$bvToast.toast('No valid parties to add', {
          variant: 'info',
          solid: true,
        })
      }
    },
    async saveEmailSettings(emailSettings) {
      try {
        const updatedCustomer = {
          ...this.currentCustomer,
          ...emailSettings,
        }

        const index = this.items.findIndex(c => (c.id && c.id === this.currentCustomer.id)
          || c.address_id === this.currentCustomer.address_id)

        if (index !== -1) {
          this.$store.commit('profile/updateCustomer', {
            index,
            customer: updatedCustomer,
          })

          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Email settings saved successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
        }

        this.showEmailSettings = false
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Error saving email settings:', error)
        this.$bvToast.toast('Failed to save email settings', {
          variant: 'danger',
          solid: true,
        })
      }
    },
    openEmailSettingsDialog(customer) {
      const completeCustomer = this.items.find(item => (item.id && item.id === customer.id)
        || item.address_id === customer.address_id) || customer
      this.currentCustomer = {
        ...completeCustomer,
        success_notification_with_same_subject: completeCustomer?.success_notification_with_same_subject || false,
        success_notification_subject: completeCustomer?.success_notification_subject || '',
        success_notify_email_sender: completeCustomer?.success_notify_email_sender || false,
        success_notify_email_recipients: completeCustomer?.success_notify_email_recipients || false,
        success_notify_cc_users: completeCustomer?.success_notify_cc_users || false,
        success_notify_additional_emails: completeCustomer?.success_notify_additional_emails || '',
        failure_notification_with_same_subject: completeCustomer?.failure_notification_with_same_subject || false,
        failure_notification_subject: completeCustomer?.failure_notification_subject || '',
        failure_notify_email_sender: completeCustomer?.failure_notify_email_sender || false,
        failure_notify_email_recipients: completeCustomer?.failure_notify_email_recipients || false,
        failure_notify_cc_users: completeCustomer?.failure_notify_cc_users || false,
        failure_notify_additional_emails: completeCustomer?.failure_notify_additional_emails || '',
      }
      this.showEmailSettings = true
    },
    pageChanged(page) {
      this.currentPage = page
      this.applyPagination()
    },
    handlePartySubmit(customerData) {
      if (this.isEdit) {
        const index = this.items.findIndex(item => (customerData.id && item.id === customerData.id) || item.address_id === customerData.address_id)
        if (index !== -1) {
          this.$store.commit('profile/updateCustomer', {
            index,
            customer: customerData,
          })
          this.$toast({
            component: ToastificationContent,
            props: {
              title: 'Party updated successfully',
              icon: 'CheckIcon',
              variant: 'success',
            },
          })
        }
      } else {
        this.$store.commit('profile/addCustomer', customerData)
        this.$toast({
          component: ToastificationContent,
          props: {
            title: 'Party added successfully',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
      }
      this.setInitialState()
      this.showUpdateParty = false
    },
    openUpdateParty(isEdit, item) {
      this.isEdit = isEdit
      this.currentParty = cloneDeep(item)
      this.showUpdateParty = true
    },
    deleteItem(id, addressId) {
      const index = this.items.findIndex(item => {
        // First try to match by ID if both exist and are real (not generated timestamps)
        if (id && item.id && item.id === id) {
          return true
        }
        // For locally added items or when ID matching fails, use address_id
        if (addressId && item.address_id === addressId) {
          return true
        }
        return false
      })

      if (index !== -1) {
        this.$store.commit('profile/removeCustomer', index)
        this.setInitialState()

        // Adjust pagination if needed
        if (this.renderedItems.length <= (this.currentPage - 1) * this.perPage) {
          this.currentPage = Math.max(1, Math.ceil(this.filteredItems.length / this.perPage))
        }
      }
    },
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
    onColumnSearch() {
      this.loading = true
      const filteredItems = cloneDeep(this.searchableItems)
      const activeSearches = Object.entries(this.searchFields)?.filter(
        ([, value]) => value !== '' && value !== null && value !== undefined,
      )

      let result = activeSearches.length
        ? filteredItems.filter(item => activeSearches
          .every(([key, searchValue]) => item[key]?.toString()
            .toLowerCase().includes(searchValue.toLowerCase())))
        : filteredItems

      if (this.sortField) {
        result = result.sort((a, b) => {
          const aValue = a[this.sortField]?.toString().toLowerCase()
          const bValue = b[this.sortField]?.toString().toLowerCase()
          if (aValue < bValue) return this.sortDesc ? 1 : -1
          if (aValue > bValue) return this.sortDesc ? -1 : 1
          return 0
        })
      }
      this.filteredItems = result
      // Adjust currentPage to ensure it doesn't exceed the maximum page
      const maxPage = Math.max(1, Math.ceil(this.filteredItems.length / this.perPage))
      this.currentPage = Math.min(this.currentPage, maxPage)
      this.applyPagination()
      this.loading = false
    },
    applyPagination() {
      const start = (this.currentPage - 1) * this.perPage
      const end = start + this.perPage
      this.renderedItems = this.filteredItems.slice(start, end)
    },
    setInitialState() {
      this.searchableItems = cloneDeep(this.items.map(item => ({
        ...item,
      })))
      this.filteredItems = [...this.searchableItems]
      this.applyPagination()
    },
  },
}
</script>
<style scoped>
.max-w {
  max-width: 500px;
  overflow-wrap: break-word;
  white-space: normal;
}
</style>
