<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { settingsApi } from '@/api'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const store = useAppStore()
const route = useRoute()
const splashDone = ref(false)
const splashLeaving = ref(false)

// 从 localStorage 恢复主题
const currentTheme = ref(localStorage.getItem('theme') || 'cinnabar')
document.documentElement.setAttribute('data-theme', currentTheme.value)
if (currentTheme.value === 'ink' || currentTheme.value === 'dark') document.documentElement.classList.add('dark')

function changeTheme(theme: string) {
  currentTheme.value = theme
  document.documentElement.setAttribute('data-theme', theme)
  if (theme === 'ink') document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
  localStorage.setItem('theme', theme)
  settingsApi.update({ theme_mode: theme }).catch(() => {})
}

provide('changeTheme', changeTheme)
provide('currentTheme', currentTheme)

onMounted(() => {
  // 2200ms 后触发开屏离场
  setTimeout(() => {
    splashLeaving.value = true
  }, 2200)
})

function onSplashTransitionEnd() {
  splashDone.value = true
}
</script>

<template>
  <div class="app-root">
    <div class="paper-texture"></div>

    <!-- ====== 开屏动画 ====== -->
    <div
      v-if="!splashDone"
      class="splash-wrap"
      :class="{ 'splash-leave': splashLeaving }"
      @transitionend="onSplashTransitionEnd"
    >
      <div class="splash-inner">
        <!-- 线条 + 圆点 -->
        <div class="line-box">
          <div class="expand-line"></div>
          <div class="dot"></div>
        </div>
        <!-- 标题 -->
        <h1 class="splash-title serif-text">藏卷小筑</h1>
        <!-- 底部小字 -->
        <div class="splash-tip">System Initialization // 2026</div>
      </div>
    </div>

    <!-- ====== 全屏页面（登录/注册） ====== -->
    <router-view v-if="route.meta?.hideSidebar && splashDone" v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>

    <!-- ====== 侧边栏布局页面 ====== -->
    <DefaultLayout v-if="!route.meta?.hideSidebar && splashDone" />
  </div>
</template>

<style>
.app-root { min-height: 100vh; }

/* ========================================
   开屏动画
   ======================================== */
.splash-wrap {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background-color: #FDFBF7;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  user-select: none;
}
.splash-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 320px;
  width: 100%;
  padding: 0 24px;
  text-align: center;
  gap: 24px;
}

/* 线条圆点容器 */
.line-box {
  position: relative;
  width: 64px;
  height: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.expand-line {
  position: absolute;
  height: 1px;
  background-color: #C85D5D;
  animation: expandLine 1.6s ease-in-out forwards;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #C85D5D;
  animation: pulse 2s infinite ease-in-out;
  z-index: 2;
}

/* 标题 */
.splash-title {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.4em;
  color: #2C2421;
  opacity: 0;
  padding-left: 0.4em;
  animation: fadeInTitle 1s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards;
}

/* 底部提示 */
.splash-tip {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.2em;
  color: #8C7A76;
  text-transform: uppercase;
  opacity: 0.4;
  padding-top: 8px;
  animation: pulse 2s infinite ease-in-out;
}

/* 离场过渡 */
.splash-leave {
  transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  opacity: 0;
  transform: scale(1.02);
  pointer-events: none;
}

/* ========================================
   关键帧
   ======================================== */
@keyframes expandLine {
  0%   { width: 0%; opacity: 0; }
  50%  { width: 100%; opacity: 0.7; }
  100% { width: 100%; opacity: 0.2; }
}
@keyframes fadeInTitle {
  0%   { opacity: 0; transform: translateY(8px); filter: blur(2px); }
  100% { opacity: 1; transform: translateY(0); filter: blur(0); }
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.6; transform: scale(0.9); }
}
</style>
