/**
 * Organization: AIDocbuilder Inc.
 * File: classifications/index.js
 * Version: 6.0
 *
 * Authors:
 *   - Vinay: Initial implementation
 *   - Ali: Code optimization
 *
 * Last Updated By: Ali
 * Last Updated At: 2024-12-02
 *
 * Description:
 *   This file serves as the Vuex store module for managing classifications-batch-related data in the application.
 *
 * Dependencies:
 *   - None (or specify if any external libraries are used)
 *
 * Main Features:
 *   - Define the default state and initialize its values.
 *   - Implement mutations and getters for state management.
 *   - Write action methods to handle asynchronous operations.
 *   - Integrate and bind APIs for classifications batch data.
 */

// Importing dependencies
import axios from 'axios' // For making HTTP requests
import Vue from 'vue' // For interacting with Vue.js features
import ToastificationContent from '@core/components/toastification/ToastificationContent.vue' // Custom toast notification component

// Exporting a Vuex module to manage the state of classification-related data
export default {
  namespaced: true, // Namespacing this module for modular Vuex store
  state: {
    classificationData: {}, // Stores classification data fetched from the server
    classificationRaJosn: {}, // Stores additional classification JSON data
    verified: false, // Flag to track if the classification is verified
    test: false, // Flag to track if the classification test was run
    newCreatedTrainID: '', // Stores the ID of a newly created train batch
    fetchedImages: [], // List of images fetched for display or processing
  },

  // Getters to access the state properties
  getters: {
    getClassificationData(state) {
      return state.classificationData
    },
    getClassificationRaJosn(state) {
      return state.classificationRaJosn
    },
    getVerified(state) {
      return state.verified
    },
    // Get all documents that have a '.pdf' extension, from classificationRaJosn
    getAlldocs(state) {
      const docs = []
      if (state.classificationRaJosn) {
        state.classificationRaJosn.nodes.forEach(element => {
          if (element.ext === '.pdf') {
            element.children.forEach(el => {
              docs.push(el) // Push all child elements of PDF files
            })
          }
        })
      }
      return docs
    },
    getNewCreatedTrainID(state) {
      return state.newCreatedTrainID
    },
    getFetchedImages(state) {
      return state.fetchedImages
    },
  },

  // Mutations to modify the state properties
  mutations: {
    // Sets the classification data in the state
    SET_CLASSIFICATION_DATA(state, value) {
      state.classificationData = value
    },
    // Sets the classificationRaJosn data in the state
    SET_CLASSIFICATION_RAJSON(state, value) {
      state.classificationRaJosn = value
    },
    // Sets the test flag
    SET_Test(state, value) {
      state.test = value
    },
    // Sets the verification flag
    SET_VERIFIED(state, value) {
      state.verified = value
    },
    // Sets the ID for the newly created train batch
    SET_NEW_CREATED_TRAIN_ID(state, value) {
      state.newCreatedTrainID = value
    },
    // Modifies an image in the fetched image list based on its index
    MODIFY_FETCHED_IMAGE_LIST(state, value) {
      const images = [...state.fetchedImages] // Clone the current list of images
      images[value.index] = value // Update the image at the specified index
      state.fetchedImages = images // Update the state with the modified list
    },
  },

  // Actions to perform asynchronous tasks
  actions: {
    // Fetches classification data in JSON format using the batch ID
    async fetchRaJsonClassification({ commit }, batchId) {
      try {
        const res = await axios.get('/get_train_batch_ra_json/', {
          params: { batch_id: batchId },
        })
        commit('SET_CLASSIFICATION_RAJSON', res.data) // Commit the fetched data to the store

        return false
      } catch {
        return false
      }
    },

    // Fetches manual classification data using the batch ID
    async fetchManualClassification({ commit }, batchId) {
      try {
        const res = await axios.get('/pipeline/get_manual_classification_data/', {
          params: { train_batch_id: batchId },
        })
        commit('SET_VERIFIED', false) // Reset the verified status
        commit('SET_CLASSIFICATION_DATA', res.data) // Commit the fetched data to the store

        return false
      } catch {
        return false
      }
    },

    // Tests the manual classification using the classification data and batch ID
    async testClassification({ state, commit }, batchId) {
      try {
        const res = await axios.post('/pipeline/test_manual_classification/', {
          train_batch_id: batchId,
          profile: state.classificationData.profile,
          manual_classification_data: state.classificationData.data,
        })
        commit('SET_VERIFIED', true) // Set the verified status to true
        commit('SET_CLASSIFICATION_DATA', {
          ...state.classificationData,
          data: res.data, // Update the classification data with the test result
        })
        commit('SET_Test', res) // Store the test result
        // Display a success toast notification
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: 'Classification testing successful',
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
        return false
      } catch (err) {
        // Display a failure toast notification if an error occurs
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: 'Classification testing failed',
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
        return false
      }
    },

    // Verifies the manual classification using the batch ID and classification data
    async verifyClassification({ state, commit, dispatch }, data) {
      try {
        const { train_batch_id, forceSubmit } = data

        if (forceSubmit) {
          await dispatch('fetchManualClassification', train_batch_id)
        }

        const res = await axios.post('/pipeline/verify_manual_classification/', {
          train_batch_id,
          profile: state.classificationData.profile,
          manual_classification_data: state.classificationData.data,
        })
        commit('SET_Test', res) // Store the verification result
        // Display a success toast notification with the verification result
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: res.data.detail,
            icon: 'CheckIcon',
            variant: 'success',
          },
        })
        return true
      } catch (err) {
        // Display a failure toast notification if an error occurs
        Vue.$toast({
          component: ToastificationContent,
          props: {
            title: err,
            icon: 'AlertTriangleIcon',
            variant: 'danger',
          },
        })
      }
      return false
    },
  },
}
