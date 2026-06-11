<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { articlesApi, collectionsApi, tagsApi, settingsApi } from '@/api'
import type { Article, Collection, UserSettings } from '@/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const article = ref<Article | null>(null)
const isEditing = ref(false)
const newTagInput = ref('')
const editTitle = ref('')
const editContent = ref('')
const collections = ref<Collection[]>([])
const showCollectionPicker = ref(false)
const readerSettings = ref<UserSettings | null>(null)

const id = route.params.id as string

onMounted(async () => {
  try {
    const [aRes, cRes, sRes] = await Promise.all([
      articlesApi.get(id),
      collectionsApi.list(),
      settingsApi.get().catch(() => ({ data: null })),
    ])
    article.value = aRes.data
    editTitle.value = aRes.data.title
    editContent.value = aRes.data.raw_text
    collections.value = Array.isArray(cRes.data) ? cRes.data : (cRes.data.items ?? [])
    readerSettings.value = sRes.data
  } catch {
    article.value = null
  }
})

async function addToCollection(collectionId: string) {
  if (!article.value) return
  try {
    await collectionsApi.addArticle(collectionId, article.value.id)
    ElMessage.success('已加入合集')
    showCollectionPicker.value = false
  } catch {
    ElMessage.error('加入合集失败')
  }
}

const formattedParagraphs = computed(() => {
  if (!article.value?.raw_text) return []
  return article.value.raw_text.split('\n').filter(p => p.trim())
})

const byteSize = computed(() => {
  if (!article.value?.raw_text) return 0
  return new TextEncoder().encode(article.value.raw_text).length
})

async function addTag() {
  const name = newTagInput.value.trim()
  if (!name || !article.value) return
  try {
    // 后端 upsert：存在则返回已有标签，不存在则创建
    const { data: tag } = await tagsApi.create({ name })
    // 关联到文章
    if (!article.value.tags?.some(t => t.id === tag.id)) {
      await articlesApi.addTag(article.value.id, tag.id)
      if (!article.value.tags) article.value.tags = []
      article.value.tags.push(tag)
    }
    newTagInput.value = ''
  } catch { /* */ }
}

async function removeTag(tagId: string) {
  if (!article.value) return
  try {
    await articlesApi.removeTag(article.value.id, tagId)
    if (article.value.tags) {
      article.value.tags = article.value.tags.filter(t => t.id !== tagId)
    }
  } catch { /* */ }
}

function enterEdit() {
  if (!article.value) return
  editTitle.value = article.value.title
  editContent.value = article.value.raw_text
  isEditing.value = true
}

async function saveChanges() {
  if (!article.value) return
  try {
    await articlesApi.update(article.value.id, {
      title: editTitle.value,
      raw_text: editContent.value,
    })
    article.value.title = editTitle.value
    article.value.raw_text = editContent.value
    isEditing.value = false
  } catch {
    // 保存失败静默保持编辑模式
  }
}
</script>

<template>
  <div class="reader-overlay">
    <header class="reader-header">
      <div class="reader-meta">
        <span>ASSET_ID: {{ article?.id || '......' }}</span>
        <span>BYTE_SIZE: {{ byteSize }}B</span>
      </div>
      <div class="reader-actions">
        <button
          v-if="!isEditing"
          class="reader-btn reader-btn-edit"
          @click="enterEdit"
        >
          修改文献原稿
        </button>
        <button
          v-else
          class="reader-btn reader-btn-edit"
          @click="isEditing = false"
        >
          退出编辑模式
        </button>
        <div class="collection-picker" style="position:relative;">
          <button class="reader-btn reader-btn-edit" @click="showCollectionPicker = !showCollectionPicker">
            加入合集
          </button>
          <div v-if="showCollectionPicker" class="collection-dropdown">
            <div v-if="!collections.length" class="collection-dropdown-empty">暂无合集</div>
            <div v-for="c in collections" :key="c.id"
              class="collection-dropdown-item"
              @click="addToCollection(c.id)">
              {{ c.name }}
            </div>
          </div>
        </div>

        <button class="reader-btn reader-btn-exit" @click="router.back()">
          退出沉浸阅读
        </button>
      </div>
    </header>

    <!-- 加载 / 404 -->
    <div v-if="!article" class="reader-loading">
      <span class="text-[var(--text-muted)] text-xs">加载中...</span>
    </div>

    <!-- 阅读 / 编辑区 -->
    <div v-else class="reader-body">
      <div class="reader-content">

        <!-- 标签行 -->
        <div class="tag-row">
          <span class="tag-row-label">资产标签:</span>
          <span v-for="tag in article.tags" :key="tag.id"
            class="tag-chip group/tag">
            #{{ tag.name }}
            <span class="tag-remove" @click.stop="removeTag(tag.id)">×</span>
          </span>
          <input
            v-model="newTagInput"
            type="text"
            placeholder="+ 回车绑定新特征"
            class="tag-input"
            @keydown.enter="addTag"
          />
        </div>

        <div class="reader-divider"></div>

        <!-- 阅读模式 -->
        <div v-if="!isEditing" class="reader-view">
          <h1 class="reader-title serif-text">{{ article.title }}</h1>
          <div class="reader-text serif-text" :style="{
            fontSize: (readerSettings?.font_size || 16) + 'px',
            lineHeight: readerSettings?.line_height || 2.1,
            fontFamily: readerSettings?.font_family || 'system-ui',
            textIndent: readerSettings?.first_line_indent !== false ? '2em' : '0',
            maxWidth: (readerSettings?.reader_max_width || 800) + 'px',
          }" style="margin: 0 auto;">
            <p v-for="(p, i) in formattedParagraphs" :key="i" class="reader-p" :style="{
              marginBottom: (readerSettings?.paragraph_spacing ?? 12) + 'px',
            }">
              {{ p }}
            </p>
          </div>
        </div>

        <!-- 编辑模式 -->
        <div v-else class="editor-view">
          <div class="editor-field">
            <label class="editor-label">文献大标题修改</label>
            <input v-model="editTitle" class="editor-input editor-input-title serif-text"
              placeholder="修订标题..." />
          </div>
          <div class="editor-field">
            <label class="editor-label">原稿内容持久化重构区</label>
            <textarea v-model="editContent" rows="16" class="editor-textarea"
              placeholder="写入长文本正文..."></textarea>
          </div>
          <div class="editor-actions">
            <button class="editor-save" @click="saveChanges">
              保存并写入落盘加密快照
            </button>
          </div>
        </div>

        <!-- 阅读结束标记 -->
        <div class="reader-end">❖ ❖ ❖</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reader-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: var(--bg-base); display: flex; flex-direction: column;
}

/* 顶栏 */
.reader-header {
  height: 56px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 48px; border-bottom: 1px solid var(--border);
  background: var(--bg-surface); flex-shrink: 0;
}
.reader-meta { display: flex; align-items: center; gap: 20px; font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); }
.reader-actions { display: flex; align-items: center; gap: 12px; }
.reader-btn {
  font-size: 12px; padding: 6px 16px; border-radius: 10px; border: 1px solid var(--border);
  cursor: pointer; font-weight: 500; transition: all 0.2s;
}
.reader-btn-edit { background: var(--bg-surface); color: var(--text-main); }
.reader-btn-edit:hover { background: var(--bg-base); border-color: var(--primary); }
.reader-btn-exit { background: var(--text-main); color: #fff; border-color: var(--text-main); }
.reader-btn-exit:hover { opacity: 0.9; }

/* 加载 */
.reader-loading { flex: 1; display: flex; align-items: center; justify-content: center; }

/* 内容区 */
.reader-body { flex: 1; overflow-y: auto; padding: 0 24px; }
.reader-content { max-width: 720px; margin: 0 auto; padding: 48px 0 120px; }

/* 标签行 */
.tag-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.tag-row-label { font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-right: 4px; }
.tag-chip {
  font-size: 11px; font-family: var(--font-mono); padding: 3px 10px; border-radius: 20px;
  background: var(--primary-glow); color: var(--primary); border: 1px solid rgba(200, 93, 93, 0.1);
  display: inline-flex; align-items: center; gap: 4px;
}
.tag-remove { cursor: pointer; opacity: 0.4; font-weight: 900; font-family: sans-serif; font-size: 12px; }
.tag-remove:hover { opacity: 1; }
.tag-input {
  background: transparent; border: none; border-bottom: 1px dashed var(--border);
  font-size: 11px; font-family: var(--font-mono); padding: 3px 6px; outline: none;
  color: var(--text-main); width: 140px; transition: border-color 0.2s;
}
.tag-input:focus { border-color: var(--primary); }
.tag-input::placeholder { color: var(--text-muted); }

.reader-divider { margin: 24px 0; }

/* 阅读模式 */
.reader-view { animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.reader-title { font-size: 28px; font-weight: 900; line-height: 1.3; margin-bottom: 40px; letter-spacing: -0.01em; }
.reader-text { font-size: 16px; line-height: 2.1; text-align: justify; opacity: 0.95; }
.reader-p { text-indent: 2em; margin-bottom: 0.5em; white-space: pre-line; }

/* 编辑模式 */
.editor-view { animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.editor-field { margin-bottom: 20px; }
.editor-label { font-size: 9px; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase; display: block; margin-bottom: 6px; }
.editor-input {
  width: 100%; background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 16px; outline: none; color: var(--text-main);
  transition: border-color 0.2s;
}
.editor-input:focus { border-color: var(--primary); }
.editor-input-title { font-size: 20px; font-weight: 700; }
.editor-textarea {
  width: 100%; background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px; outline: none; color: var(--text-main);
  font-size: 14px; font-family: var(--font-mono); line-height: 1.8;
  resize: vertical; transition: border-color 0.2s;
}
.editor-textarea:focus { border-color: var(--primary); }
.editor-actions { display: flex; justify-content: flex-end; padding-top: 12px; }
.editor-save {
  padding: 10px 24px; background: var(--primary); color: #fff; border: none;
  border-radius: 12px; font-size: 12px; font-weight: 700; cursor: pointer;
  transition: all 0.2s; box-shadow: 0 2px 6px var(--primary-glow);
}
.editor-save:hover { opacity: 0.95; }
.editor-save:active { transform: scale(0.98); }

/* 结束标记 */
.reader-end { height: 80px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); opacity: 0.2; font-size: 14px; letter-spacing: 0.5em; user-select: none; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.collection-picker { position: relative; }
.collection-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: 4px;
  background: #fff; border: 1px solid rgba(0,0,0,0.08); border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08); min-width: 160px; z-index: 60;
  max-height: 200px; overflow-y: auto;
}
.collection-dropdown-item {
  padding: 8px 14px; font-size: 12px; cursor: pointer; color: #2C2421;
  transition: background 0.15s;
}
.collection-dropdown-item:hover { background: rgba(0,0,0,0.03); }
.collection-dropdown-empty { padding: 12px 14px; font-size: 11px; color: #8C7A76; text-align: center; }

@media (max-width: 768px) {
  .reader-header { padding: 0 16px; }
  .reader-content { padding: 24px 0 80px; }
  .reader-title { font-size: 22px; }
  .reader-text { font-size: 15px; }
}
</style>
