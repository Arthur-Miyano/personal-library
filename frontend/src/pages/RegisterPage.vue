<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api'
import gsap from 'gsap'

const router = useRouter()
const store = useAppStore()
const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)

onMounted(() => {
  nextTick(() => {
    gsap.fromTo('#register-card', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6 })
  })
})

async function handleRegister() {
  if (!username.value.trim() || !email.value.trim() || !password.value) {
    ElMessage.warning('请填写所有字段')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.register({
      username: username.value,
      email: email.value,
      password: password.value,
    })
    store.setToken(data.access_token)
    store.setUsername(data.user?.username || username.value)
    gsap.to('#register-card', {
      scale: 0.97, opacity: 0, duration: 0.3,
      onComplete: () => router.replace('/home')
    })
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
    <div class="ink-container">
      <div class="ink-blob"></div>
      <div class="ink-blob"></div>
    </div>

    <div id="register-card" class="glass-card register-card">
      <div class="register-header">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="1.5" :style="{ color: 'var(--primary)' }">
          <path d="M4 20V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2z" />
        </svg>
        <h2 class="register-title">创建账号</h2>
        <p class="register-subtitle">加入藏卷小筑</p>
      </div>

      <div class="register-form">
        <input v-model="username" type="text" placeholder="用户名" class="form-input" />
        <input v-model="email" type="email" placeholder="邮箱" class="form-input" />
        <input v-model="password" type="password" placeholder="密码" class="form-input" />
        <button class="register-btn" :disabled="loading" @click="handleRegister">
          {{ loading ? '注册中...' : '注册并进入' }}
        </button>
      </div>

      <div class="register-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="login-link">登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-base);
  position: relative;
  overflow: hidden;
}
.register-card {
  width: 360px;
  padding: 40px 32px;
  border-radius: 16px;
  position: relative;
  z-index: 10;
}
.register-header {
  text-align: center;
  margin-bottom: 32px;
}
.register-header svg { width: 24px; height: 24px; margin-bottom: 12px; }
.register-title {
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-serif);
  color: var(--text-main);
  letter-spacing: 0.2em;
}
.register-subtitle {
  font-size: 9px;
  color: var(--text-muted);
  margin-top: 6px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-family: var(--font-mono);
}
.register-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 13px;
  background: var(--bg-base);
  color: var(--text-main);
  outline: none;
  transition: border-color 0.2s;
}
.form-input:focus { border-color: var(--primary); }
.form-input::placeholder { color: var(--text-muted); }
.register-btn {
  width: 100%;
  margin-top: 8px;
  padding: 12px;
  border: none;
  border-radius: 10px;
  font-size: 12px;
  letter-spacing: 0.1em;
  color: #fff;
  background: var(--primary);
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}
.register-btn:hover { opacity: 0.9; }
.register-btn:active { transform: scale(0.98); }
.register-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.register-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
.login-link {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}
.login-link:hover { text-decoration: underline; }
</style>
