<script setup lang="ts">
import type { Novel } from '@/types'

defineProps<{ novel: Novel }>()
const emit = defineEmits<{ delete: [id: string] }>()
</script>

<template>
  <div class="lofter-card novel-card">
    <div class="cover" :style="{ backgroundColor: '#E9F0F8' }">
      <span class="cover-text">{{ novel.title[0] }}</span>
    </div>
    <div class="info">
      <span class="name">{{ novel.title }}</span>
      <span class="author" v-if="novel.author">{{ novel.author }}</span>
      <span class="meta">
        {{ novel.total_chapters || 0 }}章 · {{ novel.total_words || 0 }}字
        <el-tag v-if="novel.is_read" size="small" type="success" class="read-tag">已读</el-tag>
      </span>
    </div>
    <el-button text type="danger" size="small" @click.stop="emit('delete', novel.id)">
      <el-icon><Delete /></el-icon>
    </el-button>
  </div>
</template>

<style scoped>
.novel-card { display: flex; gap: 12px; align-items: center; }
.cover {
  width: 50px; height: 66px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.cover-text { font-size: 20px; color: var(--el-color-primary); font-weight: 600; }
.info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.name { font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.author { font-size: 13px; color: var(--el-text-color-secondary); }
.meta { font-size: 12px; color: var(--el-text-color-secondary); display: flex; align-items: center; gap: 6px; }
.read-tag { font-size: 11px; }
</style>
