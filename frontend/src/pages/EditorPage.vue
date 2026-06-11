<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { articlesApi, tagsApi } from '@/api'
import { ArrowLeft, Upload } from '@element-plus/icons-vue'
import type { Tag } from '@/types'
import type { UploadRawFile } from 'element-plus'

const route = useRoute()
const router = useRouter()
const articleId = ref(Array.isArray(route.query.id) ? route.query.id[0] : (route.query.id as string) || '')
const title = ref('')
const rawText = ref('')
const saving = ref(false)
const uploading = ref(false)
const localTags = ref<Tag[]>([])
const newTagName = ref('')

function addLocalTag() {
  const name = newTagName.value.trim()
  if (!name || localTags.value.some(t => t.name === name)) return
  localTags.value.push({ id: '', name, color: '#C85D5D' })
  newTagName.value = ''
}

function removeLocalTag(name: string) {
  localTags.value = localTags.value.filter(t => t.name !== name)
}

onMounted(async () => {
  if (articleId.value) {
    const { data } = await articlesApi.get(articleId.value)
    title.value = data.title
    rawText.value = data.raw_text
  }
})

async function save() {
  if (!title.value.trim()) { ElMessage.warning('请输入标题'); return }
  saving.value = true
  try {
    let aid = articleId.value
    if (aid) {
      await articlesApi.update(aid, { title: title.value, raw_text: rawText.value })
    } else {
      const { data } = await articlesApi.create({ title: title.value, raw_text: rawText.value })
      aid = data.id
      articleId.value = aid
      router.replace(`/editor?id=${aid}`)
    }
    // 批量关联暂存标签
    if (localTags.value.length > 0) {
      const results = await Promise.all(localTags.value.map(t => tagsApi.create({ name: t.name })))
      const tagIds = results.map(r => r.data.id)
      await articlesApi.batchSetTags(aid, { tag_ids: tagIds })
      localTags.value = []
    }
    router.push(`/reader/${aid}`)
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleFileUpload(rawFile: UploadRawFile) {
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', rawFile)
    const { data } = await api.post('/upload', form)
    articleId.value = data.id
    title.value = data.title
    rawText.value = data.raw_text
    router.replace(`/editor?id=${data.id}`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="editor-page">
    <header class="editor-header">
      <el-icon class="back-btn" @click="router.back()"><ArrowLeft /></el-icon>
      <span class="header-title">{{ articleId ? '编辑文章' : '新建文章' }}</span>
      <div class="header-actions">
        <el-upload
          :show-file-list="false"
          :before-upload="(f: UploadRawFile) => { handleFileUpload(f); return false }"
          accept=".txt,.md,.html,.epub,.pdf,.docx"
        >
          <el-button text :loading="uploading" :icon="Upload" />
        </el-upload>
        <el-button type="primary" size="small" :loading="saving" @click="save">保存</el-button>
      </div>
    </header>
    <el-input
      v-model="title"
      placeholder="文章标题"
      class="title-input"
      maxlength="500"
      show-word-limit
    />
    <div class="editor-tags">
      <span v-for="t in localTags" :key="t.name" class="editor-tag-chip">
        #{{ t.name }} <button @click="removeLocalTag(t.name)" class="editor-tag-remove">×</button>
      </span>
      <input v-model="newTagName" placeholder="+ 添加标签" class="editor-tag-input"
        @keydown.enter="addLocalTag" />
    </div>
    <el-input
      v-model="rawText"
      type="textarea"
      placeholder="开始写作，或点击右上角上传按钮导入文件..."
      class="content-input"
      :autosize="{ minRows: 15 }"
      resize="none"
    />
  </div>
</template>

<style scoped>
.editor-page { min-height: 100vh; }
.editor-header {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; background: var(--el-bg-color);
  position: sticky; top: 0; z-index: 10;
}
.header-title { flex: 1; font-size: 16px; font-weight: 600; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.title-input { padding: 12px 16px; }
.title-input :deep(.el-input__wrapper) { box-shadow: none; font-size: 20px; font-weight: 600; }
.content-input { padding: 0 16px; }
.content-input :deep(.el-textarea__inner) { box-shadow: none; font-size: 16px; line-height: 1.9; border: none; }

.editor-tags { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 8px 16px; }
.editor-tag-chip {
  padding: 3px 10px; border-radius: 16px; font-size: 11px; font-family: var(--font-mono);
  background: var(--primary-glow); color: var(--primary); border: 1px solid rgba(200,93,93,0.15);
  display: inline-flex; align-items: center; gap: 4px;
}
.editor-tag-remove { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 12px; padding: 0; opacity: 0.5; }
.editor-tag-remove:hover { opacity: 1; }
.editor-tag-input {
  border: none; border-bottom: 1px dashed var(--border); padding: 3px 6px;
  font-size: 12px; outline: none; color: var(--text-main); width: 100px;
}
.editor-tag-input:focus { border-color: var(--primary); }
</style>
