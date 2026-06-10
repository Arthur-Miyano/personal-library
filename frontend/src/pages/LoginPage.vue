<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api'

const router = useRouter()
const store = useAppStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function doLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.login({ username: username.value, password: password.value })
    store.setToken(data.access_token)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <h1 class="logo">个人图书馆</h1>
    <el-input v-model="username" placeholder="用户名或邮箱" size="large" clearable />
    <el-input v-model="password" type="password" placeholder="密码" size="large" show-password @keyup.enter="doLogin" />
    <el-button type="primary" size="large" :loading="loading" block @click="doLogin">登录</el-button>
    <p class="switch-link">还没有账号？<router-link to="/register">注册</router-link></p>
  </div>
</template>

<style scoped>
.login-page { display: flex; flex-direction: column; gap: 16px; justify-content: center; min-height: 100vh; max-width: 320px; margin: 0 auto; padding: 40px 20px; }
.logo { text-align: center; font-size: 28px; font-weight: 300; margin-bottom: 32px; }
.switch-link { text-align: center; font-size: 14px; color: var(--el-text-color-secondary); }
</style>
