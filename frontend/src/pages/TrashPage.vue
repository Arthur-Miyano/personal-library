<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { articlesApi } from '@/api'
import type { Article } from '@/types'

const router = useRouter()
const articles = ref<Article[]>([])

onMounted(async () => {
  const { data } = await articlesApi.trash()
  articles.value = data
})

async function restore(id: string) {
  await articlesApi.restore(id)
  const { data } = await articlesApi.trash()
  articles.value = data
}

async function permanentDelete(id: string) {
  await articlesApi.permanentDelete(id)
  const { data } = await articlesApi.trash()
  articles.value = data
}
</script>

<template>
  <div class="trash-page">
    <div class="page-header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <h2>回收站</h2>
    </div>
    <div v-for="a in articles" :key="a.id" class="lofter-card trash-item">
      <div class="info">
        <span class="title">{{ a.title }}</span>
        <span class="meta">{{ a.word_count }}字 · {{ a.created_at?.slice(0, 10) }}</span>
      </div>
      <div class="actions">
        <el-button size="small" @click="restore(a.id)">恢复</el-button>
        <el-button size="small" type="danger" @click="permanentDelete(a.id)">彻底删除</el-button>
      </div>
    </div>
    <el-empty v-if="!articles.length" description="回收站为空" />
  </div>
</template>

<style scoped>
.trash-page { padding: 12px 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; font-size: 20px; font-weight: 600; }
.trash-item { display: flex; justify-content: space-between; align-items: center; }
.info { display: flex; flex-direction: column; }
.title { font-size: 15px; font-weight: 500; }
.meta { font-size: 13px; color: var(--el-text-color-secondary); }
.actions { display: flex; gap: 8px; }
</style>
