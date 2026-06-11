<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, FolderOpened } from '@element-plus/icons-vue'
import api, { collectionsApi } from '@/api'
import { useAppStore } from '@/stores/app'
import ProgressPanel from '@/components/ProgressPanel.vue'
import FailureList from '@/components/FailureList.vue'

const ALLOWED = ['.txt','.md','.html','.epub','.pdf','.docx']
const MAX_SIZE = 10 * 1024 * 1024
const MAX_TOTAL = 500 * 1024 * 1024
const MAX_COUNT = 2000

const router = useRouter()
const store = useAppStore()
const encoding = ref('auto')
const collections = ref<{id:string;name:string}[]>([])
const collectionId = ref('')
const newCollName = ref('')
const showNewColl = ref(false)

// Precheck
const rawFiles = ref<File[]>([])
const validFiles = ref<File[]>([])
const skippedExt = ref(0)
const skippedDup = ref(0)
const skippedBig = ref(0)
const skippedEmpty = ref(0)
const totalSize = ref(0)

// Upload state
const started = ref(false)
const paused = ref(false)
const cancelled = ref(false)
const done = ref(false)
const successCount = ref(0)
const duplicateCount = ref(0)
const failedCount = ref(0)
const currentFile = ref('')
const failures = ref<{name:string;reason:string}[]>([])
const orphanIds = ref<string[]>([])

let pending: File[] = []
let activeCount = 0
let controllers: AbortController[] = []

const orphanKey = computed(() => `orphan_articles_${store.token ? 'user' : 'anon'}`)

onMounted(() => {
  try { orphanIds.value = JSON.parse(localStorage.getItem(orphanKey.value) || '[]') }
  catch { /* */ }
  collectionsApi.list().then(r => collections.value = r.data)
})

onUnmounted(() => { controllers.forEach(c => c.abort()) })

watch(orphanIds, v => { try { localStorage.setItem(orphanKey.value, JSON.stringify(v)) } catch { /* */ } }, { deep: true })

function selectFolder(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  const all = Array.from(input.files)
  rawFiles.value = all
  skippedExt.value = 0; skippedDup.value = 0; skippedBig.value = 0; skippedEmpty.value = 0
  totalSize.value = 0
  const seen = new Set<string>()
  const valid: File[] = []

  for (const f of all.slice(0, MAX_COUNT)) {
    const key = f.webkitRelativePath || f.name
    if (seen.has(key)) { skippedDup.value++; continue }
    seen.add(key)
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED.includes(ext)) { skippedExt.value++; continue }
    if (f.size === 0) { skippedEmpty.value++; continue }
    if (f.size > MAX_SIZE) { skippedBig.value++; continue }
    totalSize.value += f.size
    valid.push(f)
  }
  if (totalSize.value > MAX_TOTAL) {
    ElMessage.error(`总大小 ${(totalSize.value/1024/1024).toFixed(0)}MB 超过 500MB 限制，请分批上传`)
    validFiles.value = []
    return
  }
  validFiles.value = valid
}

function drain() {
  while (!paused.value && !cancelled.value && pending.length && activeCount < 3) {
    activeCount++
    const file = pending.shift()!, ctrl = new AbortController()
    controllers.push(ctrl)
    uploadOne(file, ctrl).finally(() => {
      activeCount--
      controllers = controllers.filter(c => c !== ctrl)
      setTimeout(() => drain(), 0)
    })
  }
  if (pending.length === 0 && activeCount === 0 && started.value) {
    done.value = true
  }
}

async function uploadOne(file: File, ctrl: AbortController) {
  try {
    const form = new FormData(); form.append('file', file)
    if (encoding.value !== 'auto') form.append('encoding', encoding.value)
    const { data } = await api.post('/upload', form, { signal: ctrl.signal })
    if (collectionId.value) {
      try { await api.post(`/collections/${collectionId.value}/articles/${data.id}`) }
      catch { orphanIds.value.push(data.id) }
    }
    successCount.value++
  } catch (e: unknown) {
    if (cancelled.value) return
    const status = (e as {response?:{status?:number}}).response?.status
    if (status === 409) { duplicateCount.value++; return }
    failures.value.push({ name: file.name, reason: classify(e) })
    failedCount.value++
  }
  currentFile.value = file.name
}

function classify(e: unknown): string {
  const s = (e as {response?:{status?:number}}).response?.status
  const d = (e as {response?:{data?:{detail?:string}}})?.response?.data?.detail || ''
  if (s === 413 || d.includes('10MB')) return '文件过大'
  if (s === 415) return '格式不支持'
  if (s === 400 && d.includes('编码')) return '编码错误'
  if (s === 400 && d.includes('空')) return '文件为空'
  if (d) return d
  return '上传失败'
}

function start() {
  if (!validFiles.value.length) return
  started.value = true; paused.value = false; cancelled.value = false; done.value = false
  successCount.value = 0; duplicateCount.value = 0; failedCount.value = 0
  failures.value = []; pending = [...validFiles.value]; controllers = []
  drain()
}

function pause() { paused.value = true }
function resume() { paused.value = false; drain() }
async function cancelUpload() {
  try { await ElMessageBox.confirm(`已上传 ${successCount.value} 个文件将保留，确定取消？`, '提示', { type: 'warning' }) }
  catch { return }
  cancelled.value = true; pending.length = 0; controllers.forEach(c => c.abort()); done.value = true
}

async function createColl() {
  if (!newCollName.value.trim()) return
  const { data } = await collectionsApi.create({ name: newCollName.value })
  collections.value.unshift(data)
  collectionId.value = data.id
  showNewColl.value = false; newCollName.value = ''
}

async function batchAddOrphans() {
  let ok = 0
  const toAdd = [...orphanIds.value]
  for (const id of toAdd) {
    try { await api.post(`/collections/${collectionId.value}/articles/${id}`); ok++ }
    catch { /* */ }
  }
  orphanIds.value = orphanIds.value.filter(x => !toAdd.includes(x))
  ElMessage.success(`已补加 ${ok} 篇`)
}

const progress = computed(() => validFiles.value.length ? (successCount.value + duplicateCount.value + failedCount.value) / validFiles.value.length * 100 : 0)
const total = computed(() => validFiles.value.length)
const doneCount = computed(() => successCount.value + duplicateCount.value + failedCount.value)
</script>

<template>
  <div class="batch-page">
    <header class="header">
      <el-icon @click="router.back()"><ArrowLeft /></el-icon>
      <span>批量导入</span>
    </header>

    <div class="controls">
      <el-select v-model="collectionId" placeholder="选择合集" clearable style="flex:1">
        <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button v-if="!showNewColl" @click="showNewColl=true" size="small">+新建</el-button>
    </div>
    <div v-if="showNewColl" class="new-coll">
      <el-input v-model="newCollName" placeholder="合集名称" size="small" />
      <el-button size="small" type="primary" @click="createColl">创建</el-button>
      <el-button size="small" @click="showNewColl=false">取消</el-button>
    </div>

    <div class="encoding-row">
      <span>编码：</span>
      <el-select v-model="encoding" size="small" style="width:140px">
        <el-option label="自动识别" value="auto" />
        <el-option label="UTF-8" value="utf-8" />
        <el-option label="GBK" value="gbk" />
        <el-option label="GB18030" value="gb18030" />
      </el-select>
    </div>

    <div class="folder-pick" v-if="!started">
      <input type="file" webkitdirectory multiple @change="selectFolder" id="folderInput" style="display:none" />
      <label for="folderInput" class="pick-label">
        <el-icon size="32"><FolderOpened /></el-icon>
        <p>点击选择文件夹</p>
      </label>

      <div class="precheck" v-if="rawFiles.length">
        <p>扫描: {{ rawFiles.length }} 文件</p>
        <p v-if="skippedExt">跳过不支持: {{ skippedExt }}</p>
        <p v-if="skippedDup">跳过重复: {{ skippedDup }}</p>
        <p v-if="skippedEmpty">跳过空文件: {{ skippedEmpty }}</p>
        <p v-if="skippedBig">超过10MB: {{ skippedBig }}</p>
        <p class="valid">有效: {{ validFiles.length }} | {{ (totalSize/1024/1024).toFixed(1) }}MB</p>
      </div>
    </div>

    <ProgressPanel v-if="started"
      :progress="progress" :done="doneCount" :total="total"
      :success="successCount" :duplicate="duplicateCount" :failed="failedCount"
      :current="currentFile" :paused="paused"
    />

    <FailureList v-if="failures.length" :items="failures" />

    <div v-if="orphanIds.length" class="orphan-bar">
      ⚠ {{ orphanIds.length }} 篇未加入合集
      <el-button size="small" @click="batchAddOrphans">批量补加</el-button>
    </div>

    <div class="actions">
      <template v-if="!started">
        <el-button type="primary" :disabled="!validFiles.length" @click="start">开始上传</el-button>
      </template>
      <template v-else-if="!done">
        <el-button v-if="!paused" @click="pause">暂停</el-button>
        <el-button v-else type="primary" @click="resume">继续</el-button>
        <el-button type="danger" @click="cancelUpload">取消</el-button>
      </template>
      <template v-else>
        <el-button @click="router.push('/home')">返回首页</el-button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.batch-page { padding: 12px 16px; }
.header { display: flex; align-items: center; gap: 12px; padding: 8px 0 16px; font-size: 18px; font-weight: 600; }
.controls { display: flex; gap: 8px; margin-bottom: 8px; }
.new-coll { display: flex; gap: 8px; margin-bottom: 8px; }
.encoding-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 14px; }
.folder-pick { text-align: center; }
.pick-label { display: block; padding: 40px; border: 2px dashed var(--el-border-color); border-radius: 12px; cursor: pointer; margin-bottom: 12px; }
.pick-label p { margin-top: 8px; font-size: 14px; color: var(--el-text-color-secondary); }
.precheck { text-align: left; font-size: 13px; color: var(--el-text-color-secondary); line-height: 1.8; }
.precheck .valid { color: var(--el-color-primary); font-weight: 500; }
.orphan-bar { display: flex; align-items: center; gap: 8px; padding: 12px; background: #fdf6ec; border-radius: 8px; margin-top: 12px; font-size: 14px; }
.actions { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }
</style>
