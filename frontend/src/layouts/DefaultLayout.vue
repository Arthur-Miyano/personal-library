<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useArticleStore } from '@/stores/article'
import { articlesApi, collectionsApi } from '@/api'
import api from '@/api'
import { inject } from 'vue'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const articleStore = useArticleStore()
const changeTheme = inject<(t: string) => void>('changeTheme') || (() => {})
const currentTheme = inject('currentTheme') || 'cinnabar'

// --- 面板状态 ---
const profileDrawer = ref(false)
const uploadModal = ref(false)
const deleteModal = ref(false)
const rotating = ref(false)
const searchQuery = ref('')
const activeShelf = ref('all')

// --- 上传状态 ---
const uploadType = ref<'single' | 'batch'>('single')
const uploadTarget = ref<'article' | 'novel'>('article')
const enableRetypeset = ref(true)
const uploadDragover = ref(false)
const uploadProgress = ref(false)
const uploadError = ref('')

// --- 删除状态 ---
const deleteScope = ref<'selected' | 'all'>('selected')

// --- 侧边栏数据 ---
const navItems = [
  { id: 'bookshelf', name: '文章', icon: 'grid', route: '/home', idx: 1 },
  { id: 'explore', name: '合集', icon: 'compass', route: '/collections', idx: 2 },
  { id: 'tags', name: '标签', icon: 'git-network', route: '/tags', idx: 3 },
  { id: 'novels', name: '小说', icon: 'bookmark', route: '/novels', idx: 4 },
]

const themes = [
  { id: 'cinnabar', color: '#C85D5D' },
  { id: 'azure', color: '#5A849B' },
  { id: 'jade', color: '#6A8D73' },
  { id: 'ink', color: '#D4C4B7' },
]

const shelves = ref<{ id: string; name: string; count: number }[]>([
  { id: 'all', name: '全本典藏总目', count: 0 },
])

async function loadShelves() {
  try {
    const { data } = await collectionsApi.list()
    const list = Array.isArray(data) ? data : (data.items ?? [])
    shelves.value = [
      { id: 'all', name: '全本典藏总目', count: 0 },
      ...list.map((c: any) => ({ id: c.id, name: c.name, count: c.articles?.length || 0 })),
    ]
  } catch { /* */ }
}

const user = ref({
  nickname: '书斋主人',
  avatar: 'https://api.dicebear.com/7.x/bottts-neutral/svg?seed=Felix',
  readingTime: 0,
})

const qAvatars = [
  'https://api.dicebear.com/7.x/adventurer/svg?seed=Bob',
  'https://api.dicebear.com/7.x/adventurer/svg?seed=Anya',
  'https://api.dicebear.com/7.x/adventurer/svg?seed=Jack',
  'https://api.dicebear.com/7.x/adventurer/svg?seed=Lily',
]

// --- 计算属性 ---
const activeNav = computed(() => route.meta?.navId || 'bookshelf')
const currentNavTitle = computed(() => navItems.find(n => n.id === activeNav.value)?.name || '文章')

const activeShelfName = computed(() => {
  const s = shelves.value.find(s => s.id === activeShelf.value)
  return s && activeShelf.value !== 'all' ? s.name : ''
})

const searchPlaceholder = computed(() => {
  const map: Record<string, string> = { bookshelf: '搜索文章...', explore: '搜索合集...', tags: '搜索标签...', novels: '搜索小说...' }
  return map[activeNav.value as string] || '搜索...'
})

// --- 方法 ---
function navTo(path: string) { router.push(path) }
function selectShelf(id: string) { activeShelf.value = id }

function rotateSecretKey() {
  if (rotating.value) return
  rotating.value = true
  setTimeout(() => { rotating.value = false }, 1800)
}

function logout() { appStore.logout(); router.push('/login') }

// 上传：核心上传逻辑，直接接受文件列表
async function uploadFiles(files: FileList | File[]) {
  uploadProgress.value = true
  uploadError.value = ''

  try {
    const fileList = Array.from(files)
    if (uploadTarget.value === 'novel') {
      for (const file of fileList) {
        const form = new FormData()
        form.append('file', file)
        await api.post('/novels/upload', form)
      }
      router.push('/novels')
    } else {
      for (const file of fileList) {
        const form = new FormData()
        form.append('file', file)
        await api.post('/upload', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      }
      await articleStore.fetchArticles()
    }
    uploadModal.value = false
  } catch (e: unknown) {
    const err = e as any
    const detail = err?.response?.data?.detail || err?.message || '上传失败，请检查文件格式和大小'
    uploadError.value = `${detail}`
  } finally {
    uploadProgress.value = false
  }
}

function onFileInputChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    uploadFiles(input.files)
    input.value = ''
  }
}

function onUploadDragOver(e: DragEvent) {
  e.preventDefault()
  uploadDragover.value = true
}
function onUploadDragLeave() {
  uploadDragover.value = false
}
function onUploadDrop(e: DragEvent) {
  e.preventDefault()
  uploadDragover.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    uploadFiles(e.dataTransfer.files)
  }
}

// 删除：根据范围调用后端 API
function executeDeleteStrategy() {
  deleteModal.value = false
  if (deleteScope.value === 'all') {
    // 批量清空：逐个删除当前列表中的文章
    articleStore.articles.forEach(a => articlesApi.delete(a.id).catch(() => {}))
    articleStore.articles = []
  }
}

// 阅读心流计时器
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  timer = setInterval(() => { user.value.readingTime += 1 }, 60000)
  loadShelves()
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="app-layout">
    <!-- ========================================== 侧边栏 ========================================== -->
    <aside class="sidebar">
      <div class="sidebar-pad">
        <div class="logo-row">
          <div class="logo-dot"></div>
          <span class="logo-text">藏卷小筑</span>
        </div>

        <!-- 主导航：文章 / 合集 / 标签 -->
        <nav class="nav-wrap">
          <div v-for="item in navItems" :key="item.id"
            class="nav-item" :class="{ active: activeNav === item.id }"
            @click="navTo(item.route)">
            <div v-if="activeNav === item.id" class="nav-bar"></div>
            <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path v-if="item.id === 'bookshelf'" d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <path v-if="item.id === 'explore'" d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              <path v-if="item.id === 'tags'" d="M18 20V10M12 20V4M6 20v-6" />
              <path v-if="item.id === 'novels'" d="M4 20V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2z" />
            </svg>
            <span class="nav-label">{{ item.name }}</span>
            <span class="nav-idx">// 0{{ item.idx }}</span>
          </div>
        </nav>

        <!-- 底部 -->
        <div class="sidebar-bottom">
          <div class="theme-dots">
            <button v-for="t in themes" :key="t.id" @click="changeTheme(t.id)"
              class="dot" :class="{ active: currentTheme === t.id }"
              :style="{ background: t.color }">
            </button>
          </div>
          <div class="user-row" @click="profileDrawer = true">
            <div class="user-avatar">
              <img :src="user.avatar" class="user-img" alt="avatar" />
            </div>
            <div class="user-info">
              <span class="user-name">{{ user.nickname }}</span>
              <span class="user-role">书斋主人</span>
            </div>
            <svg class="user-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </div>
        </div>
      </div>
    </aside>

    <!-- ========================================== 主内容区 ========================================== -->
    <main class="main-area">
      <header class="top-header">
        <div>
          <h2 class="top-title serif-text">{{ currentNavTitle }}</h2>
          <!-- 标签筛选指示器 -->
          <div v-if="articleStore.activeTagName" class="active-tag-indicator">
            <span>筛选:</span>
            <span class="active-tag-chip">
              # {{ articleStore.activeTagName }}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                class="tag-close-icon" @click="articleStore.clearTag()">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </span>
          </div>
          <!-- 书架筛选指示器 -->
          <span v-if="activeShelfName" class="shelf-filter-badge">
            {{ activeShelfName }}
          </span>
        </div>
        <div class="header-right">
          <span class="reading-time">READING: {{ user.readingTime }} MIN</span>
          <div class="top-search">
            <svg class="top-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input v-model="searchQuery" type="text" :placeholder="searchPlaceholder" class="top-search-input" />
          </div>
        </div>
      </header>

      <div class="content-scroll">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :current-shelf="activeShelf" :search-key="searchQuery" />
          </transition>
        </router-view>
      </div>

      <!-- ====== 双轨浮动按钮 ====== -->
      <div class="dual-fab">
        <button class="fab-pill fab-delete" @click="router.push('/trash')" title="回收站">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>

        <button class="fab-pill fab-upload" @click="uploadModal = true" title="上传">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </button>
      </div>

      <!-- ========================================== 上传对话框 ========================================== -->
      <Transition name="modal">
        <div v-if="uploadModal" class="modal-overlay" @click.self="uploadModal = false">
          <div class="modal-card">
            <div class="modal-header">
              <h3 class="modal-title serif-text">新建内容</h3>
              <button @click="uploadModal = false" class="modal-close">✕</button>
            </div>

            <!-- 第一组：文章 / 小说 -->
            <div class="upload-tab-group">
              <button
                @click="uploadTarget = 'article'"
                :class="uploadTarget === 'article' ? 'upload-tab-active' : 'upload-tab'"
              >文章</button>
              <button
                @click="uploadTarget = 'novel'"
                :class="uploadTarget === 'novel' ? 'upload-tab-active' : 'upload-tab'"
              >小说</button>
            </div>

            <!-- 第二组：单篇编写 / 批量导入（仅文章） -->
            <div v-if="uploadTarget === 'article'" class="upload-tab-group">
              <button
                @click="uploadType = 'single'"
                :class="uploadType === 'single' ? 'upload-tab-active' : 'upload-tab'"
              >单篇编写</button>
              <button
                @click="uploadType = 'batch'"
                :class="uploadType === 'batch' ? 'upload-tab-active' : 'upload-tab'"
              >批量导入</button>
            </div>

            <!-- 上传区域 -->
            <div
              class="upload-zone"
              :class="{ 'upload-zone-active': uploadDragover }"
              @dragover="onUploadDragOver"
              @dragleave="onUploadDragLeave"
              @drop="onUploadDrop"
            >
              <template v-if="uploadProgress">
                <span class="upload-zone-text">正在上传中...</span>
              </template>
              <template v-else-if="uploadError">
                <span class="upload-zone-text" style="color: #DC2626;">{{ uploadError }}</span>
              </template>
              <template v-else-if="uploadTarget === 'article' && uploadType === 'single'">
                <span class="upload-zone-text" @click="uploadModal = false; router.push('/editor')" style="cursor:pointer;">点击进入编辑器编写文章</span>
              </template>
              <template v-else>
                <!-- 文件选择：点击区域任意位置触发 -->
                <input
                  type="file"
                  :accept="uploadTarget === 'novel' ? '.txt,.epub,.pdf' : '.txt,.md,.html,.epub,.pdf,.docx'"
                  :multiple="uploadType === 'batch' || uploadTarget === 'novel'"
                  class="upload-file-input"
                  @change="onFileInputChange"
                  @click.stop
                />
                <span class="upload-zone-text">
                  {{ uploadTarget === 'novel' ? '点击选择或拖拽 TXT / EPUB 小说文件' : '点击选择或拖拽文件批量导入' }}
                </span>
                <span class="upload-zone-hint">
                  {{ uploadTarget === 'novel' ? '支持 .txt .epub .pdf' : '支持 .txt .md .html .epub .pdf .docx' }}
                </span>
              </template>
            </div>

            <div v-if="uploadTarget === 'novel'" class="upload-typeset">
              <div class="typeset-info">
                <span class="typeset-label">智能排版与正文提纯</span>
                <span class="typeset-desc">自动识别并删除广告、推广行与错乱空行</span>
              </div>
              <input type="checkbox" v-model="enableRetypeset" class="typeset-check" />
            </div>

            <div class="modal-actions">
              <button @click="uploadModal = false; uploadError = ''" class="btn-cancel">取消</button>
              <button
                v-if="uploadTarget === 'article' && uploadType === 'single'"
                @click="triggerUpload"
                class="btn-primary"
              >开始编写</button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- ========================================== 删除对话框 ========================================== -->
      <Transition name="modal">
        <div v-if="deleteModal" class="modal-overlay" @click.self="deleteModal = false">
          <div class="modal-card" style="width: 400px;">
            <div class="modal-header">
              <h3 class="modal-title serif-text" style="color: #C85D5D;">批量删除</h3>
              <button @click="deleteModal = false" class="modal-close">✕</button>
            </div>

            <div class="delete-body">
              <label class="delete-label">删除范围</label>
              <select v-model="deleteScope" class="delete-select">
                <option value="selected">当前筛选结果中的所有文章</option>
                <option value="all">清空全部文章</option>
              </select>

              <p class="delete-warn">
                删除后将移入回收站，可在回收站中恢复或永久删除。
              </p>
            </div>

            <div class="modal-actions">
              <button @click="deleteModal = false" class="btn-cancel">取消</button>
              <button @click="executeDeleteStrategy" class="btn-danger">确认删除</button>
            </div>
          </div>
        </div>
      </Transition>
    </main>

    <!-- ========================================== 个人配置面板 ========================================== -->
    <Transition name="slide-right">
      <div v-if="profileDrawer" class="profile-panel">
        <div class="profile-inner">
          <div class="profile-header">
            <h3 class="profile-title">个人设置</h3>
            <button @click="profileDrawer = false" class="modal-close">✕</button>
          </div>

          <div class="profile-body">
            <!-- 头像 -->
            <label class="profile-label">头像</label>
            <div class="profile-avatar-row">
              <img :src="user.avatar" class="profile-avatar-lg" alt="avatar" />
              <div class="q-avatar-grid">
                <div
                  v-for="(qa, idx) in qAvatars"
                  :key="idx"
                  @click="user.avatar = qa"
                  class="q-avatar-item"
                  :class="{ 'q-avatar-selected': user.avatar === qa }"
                >
                  <img :src="qa" class="q-avatar-img" alt="Q avatar" />
                </div>
              </div>
            </div>

            <!-- 昵称 -->
            <div class="profile-field">
              <label class="profile-label">昵称</label>
              <input v-model="user.nickname" class="profile-input" placeholder="书斋主人" />
            </div>

            <!-- 密钥状态 -->
            <div class="profile-key">
              <div class="ac-key-row">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" :style="{ color: 'var(--primary)' }">
                  <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
                </svg>
                <span>加密状态</span>
              </div>
              <p class="ac-key-desc">AES-256-GCM 加密保护中</p>
              <button class="ac-key-btn" @click="rotateSecretKey">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" :class="{ 'animate-spin': rotating }">
                  <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                <span>{{ rotating ? '轮换中...' : '轮换主密钥' }}</span>
              </button>
            </div>

            <!-- 引擎指标 -->
            <div class="ac-stats">
              <div class="ac-stat"><div class="ac-stat-l">LSH 命中率</div><div class="ac-stat-v">99.2%</div></div>
              <div class="ac-stat"><div class="ac-stat-l">分组准确率</div><div class="ac-stat-v">98.5%</div></div>
            </div>
          </div>

          <div class="profile-footer">
            <span class="profile-version">V4.0.0</span>
            <button @click="logout" class="profile-logout">退出登录</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="profileDrawer || uploadModal || deleteModal" class="panel-mask"
        @click="profileDrawer = false; uploadModal = false; deleteModal = false"></div>
    </Transition>
  </div>
</template>

<style scoped>
/* ======================================== 布局 ======================================== */
.app-layout { display: flex; min-height: 100vh; background: #FDFBF7; }

/* ======================================== 侧边栏 ======================================== */
.sidebar {
  width: 240px; flex-shrink: 0; position: fixed; top: 0; left: 0; bottom: 0; z-index: 20;
  background: #fff; border-right: 1px solid rgba(0,0,0,0.05);
  display: flex; flex-direction: column;
}
.sidebar-pad { display: flex; flex-direction: column; height: 100%; padding: 32px 12px; }
.logo-row { display: flex; align-items: center; gap: 10px; padding: 0 12px 24px; border-bottom: 1px solid rgba(0,0,0,0.05); margin-bottom: 16px; }
.logo-dot { width: 14px; height: 14px; background: #C85D5D; border-radius: 2px; flex-shrink: 0; }
.logo-text { font-family: var(--font-serif); font-weight: 900; font-size: 12px; color: #2C2421; letter-spacing: 0.2em; text-transform: uppercase; }

/* 导航 */
.nav-wrap { display: flex; flex-direction: column; gap: 2px; padding: 0 4px; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 10px;
  cursor: pointer; color: #8C7A76; transition: all 0.2s; position: relative;
}
.nav-item:hover { background: rgba(0,0,0,0.03); color: #2C2421; }
.nav-item.active { background: #FDFBF7; color: #2C2421; font-weight: 600; }
.nav-bar { position: absolute; left: 0; top: 6px; bottom: 6px; width: 2px; background: #C85D5D; border-radius: 2px; }
.nav-svg { width: 16px; height: 16px; flex-shrink: 0; }
.nav-label { font-size: 13px; letter-spacing: 0.03em; flex: 1; }
.nav-idx { font-size: 9px; font-family: var(--font-mono); opacity: 0.4; }

/* 书架 */
.shelves-section { padding: 14px 8px 0; border-top: 1px solid rgba(0,0,0,0.05); margin-top: 10px; }
.shelves-title { font-size: 10px; font-family: var(--font-mono); color: #8C7A76; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; padding: 0 8px; }
.shelves-list { display: flex; flex-direction: column; gap: 2px; max-height: 160px; overflow-y: auto; }
.shelves-list::-webkit-scrollbar { display: none; }
.shelf-item {
  width: 100%; text-align: left; padding: 7px 12px; border-radius: 10px; border: none; background: none;
  font-size: 12px; cursor: pointer; color: #8C7A76;
  display: flex; align-items: center; justify-content: space-between; transition: all 0.15s;
}
.shelf-item:hover { background: rgba(0,0,0,0.03); color: #2C2421; }
.shelf-item.active { background: #FDFBF7; color: #C85D5D; font-weight: 600; }
.shelf-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.shelf-count {
  font-size: 9px; font-family: var(--font-mono); background: #FAFAFA;
  padding: 1px 6px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.05); color: #A0A0A0; flex-shrink: 0;
}

.sidebar-bottom { border-top: 1px solid rgba(0,0,0,0.05); padding-top: 12px; margin-top: auto; }
.theme-dots { display: flex; gap: 8px; padding: 0 12px 10px; }
.dot { width: 16px; height: 16px; border-radius: 50%; border: none; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.dot:hover { transform: scale(1.15); }
.dot.active { outline: 2px solid #C85D5D; outline-offset: 2px; transform: scale(1.1); }
.user-row { display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.user-row:hover { background: rgba(0,0,0,0.03); }
.user-avatar { width: 32px; height: 32px; border-radius: 50%; overflow: hidden; border: 1px solid rgba(0,0,0,0.08); flex-shrink: 0; }
.user-img { width: 100%; height: 100%; object-fit: cover; }
.user-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.user-name { font-size: 12px; font-weight: 600; color: #2C2421; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-role { font-size: 8px; color: #8C7A76; font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.05em; }
.user-arrow { width: 12px; height: 12px; flex-shrink: 0; color: #8C7A76; }

/* ======================================== 主区域 ======================================== */
.main-area { flex: 1; margin-left: 240px; display: flex; flex-direction: column; min-height: 100vh; }
.top-header {
  height: 64px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 40px; border-bottom: 1px solid rgba(0,0,0,0.05);
  background: #fff; position: sticky; top: 0; z-index: 10;
}
.top-title { font-size: 14px; font-weight: 700; font-family: var(--font-serif); color: #2C2421; text-transform: uppercase; letter-spacing: 0.02em; }
.header-right { display: flex; align-items: center; gap: 16px; }
.reading-time { font-size: 10px; font-family: var(--font-mono); color: #8C7A76; }

/* 标签筛选指示器 */
.active-tag-indicator { display: flex; align-items: center; gap: 6px; margin-top: 4px; font-size: 10px; color: var(--text-muted); }
.active-tag-chip {
  display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px;
  font-family: var(--font-mono); font-size: 10px; background: #C85D5D; color: #fff;
}
.tag-close-icon { width: 10px; height: 10px; cursor: pointer; opacity: 0.7; }
.tag-close-icon:hover { opacity: 1; }
.shelf-filter-badge {
  display: inline-block; margin-top: 4px; font-size: 10px; font-family: var(--font-mono);
  background: #fff; border: 1px solid rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 4px; color: #8C7A76;
}

/* 搜索 */
.top-search { position: relative; }
.top-search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; color: #8C7A76; }
.top-search-input {
  width: 190px; padding: 8px 14px 8px 38px; border-radius: 20px;
  border: 1px solid rgba(0,0,0,0.08); background: #FDFBF7;
  color: #2C2421; font-size: 12px; outline: none; font-family: var(--font-mono);
  transition: all 0.3s;
}
.top-search-input:focus { width: 250px; border-color: #C85D5D; }
.top-search-input::placeholder { color: #8C7A76; }
.content-scroll { flex: 1; overflow-y: auto; }

/* ======================================== 双轨 FAB ======================================== */
.dual-fab {
  position: fixed; bottom: 32px; right: 32px; z-index: 40;
  display: flex; align-items: center; gap: 10px;
  background: #fff; padding: 6px; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}
.fab-pill { width: 40px; height: 40px; border-radius: 10px; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
.fab-pill:active { transform: scale(0.95); }
.fab-delete { background: #FEF2F2; color: #DC2626; }
.fab-delete:hover { background: #FEE2E2; }
.fab-upload { background: #C85D5D; color: #fff; box-shadow: 0 4px 12px rgba(200,93,93,0.2); }
.fab-upload:hover { background: #B04F4F; }

/* ======================================== 对话框 ======================================== */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50; background: rgba(0,0,0,0.4); backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
}
.modal-card {
  background: #fff; border-radius: 16px; padding: 28px; width: 440px;
  border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 20px 40px rgba(0,0,0,0.08);
  animation: scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid rgba(0,0,0,0.05); margin-bottom: 18px; }
.modal-title { font-size: 14px; font-weight: 700; color: #2C2421; }
.modal-close { background: none; border: none; font-size: 16px; color: #A0A0A0; cursor: pointer; }
.modal-close:hover { color: #000; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 18px; }

.btn-cancel { padding: 8px 18px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.08); background: #F5F5F5; color: #666; font-size: 12px; cursor: pointer; }
.btn-primary { padding: 8px 18px; border-radius: 10px; border: none; background: #C85D5D; color: #fff; font-size: 12px; font-weight: 700; cursor: pointer; }
.btn-primary:hover { background: #B04F4F; }
.btn-danger { padding: 8px 18px; border-radius: 10px; border: none; background: #DC2626; color: #fff; font-size: 12px; font-weight: 700; cursor: pointer; }
.btn-danger:hover { background: #B91C1C; }

/* 上传 */
.upload-tab-group { display: flex; background: #FDFBF7; border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; padding: 3px; margin-bottom: 14px; }
.upload-tab, .upload-tab-active { flex: 1; padding: 8px; border-radius: 8px; border: none; font-size: 12px; cursor: pointer; transition: all 0.2s; background: transparent; color: #A0A0A0; }
.upload-tab-active { background: #fff; color: #2C2421; font-weight: 700; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.upload-zone {
  border: 2px dashed rgba(0,0,0,0.1); border-radius: 12px; padding: 28px;
  text-align: center; background: rgba(253,251,247,0.3); margin-bottom: 14px;
  transition: border-color 0.2s;
}
.upload-zone { cursor: pointer; position: relative; }
.upload-zone:hover { border-color: #C85D5D; }
.upload-zone-active { border-color: #C85D5D; background: rgba(200,93,93,0.04); }
.upload-file-input {
  position: absolute; inset: 0; opacity: 0; cursor: pointer;
  width: 100%; height: 100%;
}
.upload-zone-text { font-size: 11px; font-family: var(--font-mono); color: #8C7A76; letter-spacing: 0.03em; line-height: 1.6; }
.upload-zone-hint { font-size: 10px; font-family: var(--font-mono); color: #A0A0A0; display: block; margin-top: 6px; }
.upload-typeset {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px; border-radius: 10px; background: #FDFBF7; border: 1px solid rgba(0,0,0,0.05);
}
.typeset-label { font-size: 12px; font-weight: 700; color: #2C2421; display: block; }
.typeset-desc { font-size: 10px; color: #8C7A76; margin-top: 2px; }
.typeset-check { width: 16px; height: 16px; accent-color: #C85D5D; cursor: pointer; }

/* 删除 */
.delete-body { margin-bottom: 4px; }
.delete-label { font-size: 10px; font-family: var(--font-mono); color: #8C7A76; text-transform: uppercase; display: block; margin-bottom: 8px; }
.delete-select {
  width: 100%; background: #FDFBF7; border: 1px solid rgba(0,0,0,0.05);
  border-radius: 10px; padding: 12px; font-size: 12px; outline: none; color: #2C2421; margin-bottom: 14px;
}
.delete-warn {
  font-size: 11px; color: #8C7A76; background: rgba(220,38,38,0.04); padding: 12px;
  border-radius: 10px; border: 1px solid rgba(220,38,38,0.08); line-height: 1.6;
}

/* ======================================== 个人设置面板 ======================================== */
.profile-panel {
  position: fixed; top: 0; right: 0; bottom: 0; width: 380px; z-index: 50;
  background: #fff; border-left: 1px solid rgba(0,0,0,0.05);
  display: flex; flex-direction: column; box-shadow: -10px 0 40px rgba(0,0,0,0.05);
}
.profile-inner { display: flex; flex-direction: column; height: 100%; }
.profile-header { display: flex; align-items: center; justify-content: space-between; padding: 22px 24px; border-bottom: 1px solid rgba(0,0,0,0.05); }
.profile-title { font-size: 12px; font-weight: 700; font-family: var(--font-mono); color: #2C2421; text-transform: uppercase; letter-spacing: 0.05em; }
.profile-body { flex: 1; overflow-y: auto; padding: 20px 24px; }
.profile-label { font-size: 10px; font-family: var(--font-mono); color: #8C7A76; text-transform: uppercase; display: block; margin-bottom: 8px; }
.profile-avatar-row { display: flex; gap: 14px; margin-bottom: 16px; align-items: flex-start; }
.profile-avatar-lg { width: 52px; height: 52px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.08); flex-shrink: 0; }
.q-avatar-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; flex: 1; }
.q-avatar-item { padding: 3px; border-radius: 10px; cursor: pointer; border: 2px solid transparent; transition: all 0.2s; background: #FAFAFA; }
.q-avatar-item:hover { border-color: #ddd; }
.q-avatar-selected { border-color: #C85D5D; }
.q-avatar-img { width: 100%; display: block; border-radius: 6px; }
.profile-field { margin-bottom: 18px; }
.profile-input {
  width: 100%; background: #FDFBF7; border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px; padding: 10px 14px; font-size: 13px; font-weight: 600;
  color: #2C2421; outline: none; transition: border-color 0.2s;
}
.profile-input:focus { border-color: #C85D5D; }

.profile-key { padding: 14px; border: 1px solid rgba(0,0,0,0.05); border-radius: 10px; background: #FDFBF7; margin-bottom: 18px; }
.ac-key-row { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 500; color: #2C2421; margin-bottom: 6px; }
.ac-key-row svg { width: 14px; height: 14px; flex-shrink: 0; }
.ac-key-desc { font-size: 10px; color: #8C7A76; margin-bottom: 10px; }
.ac-key-btn {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px; border: 1px solid rgba(0,0,0,0.05); border-radius: 8px;
  background: #fff; color: #2C2421; font-size: 10px; cursor: pointer; transition: all 0.2s;
}
.ac-key-btn svg { width: 12px; height: 12px; flex-shrink: 0; }
.ac-key-btn:hover { background: rgba(0,0,0,0.03); }

.ac-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ac-stat { padding: 12px; border: 1px solid rgba(0,0,0,0.05); border-radius: 10px; background: #fff; }
.ac-stat-l { font-size: 9px; color: #8C7A76; margin-bottom: 4px; font-family: var(--font-mono); }
.ac-stat-v { font-size: 14px; font-weight: 700; font-family: var(--font-mono); color: #2C2421; }

.profile-footer { display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; border-top: 1px solid rgba(0,0,0,0.05); }
.profile-version { font-size: 9px; font-family: var(--font-mono); color: #A0A0A0; text-transform: uppercase; }
.profile-logout { font-size: 9px; font-weight: 700; color: #C85D5D; background: none; border: none; cursor: pointer; font-family: var(--font-mono); text-transform: uppercase; }
.profile-logout:hover { text-decoration: underline; }

.panel-mask { position: fixed; inset: 0; z-index: 30; background: rgba(0,0,0,0.04); }

/* ======================================== 动画 ======================================== */
.slide-right-enter-active, .slide-right-leave-active { transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); opacity: 0; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.modal-enter-active, .modal-leave-active { transition: opacity 0.3s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
@keyframes scaleIn { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* ======================================== 响应式 ======================================== */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .main-area { margin-left: 0; }
  .top-header { padding: 0 16px; height: 56px; }
  .top-search-input { width: 120px; }
  .top-search-input:focus { width: 160px; }
  .profile-panel { width: 100%; }
  .modal-card { width: 90%; margin: 0 16px; }
  .reading-time { display: none; }
}
</style>
