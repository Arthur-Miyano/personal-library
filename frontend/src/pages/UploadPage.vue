<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UploadFilled } from '@element-plus/icons-vue'
import type { UploadRawFile } from 'element-plus'
import api from '@/api'

const router = useRouter()
const uploading = ref(false)

async function handleUpload(rawFile: UploadRawFile) {
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', rawFile)
    const { data } = await api.post('/upload', form)
    ElMessage.success('上传成功')
    router.replace(`/reader/${data.id}`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="upload-page">
    <header class="header">
      <el-icon class="back-btn" @click="router.back()"><ArrowLeft /></el-icon>
      <span>上传文件</span>
    </header>

    <div class="form">
      <el-upload
        drag
        :show-file-list="true"
        :before-upload="(f: UploadRawFile) => { handleUpload(f); return false }"
        accept=".txt,.md,.html,.epub,.pdf,.docx"
        :disabled="uploading"
      >
        <div class="upload-area">
          <el-icon size="40" color="var(--el-color-primary)"><UploadFilled /></el-icon>
          <p>点击或拖拽文件到此处</p>
          <p class="hint">支持 .txt .md .html .epub .pdf .docx，最大 10MB</p>
        </div>
      </el-upload>

      <div v-if="uploading" class="loading-text">正在导入，请稍候...</div>

      <div class="tips">
        <p>导入后可在阅读页使用查找替换功能修改内容</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-page { min-height: 100vh; }
.header {
  display: flex; align-items: center; gap: 12px;
  padding: 16px; font-size: 18px; font-weight: 600;
}
.form { padding: 0 16px; display: flex; flex-direction: column; gap: 16px; }
.upload-area { padding: 40px 0; text-align: center; }
.upload-area p { margin-top: 8px; font-size: 14px; color: var(--el-text-color-regular); }
.hint { font-size: 12px !important; color: var(--el-text-color-secondary) !important; }
.loading-text { text-align: center; color: var(--el-color-primary); padding: 20px; }
.tips { margin-top: 24px; text-align: center; font-size: 13px; color: var(--el-text-color-secondary); }
</style>
