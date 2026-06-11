import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const nickname = ref(localStorage.getItem('nickname') || '')
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

  async function fetchNickname() {
    try {
      const { data } = await authApi.getProfile()
      if (data.nickname) {
        nickname.value = data.nickname
        localStorage.setItem('nickname', data.nickname)
      }
    } catch { /* 未登录或网络错误 */ }
  }

  async function updateNickname(name: string) {
    nickname.value = name
    localStorage.setItem('nickname', name)
    try { await authApi.updateProfile({ nickname: name }) } catch { /* */ }
  }

  function logout() {
    token.value = ''
    username.value = ''
    nickname.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('nickname')
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    const theme = isDark.value ? 'ink' : 'cinnabar'
    localStorage.setItem('theme', theme)
    document.documentElement.setAttribute('data-theme', theme)
    if (isDark.value) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  }

  return { token, username, nickname, isDark, activeTab, setToken, setUsername, fetchNickname, updateNickname, logout, toggleTheme }
})
