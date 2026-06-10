<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { UserFilled, Setting, DataAnalysis, Delete, InfoFilled, ArrowRight, Reading } from '@element-plus/icons-vue'

const router = useRouter()
const store = useAppStore()
</script>

<template>
  <div class="mine-page">
    <div class="profile-card lofter-card">
      <el-icon size="40"><UserFilled /></el-icon>
      <div class="profile-info">
        <span class="username">我的文库</span>
        <span class="sub">个人图书馆</span>
      </div>
    </div>

    <div class="menu-list">
      <div class="menu-item" @click="router.push('/novels')">
        <el-icon><Reading /></el-icon><span>我的书架</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="router.push('/settings')">
        <el-icon><Setting /></el-icon><span>设置</span>
        <el-switch v-model="store.isDark" size="small" @change="store.toggleTheme()" />
      </div>
      <div class="menu-item">
        <el-icon><DataAnalysis /></el-icon><span>数据统计</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="router.push('/trash')">
        <el-icon><Delete /></el-icon><span>回收站</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item">
        <el-icon><InfoFilled /></el-icon><span>关于</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mine-page { padding: 12px 16px; }
.profile-card {
  display: flex; align-items: center; gap: 16px;
  background: linear-gradient(135deg, var(--el-color-primary-light-9), var(--el-color-success)40);
  border-radius: 12px;
}
.profile-info { display: flex; flex-direction: column; }
.username { font-size: 20px; font-weight: 600; }
.sub { font-size: 13px; color: var(--el-text-color-secondary); }
.menu-list { margin-top: 16px; }
.menu-item {
  display: flex; align-items: center; gap: 12px;
  padding: 16px; background: var(--el-bg-color);
  border-radius: 10px; margin-bottom: 8px; cursor: pointer;
}
.menu-item span { flex: 1; font-size: 15px; }
.arrow { color: var(--el-text-color-secondary); }
</style>
