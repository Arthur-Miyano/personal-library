<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useArticleStore } from '@/stores/article'
import { articlesApi, collectionsApi } from '@/api'
import type { Collection } from '@/types'
import BookCard from '@/components/BookCard.vue'
import gsap from 'gsap'

const props = defineProps<{
  currentShelf?: string
  searchKey?: string
}>()

const router = useRouter()
const store = useArticleStore()

// --- 多选状态 ---
const selectedIds = ref<Set<string>>(new Set())
const selectAll = ref(false)
const deleteModalOpen = ref(false)
const clearAllModalOpen = ref(false)
const clearAllConfirmText = ref('')
const deleting = ref(false)

// --- 合集 ---
const collectionModalOpen = ref(false)
const collectionPickerOpen = ref(false)
const collections = ref<Collection[]>([])
const selectedCollectionId = ref('')

// 前端搜索过滤
const displayArticles = computed(() => {
  let list = store.filteredArticles
  if (props.searchKey) {
    const q = props.searchKey.toLowerCase()
    list = list.filter(a =>
      a.title.toLowerCase().includes(q) ||
      a.raw_text.toLowerCase().includes(q)
    )
  }
  return list
})

const selectedCount = computed(() => selectedIds.value.size)
const allSelected = computed(() =>
  displayArticles.value.length > 0 &&
  displayArticles.value.every(a => selectedIds.value.has(a.id))
)

onMounted(async () => {
  await store.init()
  animateCards()
})

watch(() => [props.currentShelf, props.searchKey], () => {
  selectedIds.value.clear()
  nextTick(() => animateCards())
})

function animateCards() {
  nextTick(() => {
    gsap.fromTo('.book-card', { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.4, stagger: 0.04 })
  })
}

// --- 多选逻辑 ---
function toggleSelect(id: string) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(displayArticles.value.map(a => a.id))
  }
}

function handleCardClick(article: { id: string }) {
  if (selectedCount.value > 0) {
    // 多选模式下：点击切换勾选
    toggleSelect(article.id)
  } else {
    router.push('/reader/' + article.id)
  }
}

// --- 批量删除 ---
async function executeBatchDelete() {
  deleting.value = true
  try {
    let ok = 0
    for (const id of selectedIds.value) {
      try { await articlesApi.delete(id); ok++ } catch { /* */ }
    }
    store.articles = store.articles.filter(a => !selectedIds.value.has(a.id))
    selectedIds.value.clear()
    deleteModalOpen.value = false
    ElMessage.success(`已删除 ${ok} 篇文章`)
  } finally {
    deleting.value = false
  }
}

// --- 清空全部 ---
async function executeClearAll() {
  if (clearAllConfirmText.value !== 'DELETE') return
  deleting.value = true
  try {
    let ok = 0
    for (const a of displayArticles.value) {
      try { await articlesApi.delete(a.id); ok++ } catch { /* */ }
    }
    store.articles = store.articles.filter(a => !displayArticles.value.some(d => d.id === a.id))
    clearAllModalOpen.value = false
    clearAllConfirmText.value = ''
    ElMessage.success(`已清空 ${ok} 篇文章`)
  } finally {
    deleting.value = false
  }
}

// --- 合集操作 ---
async function openCollectionPicker() {
  collectionPickerOpen.value = false
  collectionModalOpen.value = true
  if (collections.value.length === 0) {
    try {
      const { data } = await collectionsApi.list()
      collections.value = Array.isArray(data) ? data : (data.items ?? [])
    } catch { /* */ }
  }
}

async function addSelectedToCollection() {
  if (!selectedCollectionId.value || selectedCount.value === 0) return
  let ok = 0
  for (const id of selectedIds.value) {
    try { await collectionsApi.addArticle(selectedCollectionId.value, id); ok++ } catch { /* */ }
  }
  selectedIds.value.clear()
  collectionModalOpen.value = false
  ElMessage.success(`已将 ${ok} 篇加入合集`)
}
</script>

<template>
  <div class="home-page">
    <!-- ====== 批量操作栏 ====== -->
    <div v-if="selectedCount > 0" class="batch-bar">
      <span class="batch-count">已选择 {{ selectedCount }} 篇</span>
      <button class="batch-btn batch-btn-collection" @click="openCollectionPicker">加入合集</button>
      <button class="batch-btn batch-btn-delete" @click="deleteModalOpen = true">批量删除</button>
      <button class="batch-btn batch-btn-cancel" @click="selectedIds.clear()">取消选择</button>
    </div>

    <!-- ====== 标签筛选 ====== -->
    <div class="tag-bar" v-if="store.tags.length">
      <span class="tag-chip" :class="{ active: !store.activeTagId }" @click="store.clearTag()">全部</span>
      <span v-for="t in store.tags" :key="t.id" class="tag-chip"
        :class="{ active: store.activeTagId === t.id }" @click="store.filterByTag(t.id)">{{ t.name }}</span>

      <!-- 全选复选框 -->
      <label class="select-all-chip" v-if="displayArticles.length > 0">
        <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
        <span>全选</span>
      </label>

      <!-- 清空筛选结果（高危） -->
      <button v-if="displayArticles.length > 0" class="clear-all-chip"
        @click="clearAllModalOpen = true">
        清空筛选结果
      </button>
    </div>

    <!-- ====== 空状态 ====== -->
    <div v-if="!displayArticles.length && !store.loading" class="empty-state">
      <span class="empty-title serif-text">未发现匹配的文章</span>
      <span class="empty-code">STATUS_CODE: 404_EMPTY_SET</span>
    </div>

    <!-- ====== 卡片网格 ====== -->
    <transition-group v-else name="list" tag="div" class="card-grid">
      <div v-for="a in displayArticles" :key="a.id" class="card-wrapper">
        <!-- 复选框（hover 或选中时显示） -->
        <label class="card-check" :class="{ visible: selectedCount > 0 || selectedIds.has(a.id) }"
          @click.stop>
          <input type="checkbox"
            :checked="selectedIds.has(a.id)"
            @change="toggleSelect(a.id)" />
        </label>

        <BookCard :article="a"
          :class="{ 'card-selected': selectedIds.has(a.id) }"
          @click="handleCardClick(a)"
          @tag-click="store.filterByTag" />
      </div>

      <!-- 新建文献卡片 -->
      <div
        class="create-card"
        @click="router.push('/editor')"
      >
        <span class="create-plus">+</span>
        <span class="create-label">新建文章</span>
      </div>
    </transition-group>

    <!-- ========================================== 批量删除弹窗 ========================================== -->
    <Transition name="modal">
      <div v-if="deleteModalOpen" class="modal-overlay" @click.self="deleteModalOpen = false">
        <div class="modal-card" style="width: 400px;">
          <div class="modal-header">
            <h3 class="modal-title">批量删除</h3>
            <button @click="deleteModalOpen = false" class="modal-close">✕</button>
          </div>

          <p class="delete-confirm-text">
            即将删除选中的 <strong>{{ selectedCount }}</strong> 篇文章，删除后将移入回收站。
          </p>

          <div class="modal-actions">
            <button @click="deleteModalOpen = false" class="btn-cancel">取消</button>
            <button @click="executeBatchDelete" :disabled="deleting" class="btn-danger">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ========================================== 清空全部弹窗（二次输入校验） ========================================== -->
    <Transition name="modal">
      <div v-if="clearAllModalOpen" class="modal-overlay" @click.self="clearAllModalOpen = false">
        <div class="modal-card" style="width: 420px;">
          <div class="modal-header">
            <h3 class="modal-title" style="color: #DC2626;">⚠ 清空全部文章</h3>
            <button @click="clearAllModalOpen = false" class="modal-close">✕</button>
          </div>

          <p class="delete-warn" style="margin-bottom: 16px;">
            此操作将删除当前筛选结果中的 <strong>{{ displayArticles.length }}</strong> 篇文章，移入回收站。
            如需恢复，可在回收站中找回。
          </p>

          <label class="delete-label">输入 DELETE 确认操作</label>
          <input
            v-model="clearAllConfirmText"
            type="text"
            placeholder="输入 DELETE"
            class="clear-all-input"
            autocomplete="off"
          />

          <div class="modal-actions">
            <button @click="clearAllModalOpen = false; clearAllConfirmText = ''" class="btn-cancel">取消</button>
            <button
              @click="executeClearAll"
              :disabled="deleting || clearAllConfirmText !== 'DELETE'"
              class="btn-danger"
            >
              {{ deleting ? '清空中...' : '确认清空' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ========================================== 加入合集弹窗 ========================================== -->
    <Transition name="modal">
      <div v-if="collectionModalOpen" class="modal-overlay" @click.self="collectionModalOpen = false">
        <div class="modal-card" style="width: 380px;">
          <div class="modal-header">
            <h3 class="modal-title">加入合集</h3>
            <button @click="collectionModalOpen = false" class="modal-close">✕</button>
          </div>

          <p class="delete-confirm-text" style="margin-bottom: 14px;">
            将选中的 <strong>{{ selectedCount }}</strong> 篇文章加入合集：
          </p>

          <select v-model="selectedCollectionId" class="collection-select">
            <option value="" disabled>选择合集...</option>
            <option v-for="c in collections" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>

          <div class="modal-actions">
            <button @click="collectionModalOpen = false" class="btn-cancel">取消</button>
            <button @click="addSelectedToCollection" :disabled="!selectedCollectionId" class="btn-primary">
              确认加入
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.home-page { padding: 24px 32px; height: 100%; overflow-y: auto; }

/* ====== 批量操作栏 ====== */
.batch-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; margin-bottom: 16px;
  background: #fff; border: 1px solid var(--border); border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.batch-count { font-size: 13px; font-weight: 600; color: var(--text-main); margin-right: auto; }
.batch-btn {
  padding: 6px 16px; border-radius: 8px; font-size: 12px; border: 1px solid var(--border);
  background: #fff; cursor: pointer; transition: all 0.15s;
}
.batch-btn:hover { transform: translateY(-1px); }
.batch-btn-delete { color: #DC2626; border-color: #FCA5A5; }
.batch-btn-delete:hover { background: #FEF2F2; }
.batch-btn-collection { color: var(--primary); border-color: rgba(200,93,93,0.2); }
.batch-btn-collection:hover { background: var(--primary-glow); }
.batch-btn-cancel { color: var(--text-muted); }
.batch-btn-cancel:hover { background: rgba(0,0,0,0.03); }

/* ====== 标签筛选 ====== */
.tag-bar { display: flex; gap: 6px; overflow-x: auto; margin-bottom: 20px; padding-bottom: 4px; align-items: center; }
.tag-bar::-webkit-scrollbar { display: none; }
.tag-bar { -ms-overflow-style: none; scrollbar-width: none; }
.tag-chip {
  flex-shrink: 0; padding: 4px 14px; border-radius: 16px; font-size: 12px; cursor: pointer;
  background: var(--bg-surface); border: 1px solid var(--border); color: var(--text-muted);
  transition: all 0.2s;
}
.tag-chip:hover { color: var(--text-main); }
.tag-chip.active { background: var(--primary-glow); border-color: var(--primary); color: var(--primary); font-weight: 500; }

.select-all-chip {
  flex-shrink: 0; display: flex; align-items: center; gap: 4px; padding: 4px 12px;
  font-size: 11px; color: var(--text-muted); cursor: pointer; margin-left: 8px;
}
.select-all-chip input { accent-color: var(--primary); width: 14px; height: 14px; cursor: pointer; }

.clear-all-chip {
  flex-shrink: 0; margin-left: auto; padding: 4px 12px; border-radius: 4px;
  font-size: 10px; font-family: var(--font-mono); color: #DC2626;
  background: none; border: 1px solid transparent; cursor: pointer;
  transition: all 0.15s;
}
.clear-all-chip:hover { border-color: #FCA5A5; background: #FEF2F2; }

/* ====== 卡片 + 复选框 ====== */
.card-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px; padding-bottom: 40px; position: relative;
}
.card-wrapper { position: relative; }
.card-check {
  position: absolute; top: 12px; left: 12px; z-index: 5;
  width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
  background: #fff; border: 2px solid var(--border); border-radius: 4px;
  opacity: 0; transition: opacity 0.15s;
}
.card-check.visible { opacity: 1; }
.card-check input { position: absolute; opacity: 0; cursor: pointer; }
.card-check:has(input:checked) {
  background: var(--primary); border-color: var(--primary);
  opacity: 1;
}
.card-check:has(input:checked)::after {
  content: "✓"; color: #fff; font-size: 12px; font-weight: 700;
}
.card-selected { outline: 2px solid var(--primary); outline-offset: -2px; border-radius: 14px; }

/* ====== 新建卡片 ====== */
.create-card {
  border: 2px dashed var(--border); border-radius: var(--radius-pro);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.3s; color: var(--text-muted);
  min-height: 230px;
}
.create-card:hover { border-color: var(--primary); color: var(--primary); }
.create-plus { font-size: 24px; font-weight: 300; transition: transform 0.3s; }
.create-card:hover .create-plus { transform: scale(1.15); }
.create-label { font-size: 11px; font-weight: 700; font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px; }

/* ====== 空状态 ====== */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 120px 0; border: 1px solid var(--border); border-radius: 16px;
  background: var(--bg-surface);
}
.empty-title { font-size: 13px; color: var(--text-muted); font-weight: 700; }
.empty-code { font-size: 9px; font-family: var(--font-mono); color: var(--text-muted); margin-top: 6px; text-transform: uppercase; letter-spacing: 0.05em; }

/* ====== 弹窗通用 ====== */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50; background: rgba(0,0,0,0.4); backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
}
.modal-card {
  background: #fff; border-radius: 16px; padding: 24px; width: 440px;
  border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 20px 40px rgba(0,0,0,0.08);
  animation: scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid rgba(0,0,0,0.05); margin-bottom: 16px; }
.modal-title { font-size: 14px; font-weight: 700; color: #2C2421; }
.modal-close { background: none; border: none; font-size: 16px; color: #A0A0A0; cursor: pointer; }
.modal-close:hover { color: #000; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 16px; }

.btn-cancel { padding: 8px 18px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.08); background: #F5F5F5; color: #666; font-size: 12px; cursor: pointer; }
.btn-primary { padding: 8px 18px; border-radius: 10px; border: none; background: var(--primary); color: #fff; font-size: 12px; font-weight: 700; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { background: #B04F4F; }
.btn-danger { padding: 8px 18px; border-radius: 10px; border: none; background: #DC2626; color: #fff; font-size: 12px; font-weight: 700; cursor: pointer; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger:hover:not(:disabled) { background: #B91C1C; }

.delete-confirm-text { font-size: 13px; color: #2C2421; line-height: 1.6; }
.delete-label { font-size: 10px; font-family: var(--font-mono); color: #8C7A76; text-transform: uppercase; display: block; margin-bottom: 8px; }
.delete-warn { font-size: 11px; color: #8C7A76; background: rgba(220,38,38,0.04); padding: 12px; border-radius: 10px; border: 1px solid rgba(220,38,38,0.08); line-height: 1.6; }

.clear-all-input {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  border: 1px solid var(--border); background: var(--bg-surface);
  font-size: 14px; font-family: var(--font-mono); color: #2C2421;
  outline: none; margin-bottom: 4px;
}
.clear-all-input:focus { border-color: #DC2626; }

.collection-select {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  border: 1px solid var(--border); background: var(--bg-surface);
  font-size: 13px; color: #2C2421; outline: none;
}

@keyframes scaleIn { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.modal-enter-active, .modal-leave-active { transition: opacity 0.3s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .home-page { padding: 16px; }
  .card-grid { grid-template-columns: 1fr; }
  .batch-bar { flex-wrap: wrap; }
  .modal-card { width: 90%; margin: 0 16px; }
}
</style>
