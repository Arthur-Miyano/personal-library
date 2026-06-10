<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { articlesApi, collectionsApi, tagsApi } from '@/api'
import type { Article, Collection, Tag } from '@/types'
import { ArrowLeft } from '@element-plus/icons-vue'
import FindReplaceDialog from '@/components/FindReplaceDialog.vue'

const route = useRoute()
const router = useRouter()
const article = ref<Article | null>(null)
const id = route.params.id as string
const findVisible = ref(false)

const collections = ref<Collection[]>([])
const tags = ref<Tag[]>([])
const collDialog = ref(false)
const tagDialog = ref(false)
const selectedColl = ref('')
const selectedTags = ref<string[]>([])

onMounted(async () => {
  const { data } = await articlesApi.get(id)
  article.value = data
})

async function loadMeta() {
  const [cRes, tRes] = await Promise.all([collectionsApi.list(), tagsApi.list()])
  collections.value = cRes.data
  tags.value = tRes.data
}

async function openCollDialog() { await loadMeta(); collDialog.value = true }
async function openTagDialog() { await loadMeta(); tagDialog.value = true; selectedTags.value = [] }

async function addToCollection() {
  if (!selectedColl.value) return
  try {
    await collectionsApi.addArticle(selectedColl.value, id)
    ElMessage.success('已加入合集')
    collDialog.value = false
  } catch { ElMessage.error('操作失败') }
}

async function applyTags() {
  for (const tagId of selectedTags.value) {
    try { await articlesApi.addTag(id, tagId) } catch { /* skip duplicates */ }
  }
  ElMessage.success('标签已更新')
  tagDialog.value = false
}

async function onReplace(newText: string) {
  if (!article.value) return
  try {
    await articlesApi.update(id, { raw_text: newText })
    article.value.raw_text = newText
    findVisible.value = false
    ElMessage.success('替换完成')
  } catch { ElMessage.error('替换失败') }
}
</script>

<template>
  <div class="reader-page" v-if="article">
    <header class="reader-header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <span class="header-title">{{ article.title }}</span>
      <el-button text @click="findVisible = true">替换</el-button>
      <el-button text type="primary" @click="router.push(`/editor?id=${id}`)">编辑</el-button>
    </header>

    <div class="meta-bar">
      <span v-for="tag in article.tags" :key="tag.id" class="lofter-tag" :style="{ backgroundColor: tag.color + '20', color: tag.color }">{{ tag.name }}</span>
      <span class="word-count">{{ article.word_count }}字</span>
    </div>

    <article class="content" :style="{ maxWidth: '800px', margin: '0 auto', lineHeight: 1.9, fontSize: '16px' }">
      <h2>{{ article.title }}</h2>
      <div v-html="article.raw_text?.replace(/\n/g, '<br>')"></div>
    </article>

    <footer class="reader-footer">
      <el-button @click="openCollDialog">加入合集</el-button>
      <el-button @click="openTagDialog">打标签</el-button>
    </footer>

    <FindReplaceDialog :visible="findVisible" :content="article.raw_text"
      @close="findVisible = false" @apply="onReplace" />

    <el-dialog v-model="collDialog" title="加入合集" width="300px">
      <el-select v-model="selectedColl" placeholder="选择合集" style="width:100%">
        <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <template #footer><el-button @click="collDialog=false">取消</el-button><el-button type="primary" @click="addToCollection">确定</el-button></template>
    </el-dialog>

    <el-dialog v-model="tagDialog" title="打标签" width="300px">
      <el-checkbox-group v-model="selectedTags">
        <el-checkbox v-for="t in tags" :key="t.id" :value="t.id" :label="t.name" />
      </el-checkbox-group>
      <template #footer><el-button @click="tagDialog=false">取消</el-button><el-button type="primary" @click="applyTags">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.reader-page { min-height: 100vh; padding-bottom: 60px; }
.reader-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; position: sticky; top: 0; background: var(--el-bg-color); z-index: 10; }
.header-title { flex: 1; font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta-bar { padding: 0 16px 12px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.word-count { font-size: 13px; color: var(--el-text-color-secondary); }
.content { padding: 16px; }
.content h2 { font-size: 20px; margin-bottom: 16px; text-align: center; letter-spacing: 1px; }
.reader-footer { position: fixed; bottom: 0; left: 0; right: 0; display: flex; gap: 12px; justify-content: center; padding: 12px; background: var(--el-bg-color); border-top: 1px solid var(--el-border-color-lighter); }
</style>
