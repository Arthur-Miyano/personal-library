<script setup lang="ts">
defineProps<{ items: { name: string; reason: string }[] }>()
</script>

<template>
  <div class="failure-list" v-if="items.length">
    <h4>失败详情 ({{ items.length }})</h4>
    <div v-for="(f, i) in items" :key="i" class="item">
      <span class="name">{{ f.name }}</span>
      <span class="reason">{{ f.reason }}</span>
    </div>
  </div>
</template>

<style scoped>
.failure-list { margin-top: 12px; max-height: 200px; overflow-y: auto; }
h4 { font-size: 14px; margin-bottom: 4px; color: #F56C6C; }
.item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; border-bottom: 1px solid var(--el-border-color-lighter); }
.name { color: var(--el-text-color-regular); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 60%; }
.reason { color: #F56C6C; flex-shrink: 0; }
</style>
