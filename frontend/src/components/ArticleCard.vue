<script setup lang="ts">
import type { Article } from '@/types'

defineProps<{ article: Article }>()
const emit = defineEmits<{ delete: [id: string]; tagClick: [tagId: string] }>()

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="lofter-card article-card">
    <div class="card-body">
      <h3 class="title">{{ article.title }}</h3>
      <p class="excerpt">{{ Array.from(article.raw_text || '').slice(0, 120).join('') }}</p>
      <div class="tags" v-if="article.tags?.length">
        <span v-for="tag in article.tags" :key="tag.id" class="lofter-tag"
          :style="{ background: tag.color + '20', color: tag.color }"
          @click.stop="emit('tagClick', tag.id)">#{{ tag.name }}</span>
      </div>
      <div class="meta">
        <span>{{ article.word_count }}字 · {{ fmtDate(article.created_at) }}</span>
        <span class="source" v-if="article.source_name">{{ article.source_name }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.article-card { cursor: pointer; }
.card-body { padding: 20px; }
.title { font-size: 17px; font-weight: 600; margin-bottom: 8px; line-height: 1.4; color: var(--lofter-text-primary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.excerpt { font-size: 13px; color: var(--lofter-text-secondary); line-height: 1.6; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.meta { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--lofter-text-secondary); margin-top: 10px; }
.source { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 50%; }
</style>
