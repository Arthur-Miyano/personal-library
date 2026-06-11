<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { articlesApi, novelsApi } from '@/api'
import type { Article, Novel } from '@/types'

const router = useRouter()
const tab = ref<'articles' | 'novels'>('articles')
const articles = ref<Article[]>([])
const novels = ref<Novel[]>([])

async function loadTrash() {
  if (tab.value === 'articles') {
    const { data } = await articlesApi.trash()
    articles.value = data
  } else {
    const { data } = await novelsApi.trash()
    novels.value = Array.isArray(data) ? data : (data.items ?? [])
  }
}

onMounted(loadTrash)
watch(tab, loadTrash)

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

async function restoreNovel(id: string) {
  await novelsApi.restore(id)
  const { data } = await novelsApi.trash()
  novels.value = Array.isArray(data) ? data : (data.items ?? [])
}

async function permanentDeleteNovel(id: string) {
  await novelsApi.permanentDelete(id)
  const { data } = await novelsApi.trash()
  novels.value = Array.isArray(data) ? data : (data.items ?? [])
}
</script>

<template>
  <div class="trash-page">
    <div class="page-header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <h2>回收站</h2>
      <div class="trash-tabs">
        <button :class="{ active: tab === 'articles' }" @click="tab = 'articles'">文章</button>
        <button :class="{ active: tab === 'novels' }" @click="tab = 'novels'">小说</button>
      </div>
    </div>

    <!-- 文章回收站 -->
    <template v-if="tab === 'articles'">
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
    </template>

    <!-- 小说回收站 -->
    <template v-if="tab === 'novels'">
      <div v-for="n in novels" :key="n.id" class="lofter-card trash-item">
        <div class="info">
          <span class="title">{{ n.title }}</span>
          <span class="meta">{{ n.total_words || 0 }}字 · {{ n.created_at?.slice(0, 10) }}</span>
        </div>
        <div class="actions">
          <el-button size="small" @click="restoreNovel(n.id)">恢复</el-button>
          <el-button size="small" type="danger" @click="permanentDeleteNovel(n.id)">彻底删除</el-button>
        </div>
      </div>
      <el-empty v-if="!novels.length" description="回收站为空" />
    </template>
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
