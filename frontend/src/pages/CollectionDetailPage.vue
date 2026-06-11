<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { collectionsApi, articlesApi } from '@/api'
import type { Collection, Article } from '@/types'
import ArticleCard from '@/components/ArticleCard.vue'

const route = useRoute()
const router = useRouter()
const collection = ref<(Collection & { articles: Article[] }) | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const id = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
    if (!id) { router.replace('/collections'); return }
    const { data } = await collectionsApi.get(id)
    collection.value = data
  } finally { loading.value = false }
})

async function removeFromCollection(articleId: string) {
  if (!collection.value) return
  await collectionsApi.removeArticle(collection.value.id, articleId)
  collection.value.articles = collection.value.articles.filter(a => a.id !== articleId)
  ElMessage.success('已从合集移除')
}
</script>

<template>
  <div class="collection-detail" v-loading="loading">
    <div class="header-bar">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <h2>{{ collection?.name }}</h2>
    </div>
    <div class="header" :style="{ background: collection?.color + '20' }">
      <p>{{ collection?.description }}</p>
    </div>
    <ArticleCard v-for="a in collection?.articles" :key="a.id" :article="a"
      @click="router.push('/reader/' + a.id)" @delete="removeFromCollection(a.id)" style="cursor:pointer" />
    <el-empty v-if="!loading && !collection?.articles?.length" description="合集为空" />
  </div>
</template>

<style scoped>
.collection-detail { padding: 12px 16px; min-height: 200px; }
.header-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.header-bar h2 { flex: 1; font-size: 20px; font-weight: 600; }
.header { padding: 20px; border-radius: 12px; margin-bottom: 16px; }
.header p { font-size: 14px; color: var(--el-text-color-secondary); }
</style>
