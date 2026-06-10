<script setup lang="ts">
import { HomeFilled, Collection, Notebook, UserFilled } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useRouter } from 'vue-router'

const store = useAppStore()
const router = useRouter()

const tabs = [
  { key: 'home', label: '首页', icon: HomeFilled, route: '/home' },
  { key: 'collection', label: '合集', icon: Collection, route: '/collections' },
  { key: 'bookGroup', label: '书架', icon: Notebook, route: '/novels' },
  { key: 'mine', label: '我的', icon: UserFilled, route: '/mine' },
]

function onTabClick(tab: (typeof tabs)[0]) {
  store.activeTab = tab.key
  router.push(tab.route)
}
</script>

<template>
  <div class="lofter-tabbar">
    <div
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item"
      :class="{ active: store.activeTab === tab.key }"
      @click="onTabClick(tab)"
    >
      <el-icon class="icon"><component :is="tab.icon" /></el-icon>
      <span class="text">{{ tab.label }}</span>
    </div>
  </div>
</template>
