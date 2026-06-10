<script setup lang="ts">
</script>

<template>
  <div class="default-layout">
    <main class="main-content">
      <router-view />
    </main>
    <LofterTabbar v-if="$route.meta.tab" />
  </div>
</template>

<style scoped>
.default-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}
</style>
