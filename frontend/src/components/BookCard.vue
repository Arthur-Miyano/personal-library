<script setup lang="ts">
import { computed } from 'vue'
import type { Article } from '@/types'

const props = defineProps<{ article: Article }>()
const emit = defineEmits<{ click: []; tagClick: [tagId: string] }>()

const snippet = computed(() => {
  const text = props.article.raw_text || ''
  // 取前200个字符，避免每次渲染重复计算
  const sliced = text.length > 200 ? text.slice(0, 200) : text
  return sliced || '暂无内容摘要...'
})

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div
    class="book-card"
    @click="$emit('click')"
  >
    <!-- 背景水印首字 -->
    <div class="watermark-char serif-text">
      {{ article.title.charAt(0) }}
    </div>

    <!-- 内容层 -->
    <div class="content-layer">
      <!-- 标题 + 元数据 -->
      <div class="card-top">
        <h3 class="title-text serif-text">{{ article.title }}</h3>
        <div class="meta-row font-mono">
          <span v-if="article.source_name">{{ article.source_name }}</span>
          <span v-else>佚名</span>
          <span>·</span>
          <span>{{ fmtDate(article.created_at) }}</span>
          <span class="category-badge">{{ article.source_type || '文章' }}</span>
        </div>
      </div>

      <div class="divider"></div>

      <!-- 摘要 -->
      <div class="snippet-wrap">
        <p class="snippet-text">
          {{ snippet }}
          <span class="fade-mask"></span>
        </p>
      </div>

      <!-- 标签栏 -->
      <div v-if="article.tags?.length" class="tag-bar no-scrollbar">
        <span
          v-for="tag in article.tags"
          :key="tag.id"
          class="tag-item"
          @click.stop="$emit('tagClick', tag.id)"
        ># {{ tag.name }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ====== 卡片主体 ====== */
.book-card {
  background: var(--bg-surface);
  border: 1px solid rgba(220, 210, 201, 0.6);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}
.book-card:hover {
  box-shadow: 0 8px 20px rgba(44, 36, 33, 0.08);
  transform: translateY(-4px);
  border-color: rgba(200, 93, 93, 0.5);
}

/* ====== 背景水印 ====== */
.watermark-char {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 8rem;
  font-weight: 900;
  opacity: 0.03;
  pointer-events: none;
  transform: translateX(16px) translateY(-16px);
  user-select: none;
  color: var(--text-main);
}

/* ====== 内容层 ====== */
.content-layer {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.card-top {
  margin-bottom: 4px;
}

/* ====== 标题 ====== */
.title-text {
  font-weight: 700;
  font-size: 16px;
  color: var(--text-main);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
  transition: color 0.3s;
}
.book-card:hover .title-text {
  color: var(--primary);
}

/* ====== 元数据行 ====== */
.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--text-muted);
}
.category-badge {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-base);
  border: 1px solid rgba(220, 210, 201, 0.5);
  flex-shrink: 0;
}

/* ====== 分隔线 ====== */
.divider {
  border-top: 1px solid rgba(220, 210, 201, 0.3);
  margin: 14px 0;
}

/* ====== 摘要 ====== */
.snippet-wrap {
  flex: 1;
}
.snippet-text {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  position: relative;
}
.fade-mask {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 33%;
  height: 16px;
  background: linear-gradient(to left, var(--bg-surface), transparent);
}

/* ====== 标签栏 ====== */
.tag-bar {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(220, 210, 201, 0.2);
  display: flex;
  gap: 6px;
  overflow-x: auto;
  flex-shrink: 0;
}
.tag-bar::-webkit-scrollbar { display: none; }
.tag-bar { -ms-overflow-style: none; scrollbar-width: none; }
.tag-item {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  white-space: nowrap;
  border: 1px solid rgba(220, 210, 201, 0.5);
  color: var(--primary);
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.tag-item:hover {
  background: var(--primary-glow);
  border-color: var(--primary);
}
</style>
