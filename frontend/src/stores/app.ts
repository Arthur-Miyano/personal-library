import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const isDark = ref(localStorage.getItem('theme') === 'ink' || localStorage.getItem('theme') === 'dark')
  const activeTab = ref('home')

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setUsername(name: string) {
    username.value = name
    localStorage.setItem('username', name)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    const theme = isDark.value ? 'ink' : 'cinnabar'
    localStorage.setItem('theme', theme)
    document.documentElement.setAttribute('data-theme', theme)
    if (isDark.value) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  }

  return { token, username, isDark, activeTab, setToken, setUsername, logout, toggleTheme }
})
