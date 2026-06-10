<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { novelsApi } from '@/api'
import type { Novel } from '@/types'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const novels = ref<Novel[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await novelsApi.list({ page: 1, size: 50 })
    novels.value = data.items
  } finally { loading.value = false }
})
</script>

<template>
  <div class="novel-list-page">
    <div class="page-header">
      <h2>我的书架</h2>
      <el-button circle :icon="Plus" size="small" @click="router.push('/novels/upload')" />
    </div>

    <div v-loading="loading" class="novel-grid">
      <div
        v-for="n in novels"
        :key="n.id"
        class="lofter-card novel-card"
        @click="router.push(`/novels/${n.id}`)"
      >
        <div class="cover" :style="{ background: n.cover_path ? `url(${n.cover_path})` : '#E9F0F8' }">
          <span v-if="!n.cover_path" class="cover-text">{{ n.title[0] }}</span>
        </div>
        <div class="info">
          <span class="name">{{ n.title }}</span>
          <span class="author" v-if="n.author">{{ n.author }}</span>
          <span class="meta">{{ n.total_chapters || 0 }}章 · {{ n.total_words || 0 }}字</span>
          <el-tag v-if="n.is_read" size="small" type="success">已读</el-tag>
        </div>
      </div>
      <el-empty v-if="!loading && !novels.length" description="书架空空，上传第一本小说吧" />
    </div>
  </div>
</template>

<style scoped>
.novel-list-page { padding: 12px 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; font-weight: 600; }
.novel-card { display: flex; gap: 12px; cursor: pointer; }
.cover {
  width: 60px; height: 80px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.cover-text { font-size: 24px; color: var(--el-color-primary); font-weight: 600; }
.info { display: flex; flex-direction: column; gap: 2px; }
.name { font-size: 16px; font-weight: 500; }
.author { font-size: 13px; color: var(--el-text-color-secondary); }
.meta { font-size: 12px; color: var(--el-text-color-secondary); }
</style>
