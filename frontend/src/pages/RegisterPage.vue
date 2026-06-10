<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api'

const router = useRouter()
const store = useAppStore()
const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)

async function doRegister() {
  if (!username.value || !email.value || !password.value) {
    ElMessage.warning('请填写所有字段')
    return
  }
  if (password.value.length < 6) {
    ElMessage.warning('密码至少6位')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.register({ username: username.value, email: email.value, password: password.value })
    store.setToken(data.access_token)
    ElMessage.success('注册成功')
    router.push('/home')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <h1 class="logo">创建账号</h1>
    <el-input v-model="username" placeholder="用户名" size="large" clearable />
    <el-input v-model="email" placeholder="邮箱" size="large" clearable />
    <el-input v-model="password" type="password" placeholder="密码（至少6位）" size="large" show-password @keyup.enter="doRegister" />
    <el-button type="primary" size="large" :loading="loading" block @click="doRegister">注册</el-button>
    <p class="switch-link">已有账号？<router-link to="/login">登录</router-link></p>
  </div>
</template>

<style scoped>
.register-page { display: flex; flex-direction: column; gap: 16px; justify-content: center; min-height: 100vh; max-width: 320px; margin: 0 auto; padding: 40px 20px; }
.logo { text-align: center; font-size: 28px; font-weight: 300; margin-bottom: 32px; }
.switch-link { text-align: center; font-size: 14px; color: var(--el-text-color-secondary); }
</style>
