<script setup lang="ts">
defineProps<{ progress: number; done: number; total: number; success: number; duplicate: number; failed: number; current: string; paused: boolean }>()
</script>

<template>
  <div class="progress-panel">
    <el-progress :percentage="Math.round(progress)" :stroke-width="8" :color="paused ? '#E8C4A0' : '#4A6FA5'" />
    <div class="stats">
      <span>{{ done }}/{{ total }}</span>
      <span class="s">成功: {{ success }}</span>
      <span class="d">跳过: {{ duplicate }}</span>
      <span class="f" v-if="failed">失败: {{ failed }}</span>
    </div>
    <div class="current" v-if="current">当前: {{ current }}</div>
    <div class="paused-tag" v-if="paused">⏸ 已暂停</div>
  </div>
</template>

<style scoped>
.progress-panel { margin: 16px 0; }
.stats { display: flex; gap: 12px; margin-top: 8px; font-size: 13px; color: var(--el-text-color-secondary); }
.stats .s { color: #67C23A; } .stats .d { color: #909399; } .stats .f { color: #F56C6C; }
.current { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.paused-tag { text-align: center; margin-top: 8px; font-size: 14px; color: #E6A23C; }
</style>
