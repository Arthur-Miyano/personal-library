<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ visible: boolean; content: string }>()
const emit = defineEmits<{ close: []; apply: [newText: string] }>()

const findText = ref('')
const replaceText = ref('')
const caseSensitive = ref(false)
const matchCount = ref(0)
const matches = ref<number[]>([])

function doFind() {
  if (!findText.value) { matchCount.value = 0; matches.value = []; return }
  const flags = caseSensitive.value ? 'g' : 'gi'
  const re = new RegExp(findText.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), flags)
  const found = [...props.content.matchAll(re)]
  matches.value = found.map(m => m.index!)
  matchCount.value = found.length
}

watch(() => [findText.value, caseSensitive.value, props.content], doFind)

function replaceAll() {
  if (!findText.value) return
  const flags = caseSensitive.value ? 'g' : 'gi'
  const re = new RegExp(findText.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), flags)
  const newText = props.content.replace(re, replaceText.value)
  emit('apply', newText)
}
</script>

<template>
  <el-dialog :model-value="visible" title="查找替换" width="340px" @close="emit('close')" append-to-body>
    <el-input v-model="findText" placeholder="查找内容" clearable @input="doFind" />
    <el-input v-model="replaceText" placeholder="替换为" clearable class="mt-2" />
    <div class="options">
      <el-checkbox v-model="caseSensitive">区分大小写</el-checkbox>
      <span class="count" v-if="findText">找到 {{ matchCount }} 处</span>
    </div>
    <template #footer>
      <el-button @click="emit('close')">取消</el-button>
      <el-button type="primary" :disabled="matchCount === 0" @click="replaceAll">全部替换</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.mt-2 { margin-top: 12px; }
.options { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
.count { font-size: 13px; color: var(--el-text-color-secondary); }
</style>
