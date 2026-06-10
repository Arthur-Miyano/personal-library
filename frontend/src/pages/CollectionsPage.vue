<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { collectionsApi } from '@/api'
import type { Collection } from '@/types'

const router = useRouter()
const collections = ref<Collection[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await collectionsApi.list()
    collections.value = data
  } finally { loading.value = false }
})

async function createCollection() {
  try {
    const { value } = await ElMessageBox.prompt('请输入合集名称', '新建合集')
    if (!value?.trim()) return
    await collectionsApi.create({ name: value.trim() })
    const { data } = await collectionsApi.list()
    collections.value = data
  } catch { /* */ }
}
</script>

<template>
  <div class="collections-page">
    <div class="page-header">
      <h2 class="page-title serif-text">我的合集</h2>
      <button class="header-btn" @click="createCollection">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="!collections.length" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
      <p>还没有合集</p>
    </div>

    <div v-else class="collections-grid">
      <div v-for="c in collections" :key="c.id" class="surface-card collection-card"
        @click="router.push(`/collection/${c.id}`)">
        <div class="collection-icon" :style="{ backgroundColor: c.color }">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <div class="collection-info">
          <h3 class="collection-name">{{ c.name }}</h3>
          <p class="collection-desc">{{ c.description }}</p>
        </div>
        <svg class="collection-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 18l6-6-6-6" />
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.collections-page {
  padding: 24px 32px;
  min-height: 100vh;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}
.header-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-surface);
  color: var(--text-main);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.header-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.header-btn svg { width: 16px; height: 16px; }

.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.collection-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  cursor: pointer;
  border-radius: 14px;
}
.collection-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.collection-icon svg { width: 16px; height: 16px; }
.collection-info {
  flex: 1;
  min-width: 0;
}
.collection-name {
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-serif);
}
.collection-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.collection-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-muted);
}
.empty-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 16px;
  opacity: 0.3;
}
.loading-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 768px) {
  .collections-page { padding: 16px; }
}
</style>
