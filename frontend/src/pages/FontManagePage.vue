<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { fontsApi } from '@/api'
import type { UploadRawFile } from 'element-plus'

interface FontItem { id: string; filename: string; font_family: string; file_size: number }
const router = useRouter()
const fonts = ref<FontItem[]>([])
const uploading = ref(false)

onMounted(async () => {
  const { data } = await fontsApi.list()
  fonts.value = data
})

async function handleUpload(rawFile: UploadRawFile) {
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', rawFile)
    const { data } = await fontsApi.upload(form)
    fonts.value.unshift(data)
    ElMessage.success('字体上传成功')
  } catch { ElMessage.error('上传失败') }
  finally { uploading.value = false }
}

async function deleteFont(id: string) {
  try {
    await fontsApi.delete(id)
    fonts.value = fonts.value.filter(f => f.id !== id)
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
}

function formatSize(bytes: number) { return (bytes / 1024).toFixed(1) + ' KB' }
</script>

<template>
  <div class="font-page">
    <div class="page-header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <h2>字体管理</h2>
    </div>
    <el-upload
      :show-file-list="false"
      :before-upload="(f: UploadRawFile) => { handleUpload(f); return false }"
      accept=".ttf,.otf"
      :disabled="uploading"
    >
      <el-button type="primary" :loading="uploading">上传字体</el-button>
    </el-upload>

    <div class="font-list" v-if="fonts.length">
      <div v-for="f in fonts" :key="f.id" class="lofter-card font-item">
        <span class="family">{{ f.font_family }}</span>
        <span class="file-info">{{ f.filename }} · {{ formatSize(f.file_size) }}</span>
        <el-button text type="danger" size="small" @click="deleteFont(f.id)">删除</el-button>
      </div>
    </div>
    <el-empty v-else description="还没有上传字体" />
  </div>
</template>

<style scoped>
.font-page { padding: 12px 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; font-size: 20px; font-weight: 600; }
.font-list { margin-top: 16px; }
.font-item { display: flex; align-items: center; gap: 12px; }
.family { font-size: 16px; font-weight: 500; flex: 1; }
.file-info { font-size: 13px; color: var(--el-text-color-secondary); }
</style>
