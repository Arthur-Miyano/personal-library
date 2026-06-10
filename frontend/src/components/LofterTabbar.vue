<script setup lang="ts">
import { HomeFilled, Collection, Reading, UserFilled } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useRouter } from 'vue-router'

const store = useAppStore()
const router = useRouter()

const tabs = [
  { key: 'home', label: '首页', icon: HomeFilled, route: '/home' },
  { key: 'collection', label: '合集', icon: Collection, route: '/collections' },
  { key: 'bookshelf', label: '书架', icon: Reading, route: '/novels' },
  { key: 'mine', label: '我的', icon: UserFilled, route: '/mine' },
]

function onTabClick(tab: (typeof tabs)[0]) {
  store.activeTab = tab.key
  router.push(tab.route)
}
</script>

<template>
  <div class="lofter-tabbar">
    <div v-for="tab in tabs" :key="tab.key" class="tab-item"
      :class="{ active: store.activeTab === tab.key }" @click="onTabClick(tab)">
      <el-icon class="icon"><component :is="tab.icon" /></el-icon>
      <span class="text">{{ tab.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.lofter-tabbar {
  display: flex; justify-content: space-around; align-items: center;
  height: 56px; background: var(--lofter-surface);
  border-top: 1px solid var(--lofter-border);
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 100;
}
.tab-item { display: flex; flex-direction: column; align-items: center; color: var(--lofter-text-secondary); cursor: pointer; }
.tab-item.active { color: var(--lofter-accent); }
.tab-item.active::after {
  content: ""; display: block; width: 20px; height: 2px;
  background: var(--lofter-accent); border-radius: 1px; margin-top: 4px;
}
.icon { font-size: 20px; margin-bottom: 2px; }
.text { font-size: 11px; }
</style>
