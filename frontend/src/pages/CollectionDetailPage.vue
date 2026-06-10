<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { collectionsApi } from '@/api'
import type { Collection, Article } from '@/types'
import ArticleCard from '@/components/ArticleCard.vue'

const route = useRoute()
const collection = ref<(Collection & { articles: Article[] }) | null>(null)

onMounted(async () => {
  const id = route.params.id as string
  const { data } = await collectionsApi.get(id)
  collection.value = data
})
</script>

<template>
  <div class="collection-detail">
    <div class="header" :style="{ background: collection?.color + '20' }">
      <h2>{{ collection?.name }}</h2>
      <p>{{ collection?.description }}</p>
    </div>
    <ArticleCard v-for="a in collection?.articles" :key="a.id" :article="a" />
    <el-empty v-if="!collection?.articles?.length" description="合集为空" />
  </div>
</template>

<style scoped>
.collection-detail { padding: 12px 16px; }
.header { padding: 20px; border-radius: 12px; margin-bottom: 16px; }
.header h2 { font-size: 22px; margin-bottom: 4px; }
.header p { font-size: 14px; color: var(--el-text-color-secondary); }
</style>
