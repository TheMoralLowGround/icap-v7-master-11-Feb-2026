<template>
  <div>
    <div class="mb-2">
      <h3
        class="cursor-pointer d-flex justify-content-between"
        @click="showSearch = !showSearch"
      >
        <span> Search Organizations
          <feather-icon
            :icon="showSearch ? 'ChevronDownIcon' : 'ChevronUpIcon'"
            size="16"
            class="me-1"
          /></span>
        <span @click.stop>
          test
        </span>
      </h3>
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
        Dictionaries
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

    <!-- <div class="d-flex justify-content-between align-items-center mt-2">
      <h3>Parties</h3>
      <b-button
        variant="primary"
        @click="openUpdateParty(false, {})"
      >
        Add Party
      </b-button>
    </div> -->

    <!-- <b-card>
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
                  v-if="field.key !== 'action'"
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
              v-for="item in renderedItems"
              :key="`row-${item.address_id}`"
            >
              <template v-for="field in computedFields">
                <b-td
                  :key="`cell-${field.key}-${item.address_id}`"
                  class="max-w"
                >
                  <template v-if="field.key === 'action'">
                    <div class="d-flex gap-3 justify-content-end">
                      <LookupDetails
                        :id="item.address_id"
                        :item="item"
                        aria-label="View details"
                      />
                      <feather-icon
                        v-b-tooltip.hover
                        title="Edit Party"
                        icon="EditIcon"
                        class="cursor-pointer text-primary"
                        size="16"
                        @click="openUpdateParty(true, item)"
                      />
                      <feather-icon
                        v-b-tooltip.hover
                        title="Email Notifications Settings"
                        icon="SettingsIcon"
                        class="cursor-pointer text-primary"
                        size="16"
                        @click="openEmailSettingsDialog(item)"
                      />
                      <feather-icon
                        v-b-tooltip.hover
                        title="Delete Party"
                        icon="Trash2Icon"
                        class="cursor-pointer text-danger"
                        size="16"
                        @click="deleteItem(item.id, item.address_id)"
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
      <div
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
      </div>
    </b-card>

    <UpdateParty
      v-model="showUpdateParty"
      :is-edit="isEdit"
      :party="currentParty"
      :items="items"
      @submit="handlePartySubmit"
      @close="showUpdateParty = false"
    />

    <email-settings-modal
      v-model="showEmailSettings"
      :initial-data="currentCustomer"
      :current-customer="currentCustomer"
      @submit="saveEmailSettings"
      @close="showEmailSettings = false"
    /> -->
  </div>
</template>

<script>
import { cloneDeep } from 'lodash'
import {
  // BTr,
  // BThead,
  // BTbody,
  // BTh,
  // BTd,
  // BCard,
  // BButton,
  // BTableSimple,
  // BFormInput,
  // BSpinner,
  BCollapse,
} from 'bootstrap-vue'
// import DetailedPagination from '@/components/UI/DetailedPagination.vue'
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
// import EmailSettingsModal from './EmailSettingsModal.vue'
// import LookupDetails from './LookupDetails.vue'
import PartiesSearch from './PartiesSearch.vue'
// import UpdateParty from './UpdateParty.vue'
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
    // BTr,
    // BThead,
    // BTbody,
    // BTh,
    // BTd,
    // BCard,
    // BButton,
    // BTableSimple,
    // BFormInput,
    // BSpinner,
    // DetailedPagination,
    // EmailSettingsModal,
    PartiesSearch,
    // LookupDetails,
    BCollapse,
    // UpdateParty,
    SearchTemplate,
  },
  data() {
    return {
      newParties: false,
      showSearch: false,
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
      fields: [
        { key: 'name', label: 'Name', sortable: true },
        { key: 'org_name', label: 'Organization Name', sortable: true },
        { key: 'account_number', label: 'Account Number', sortable: true },
        { key: 'short_code', label: 'Short Code', sortable: true },
        { key: 'address_line1', label: 'Address Line 1', sortable: true },
        { key: 'address_line2', label: 'Address Line 2', sortable: true },
        { key: 'city', label: 'City', sortable: true },
        { key: 'action', label: 'Actions' },
      ],
      showEmailSettings: false,
      currentCustomer: {},
      filteredItems: [],
    }
  },
  computed: {
    computedFields() {
      return this.fields
    },
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
