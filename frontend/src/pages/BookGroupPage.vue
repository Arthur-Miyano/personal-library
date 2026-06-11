<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { collectionsApi } from '@/api'
import type { Collection } from '@/types'

const router = useRouter()
const groups = ref<Collection[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await collectionsApi.list()
    groups.value = Array.isArray(data) ? data : (data.items ?? [])
  } finally { loading.value = false }
})
</script>

<template>
  <div class="groups-page">
    <div class="page-header">
      <h2 class="page-title serif-text">书本分组</h2>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="!groups.length" class="empty-state">
      <p class="text-custom-muted">暂无分组，在合集页面创建合集后会自动显示在这里</p>
    </div>

    <div v-else class="groups-grid">
      <div v-for="g in groups" :key="g.id" class="group-card surface-card"
        @click="router.push(`/collection/${g.id}`)">
        <div class="group-icon" :style="{ backgroundColor: g.color || '#C85D5D' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <div class="group-info">
          <h3 class="group-name serif-text">{{ g.name }}</h3>
          <p class="group-desc" v-if="g.description">{{ g.description }}</p>
        </div>
        <span class="group-count">{{ g.articles?.length || 0 }} 篇</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.groups-page { padding: 24px 32px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--text-main); }
.groups-grid { display: flex; flex-direction: column; gap: 8px; max-width: 600px; }
.group-card {
  display: flex; align-items: center; gap: 14px; padding: 16px;
  cursor: pointer; border-radius: 14px;
}
.group-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.group-info { flex: 1; min-width: 0; }
.group-name { font-size: 14px; font-weight: 600; }
.group-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.group-count { font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); }
.empty-state, .loading-state { text-align: center; padding: 60px 0; color: var(--text-muted); }
</style>
