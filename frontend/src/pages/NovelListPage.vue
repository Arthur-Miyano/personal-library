<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { novelsApi } from '@/api'
import type { Novel } from '@/types'
import gsap from 'gsap'

const router = useRouter()
const novels = ref<Novel[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await novelsApi.list({ page: 1, size: 50 })
    novels.value = data.items
    nextTick(() => {
      gsap.fromTo('.shelf-book', { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.4, stagger: 0.04 })
    })
  } finally { loading.value = false }
})
</script>

<template>
  <div class="shelf-page">
    <div class="shelf-header">
      <h2 class="shelf-title serif-text">我的书架</h2>
      <button class="add-btn" @click="router.push('/novels/upload')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </div>

    <div v-if="loading" class="shelf-grid">
      <div v-for="i in 8" :key="i" class="skeleton-card">
        <div class="skeleton-cover"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
      </div>
    </div>

    <div v-else-if="!novels.length" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M4 20V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2z" />
      </svg>
      <p>书架空空，上传第一本小说吧</p>
      <button class="upload-btn" @click="router.push('/novels/upload')">上传小说</button>
    </div>

    <TransitionGroup v-else name="list" tag="div" class="shelf-grid">
      <div v-for="n in novels" :key="n.id" class="shelf-book surface-card"
        @click="router.push(`/novels/${n.id}`)">
        <div class="book-cover" :style="{
          background: n.cover_path
            ? `url(${n.cover_path}) center/cover`
            : 'linear-gradient(135deg, var(--primary-glow), transparent)'
        }">
          <span v-if="!n.cover_path" class="book-initial serif-text">{{ n.title[0] }}</span>
          <div v-if="n.is_read" class="read-badge">已读</div>
        </div>
        <div class="book-info">
          <p class="book-title">{{ n.title }}</p>
          <p class="book-author" v-if="n.author">{{ n.author }}</p>
          <p class="book-meta">{{ n.total_chapters || 0 }}章 · {{ n.total_words || 0 }}字</p>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.shelf-page {
  padding: 24px 32px;
  min-height: 100vh;
}
.shelf-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.shelf-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}
.add-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-surface);
  color: var(--text-main);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.add-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.add-btn svg { width: 16px; height: 16px; }

/* 书架网格 */
.shelf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
  padding-bottom: 40px;
}
.shelf-book {
  padding: 12px 12px 16px;
  cursor: pointer;
  text-align: center;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.book-cover {
  width: 100%;
  aspect-ratio: 3/4;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border);
}
.book-initial {
  font-size: 36px;
  font-weight: 700;
  color: var(--primary);
  user-select: none;
}
.read-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--primary);
  color: #fff;
  font-size: 9px;
  font-family: var(--font-mono);
}
.book-info {
  width: 100%;
}
.book-title {
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-serif);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.book-author {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.book-meta {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
  font-family: var(--font-mono);
}

/* 骨架屏 */
.skeleton-card {
  text-align: center;
}
.skeleton-cover {
  width: 100%;
  aspect-ratio: 3/4;
  border-radius: 10px;
  background: var(--border);
  margin-bottom: 12px;
  animation: pulse 1.5s infinite;
}
.skeleton-line {
  height: 12px;
  background: var(--border);
  border-radius: 6px;
  margin-bottom: 6px;
  animation: pulse 1.5s infinite;
}
.skeleton-line.short { width: 60%; margin: 0 auto; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-muted);
}
.empty-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 16px;
  opacity: 0.3;
}
.upload-btn {
  margin-top: 16px;
  padding: 8px 24px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--bg-surface);
  color: var(--text-main);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.upload-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

@media (max-width: 768px) {
  .shelf-page { padding: 16px; }
  .shelf-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
}
</style>
