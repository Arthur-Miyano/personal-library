<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { tagsApi } from '@/api'
import type { Tag } from '@/types'

const router = useRouter()
const tags = ref<Tag[]>([])
const showNew = ref(false)
const newName = ref('')
const newColor = ref('#409EFF')

onMounted(async () => { const { data } = await tagsApi.list(); tags.value = data })

async function create() {
  if (!newName.value.trim()) return
  const { data } = await tagsApi.create({ name: newName.value.trim(), color: newColor.value })
  tags.value.unshift(data); newName.value = ''; showNew.value = false
}

async function remove(tag: Tag) {
  try { await ElMessageBox.confirm(`确定删除标签"${tag.name}"？`, '提示', { type: 'warning' }) } catch { return }
  await tagsApi.delete(tag.id)
  tags.value = tags.value.filter(t => t.id !== tag.id)
  ElMessage.success('已删除')
}
</script>

<template>
  <div class="tags-page">
    <div class="header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <h2>标签管理</h2>
      <el-button size="small" @click="showNew = true">新建</el-button>
    </div>

    <div v-if="showNew" class="new-form">
      <el-input v-model="newName" placeholder="标签名" size="small" />
      <el-color-picker v-model="newColor" size="small" />
      <el-button size="small" type="primary" @click="create">创建</el-button>
      <el-button size="small" @click="showNew = false">取消</el-button>
    </div>

    <div class="tag-list">
      <div v-for="t in tags" :key="t.id" class="tag-row">
        <span class="chip" :style="{ background: t.color + '30', color: t.color }">{{ t.name }}</span>
        <el-button text type="danger" size="small" @click="remove(t)">删除</el-button>
      </div>
    </div>
    <el-empty v-if="!tags.length" description="还没有标签" />
  </div>
</template>

<style scoped>
.tags-page { padding: 12px 16px; }
.header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
h2 { flex: 1; font-size: 20px; font-weight: 600; }
.new-form { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; }
.tag-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.chip { padding: 6px 14px; border-radius: 20px; font-size: 14px; font-weight: 500; }
</style>
