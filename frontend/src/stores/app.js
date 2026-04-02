import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const sidebarCollapsed = ref(false)
  const theme = ref(localStorage.getItem('theme') || 'light')
  const loading = ref(false)
  const alerts = ref([])

  // Actions
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed) {
    sidebarCollapsed.value = collapsed
  }

  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  function toggleTheme() {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  function setLoading(isLoading) {
    loading.value = isLoading
  }

  function addAlert(alert) {
    alerts.value.unshift(alert)
  }

  function removeAlert(alertId) {
    const index = alerts.value.findIndex(a => a.id === alertId)
    if (index !== -1) {
      alerts.value.splice(index, 1)
    }
  }

  function clearAlerts() {
    alerts.value = []
  }

  // Initialize theme
  if (theme.value) {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  return {
    // State
    sidebarCollapsed,
    theme,
    loading,
    alerts,
    // Actions
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    toggleTheme,
    setLoading,
    addAlert,
    removeAlert,
    clearAlerts
  }
})
