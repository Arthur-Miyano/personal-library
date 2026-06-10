<script setup lang="ts">
import type { Article } from '@/types'

defineProps<{ article: Article }>()
</script>

<template>
  <div class="lofter-card article-card">
    <h3 class="title">{{ article.title }}</h3>
    <p class="summary">{{ article.raw_text?.slice(0, 200) }}</p>
    <div class="tags">
      <span v-for="tag in article.tags" :key="tag.id" class="lofter-tag"
        :style="{ backgroundColor: tag.color + '20', color: tag.color }">
        {{ tag.name }}
      </span>
    </div>
    <div class="footer">
      <span class="meta">
        {{ article.source_name ? article.source_name + ' · ' : '' }}{{ article.word_count }}字 · {{ article.created_at?.slice(0, 10) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.title { font-size: 17px; font-weight: 600; margin-bottom: 6px; }
.summary {
  font-size: 14px; line-height: 1.8; color: var(--el-text-color-regular);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 8px;
}
.footer { margin-top: 8px; font-size: 13px; color: var(--el-text-color-secondary); display: flex; justify-content: space-between; align-items: center; }
</style>
