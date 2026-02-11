import Vue from 'vue'
import Vuex from 'vuex'

// Modules
import app from './app'
import appConfig from './app-config'
import applicationSettings from './application-settings'
import atm from './atm'
import auth from './auth'
import batch from './batch'
import classifications from './classifications'
import dataView from './data-view'
import defaultSettings from './default-settings'
import definitionSettings from './definition-settings'
import developerSettings from './developer-settings'
import lookup from './lookup'
import project from './project'
import theme from './theme'
import verticalMenu from './vertical-menu'
import profile from './profile'

Vue.use(Vuex)

// Note: Auth state is NOT persisted to localStorage/sessionStorage for security.
// Auth is managed via HttpOnly cookies - server is the source of truth.
// User data is fetched from server on each page load.
export default new Vuex.Store({
  modules: {
    app,
    appConfig,
    applicationSettings,
    definitionSettings,
    developerSettings,
    defaultSettings,
    verticalMenu,
    dataView,
    batch,
    auth,
    theme,
    lookup,
    atm,
    classifications,
    project,
    profile,
  },
  strict: process.env.DEV,
})
