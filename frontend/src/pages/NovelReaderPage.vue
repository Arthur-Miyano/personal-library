<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { novelsApi } from '@/api'
import type { Novel, Chapter, ReadingProgress } from '@/types'
import { ArrowLeft } from '@element-plus/icons-vue'
import FindReplaceDialog from '@/components/FindReplaceDialog.vue'

const route = useRoute()
const router = useRouter()
const novelId = route.params.id as string
const novel = ref<Novel | null>(null)
const chapters = ref<Chapter[]>([])
const chapter = ref<Chapter | null>(null)
const progress = ref<ReadingProgress | null>(null)
const tocOpen = ref(false)
const editMode = ref(false)
const editContent = ref('')
const findVisible = ref(false)
const saving = ref(false)

onMounted(async () => {
  const { data: n } = await novelsApi.get(novelId)
  novel.value = n
  chapters.value = n.chapters || []
  try { const { data: p } = await novelsApi.getProgress(novelId); progress.value = p } catch { /* */ }
  if (progress.value?.chapter_id) {
    const idx = chapters.value.findIndex(c => c.id === progress.value!.chapter_id)
    await loadChapter(idx >= 0 ? idx : 0)
  } else if (chapters.value.length) {
    const first = chapters.value.find(c => !c.is_prologue) || chapters.value[0]
    await loadChapter(chapters.value.indexOf(first))
  }
})

async function loadChapter(index: number) {
  if (index < 0 || index >= chapters.value.length) return
  const c = chapters.value[index]
  const { data } = await novelsApi.getChapter(novelId, c.id)
  chapter.value = data
  tocOpen.value = false; editMode.value = false
  try { await novelsApi.updateProgress(novelId, { chapter_id: c.id, percentage: 0 }) } catch { /* */ }
}

function enterEdit() { editContent.value = chapter.value?.content || ''; editMode.value = true }

async function saveEdit() {
  if (!chapter.value) return
  saving.value = true
  try {
    await novelsApi.updateChapter(novelId, chapter.value.id, { content: editContent.value })
    chapter.value.content = editContent.value
    editMode.value = false
    ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

function onFindReplace(newText: string) {
  editContent.value = newText
  findVisible.value = false
}

function currentIndex() { return chapter.value ? chapters.value.findIndex(c => c.id === chapter.value!.id) : -1 }
</script>

<template>
  <div class="novel-reader">
    <header class="reader-header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <span class="title">{{ novel?.title }}</span>
      <template v-if="!editMode">
        <el-button text @click="enterEdit">编辑</el-button>
        <el-button text @click="tocOpen = !tocOpen">目录</el-button>
      </template>
      <template v-else>
        <el-button text @click="editMode = false">取消</el-button>
        <el-button text @click="findVisible = true">替换</el-button>
        <el-button text type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </header>

    <div v-if="tocOpen" class="toc-overlay" @click.self="tocOpen = false">
      <div class="toc-panel">
        <h3>目录 ({{ chapters.length }}章)</h3>
        <div v-for="(c, i) in chapters" :key="c.id" class="toc-item"
          :class="{ active: chapter?.id === c.id, prologue: c.is_prologue }" @click="loadChapter(i)">
          <span class="num">{{ c.is_prologue ? '序' : c.chapter_number }}</span>
          <span class="toc-title">{{ c.title }}</span>
          <el-tag v-if="c.needs_review" size="small" type="warning">待审</el-tag>
        </div>
      </div>
    </div>

    <div v-if="chapter" class="chapter-content" :style="{ maxWidth: '780px', margin: '0 auto' }">
      <h2 class="chapter-title">{{ chapter.title }}</h2>
      <div v-if="!editMode" class="content" v-html="chapter.content?.replace(/\n/g, '<br>')"></div>
      <el-input v-else v-model="editContent" type="textarea" :autosize="{ minRows: 15 }" resize="none" />

      <div class="nav">
        <el-button :disabled="currentIndex() <= 0" @click="loadChapter(currentIndex() - 1)">上一章</el-button>
        <span class="pos">{{ currentIndex() + 1 }} / {{ chapters.length }}</span>
        <el-button :disabled="currentIndex() >= chapters.length - 1" @click="loadChapter(currentIndex() + 1)">下一章</el-button>
      </div>
    </div>

    <FindReplaceDialog :visible="findVisible" :content="editContent"
      @close="findVisible = false" @apply="onFindReplace" />
  </div>
</template>

<style scoped>
.novel-reader { min-height: 100vh; }
.reader-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--el-bg-color); position: sticky; top: 0; z-index: 20; }
.reader-header .title { flex: 1; font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.toc-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 30; display: flex; justify-content: flex-end; }
.toc-panel { width: 75%; background: var(--el-bg-color); overflow-y: auto; padding: 20px 16px; border-radius: 12px 0 0 12px; }
.toc-panel h3 { font-size: 18px; margin-bottom: 12px; }
.toc-item { display: flex; align-items: center; gap: 8px; padding: 10px 8px; border-radius: 8px; cursor: pointer; }
.toc-item.active { background: var(--el-color-primary-light-9); }
.toc-item.prologue { opacity: 0.6; }
.num { width: 32px; text-align: center; font-size: 14px; color: var(--el-color-primary); font-weight: 500; }
.toc-title { flex: 1; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chapter-content { padding: 24px 16px 80px; }
.chapter-title { font-size: 22px; text-align: center; margin-bottom: 20px; letter-spacing: 1px; }
.content { font-size: 16px; line-height: 2; }
.nav { display: flex; justify-content: space-between; align-items: center; margin-top: 32px; }
.pos { font-size: 13px; color: var(--el-text-color-secondary); }
</style>
