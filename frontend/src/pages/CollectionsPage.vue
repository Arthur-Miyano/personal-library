<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { collectionsApi } from '@/api'
import type { Collection } from '@/types'
import { Plus } from '@element-plus/icons-vue'

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
  const name = prompt('合集名称')
  if (!name) return
  await collectionsApi.create({ name })
  const { data } = await collectionsApi.list()
  collections.value = data
}
</script>

<template>
  <div class="collections-page">
    <div class="page-header">
      <h2>我的合集</h2>
      <el-button circle :icon="Plus" size="small" @click="createCollection" />
    </div>
    <div v-loading="loading" class="collection-grid">
      <div
        v-for="c in collections"
        :key="c.id"
        class="lofter-card collection-card"
        :style="{ borderLeft: `4px solid ${c.color}` }"
        @click="router.push(`/collection/${c.id}`)"
      >
        <el-icon size="24"><Folder /></el-icon>
        <span class="name">{{ c.name }}</span>
        <span class="desc">{{ c.description }}</span>
      </div>
      <el-empty v-if="!loading && !collections.length" description="还没有合集" />
    </div>
  </div>
</template>

<style scoped>
.collections-page { padding: 12px 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; font-weight: 600; }
.collection-card {
  display: flex; align-items: center; gap: 12px; cursor: pointer;
}
.name { font-size: 16px; font-weight: 500; }
.desc { font-size: 13px; color: var(--el-text-color-secondary); }
</style>
