<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { articlesApi } from '@/api'
import { ArrowLeft, Upload } from '@element-plus/icons-vue'
import type { UploadRawFile } from 'element-plus'

const route = useRoute()
const router = useRouter()
const articleId = ref((route.query.id as string) || '')
const title = ref('')
const rawText = ref('')
const saving = ref(false)
const uploading = ref(false)

onMounted(async () => {
  if (articleId.value) {
    const { data } = await articlesApi.get(articleId.value)
    title.value = data.title
    rawText.value = data.raw_text
  }
})

async function save() {
  if (!title.value.trim()) return
  saving.value = true
  try {
    if (articleId.value) {
      await articlesApi.update(articleId.value, { title: title.value, raw_text: rawText.value })
    } else {
      const { data } = await articlesApi.create({ title: title.value, raw_text: rawText.value })
      articleId.value = data.id
      router.replace(`/editor?id=${data.id}`)
    }
    router.push(`/reader/${articleId.value}`)
  } finally {
    saving.value = false
  }
}

async function handleFileUpload(rawFile: UploadRawFile) {
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', rawFile)
    const { data } = await api.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    articleId.value = data.id
    title.value = data.title
    rawText.value = data.raw_text
    router.replace(`/editor?id=${data.id}`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    alert(detail || '上传失败')
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
</style>
