<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { novelsApi } from '@/api'
import type { Novel } from '@/types'
import gsap from 'gsap'

const router = useRouter()
const novels = ref<Novel[]>([])
const loading = ref(false)
const novSearch = ref('')
const batchMode = ref(false)
const selectedIds = ref<Set<string>>(new Set())

const filteredNovels = computed(() => {
  if (!novSearch.value) return novels.value
  const q = novSearch.value.toLowerCase()
  return novels.value.filter(n => n.title.toLowerCase().includes(q) || (n.author || '').toLowerCase().includes(q))
})

const allSelected = computed(() => {
  return filteredNovels.value.length > 0 && filteredNovels.value.every(n => selectedIds.value.has(n.id))
})

async function fetchNovels() {
  loading.value = true
  try {
    const { data } = await novelsApi.list({ page: 1, size: 50 })
    novels.value = data.items
    nextTick(() => {
      gsap.fromTo('.shelf-book', { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.4, stagger: 0.04 })
    })
  } finally { loading.value = false }
}

onMounted(fetchNovels)

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selectedIds.value.clear()
}

function toggleSelect(novel: Novel) {
  if (selectedIds.value.has(novel.id)) {
    selectedIds.value.delete(novel.id)
  } else {
    selectedIds.value.add(novel.id)
  }
}

function toggleSelectAll() {
  if (allSelected.value) {
    filteredNovels.value.forEach(n => selectedIds.value.delete(n.id))
  } else {
    filteredNovels.value.forEach(n => selectedIds.value.add(n.id))
  }
}

async function handleBatchDelete() {
  const ids = Array.from(selectedIds.value)
  if (!ids.length) return
  if (!confirm(`确定要删除选中的 ${ids.length} 本小说吗？`)) return
  try {
    await novelsApi.batchDelete(ids)
    novels.value = novels.value.filter(n => !selectedIds.value.has(n.id))
    selectedIds.value.clear()
    batchMode.value = false
    ElMessage.success(`已删除 ${ids.length} 本小说`)
  } catch { ElMessage.error('批量删除失败') }
}

async function handleDelete(novel: Novel) {
  if (!confirm(`确定要删除《${novel.title}》吗？`)) return
  try {
    await novelsApi.delete(novel.id)
    novels.value = novels.value.filter(n => n.id !== novel.id)
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
}
</script>

<template>
  <div class="shelf-page">
    <div class="shelf-header">
      <h2 class="shelf-title serif-text">我的书架</h2>
      <input v-model="novSearch" type="text" placeholder="搜索小说..." class="novel-search-input" />
      <div class="header-actions">
        <button v-if="novels.length" class="batch-toggle-btn" @click="toggleBatchMode">
          {{ batchMode ? '完成' : '管理' }}
        </button>
        <button class="add-btn" @click="router.push('/novels/upload')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="batchMode" class="batch-bar">
      <label class="batch-check-all">
        <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
        <span>全选</span>
      </label>
      <span class="batch-count">已选 {{ selectedIds.size }} 本</span>
      <button class="batch-delete-btn" :disabled="!selectedIds.size" @click="handleBatchDelete">
        删除选中
      </button>
    </div>

    <div v-if="loading" class="shelf-grid">
      <div v-for="i in 8" :key="i" class="skeleton-card">
        <div class="skeleton-cover"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
      </div>
    </div>

    <div v-else-if="!filteredNovels.length" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M4 20V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2z" />
      </svg>
      <p>书架空空，上传第一本小说吧</p>
      <button class="upload-btn" @click="router.push('/novels/upload')">上传小说</button>
    </div>

    <TransitionGroup v-else name="list" tag="div" class="shelf-grid">
      <div v-for="n in filteredNovels" :key="n.id" class="shelf-book surface-card novel-card-wrap">
        <!-- 批量模式复选框 -->
        <div v-if="batchMode" class="batch-checkbox" @click.stop="toggleSelect(n)">
          <input type="checkbox" :checked="selectedIds.has(n.id)" @click.stop />
        </div>
        <!-- 点击卡片主体跳转详情 -->
        <div class="card-main" @click="batchMode ? toggleSelect(n) : router.push(`/novels/${n.id}`)">
          <button v-if="!batchMode" class="novel-delete-btn" @click.stop="handleDelete(n)" title="删除">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
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
.novel-search-input {
  padding: 8px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--bg-surface); font-size: 12px; font-family: var(--font-mono);
  outline: none; width: 200px; color: var(--text-main);
}
.novel-search-input:focus { border-color: var(--primary); }
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.batch-toggle-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-surface);
  color: var(--text-main);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.batch-toggle-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
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

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  margin-bottom: 16px;
  background: var(--bg-surface);
  border-radius: 10px;
  border: 1px solid var(--border);
}
.batch-check-all {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-main);
  cursor: pointer;
}
.batch-count {
  flex: 1;
  font-size: 12px;
  color: var(--text-muted);
}
.batch-delete-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  background: #DC2626;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.batch-delete-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 书架网格 */
.shelf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
  padding-bottom: 40px;
}
.novel-card-wrap { position: relative; }
.card-main {
  position: relative;
  cursor: pointer;
}
.novel-delete-btn {
  position: absolute; top: 8px; right: 8px; z-index: 5;
  width: 24px; height: 24px; border-radius: 6px; border: none;
  background: var(--danger-bg); color: #DC2626;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; opacity: 0; transition: opacity 0.2s;
}
.novel-card-wrap:hover .novel-delete-btn { opacity: 1; }
.novel-delete-btn:hover { background: #FEE2E2; }

.batch-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  width: 20px;
  height: 20px;
}
.batch-checkbox input {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
  cursor: pointer;
}

.shelf-book {
  padding: 12px 12px 16px;
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
