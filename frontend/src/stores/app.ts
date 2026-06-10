import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('token') || '')
  const isDark = ref(localStorage.getItem('theme') === 'dark')
  const activeTab = ref('home')

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = ''
    localStorage.removeItem('token')
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  return { token, isDark, activeTab, setToken, logout, toggleTheme }
})
