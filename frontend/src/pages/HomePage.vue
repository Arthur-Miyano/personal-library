<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { articlesApi, novelsApi } from '@/api'
import type { Article, Novel } from '@/types'
import ArticleCard from '@/components/ArticleCard.vue'
import NovelCard from '@/components/NovelCard.vue'

const router = useRouter()
const activeTab = ref<'articles' | 'novels'>('articles')
const articles = ref<Article[]>([])
const novels = ref<Novel[]>([])
const loading = ref(false)
const searchText = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const [aRes, nRes] = await Promise.all([
      articlesApi.list(),
      novelsApi.list({ page: 1, size: 50 }),
    ])
    articles.value = aRes.data
    novels.value = nRes.data.items
  } finally {
    loading.value = false
  }
})

const filteredArticles = computed(() =>
  searchText.value
    ? articles.value.filter(a => a.title.includes(searchText.value))
    : articles.value
)

const filteredNovels = computed(() =>
  searchText.value
    ? novels.value.filter(n => n.title.includes(searchText.value))
    : novels.value
)

async function deleteNovel(id: string) {
  try {
    await ElMessageBox.confirm('确定删除这本小说？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await novelsApi.delete(id)
    novels.value = novels.value.filter(n => n.id !== id)
    ElMessage.success('已移入回收站')
  } catch { /* cancelled */ }
}

function goUpload() {
  router.push(activeTab.value === 'articles' ? '/upload' : '/novels/upload')
}
</script>

<template>
  <div class="home-page">
    <el-input v-model="searchText" placeholder="搜索..." clearable class="search-bar" />

    <el-tabs v-model="activeTab" stretch>
      <el-tab-pane label="文章" name="articles" />
      <el-tab-pane label="小说" name="novels" />
    </el-tabs>

    <div v-loading="loading">
      <template v-if="activeTab === 'articles'">
        <ArticleCard v-for="a in filteredArticles" :key="a.id" :article="a"
          @click="router.push(`/reader/${a.id}`)" style="cursor:pointer" />
        <el-empty v-if="!loading && !filteredArticles.length" description="还没有内容，上传文件开始阅读" />
      </template>

      <template v-if="activeTab === 'novels'">
        <NovelCard v-for="n in filteredNovels" :key="n.id" :novel="n"
          @click="router.push(`/novels/${n.id}`)" @delete="deleteNovel"
          style="cursor:pointer" />
        <el-empty v-if="!loading && !filteredNovels.length" description="书架空空，上传第一本小说吧" />
      </template>
    </div>

    <el-button type="primary" circle size="large" class="fab" @click="goUpload">
      <el-icon size="22"><Upload /></el-icon>
    </el-button>
  </div>
</template>

<style scoped>
.home-page { padding: 12px 16px; }
.search-bar { margin-bottom: 8px; }
.fab {
  position: fixed; bottom: 80px; right: 20px;
  width: 48px; height: 48px;
  box-shadow: 0 4px 12px rgba(74, 111, 165, 0.3);
  z-index: 10;
}
</style>
