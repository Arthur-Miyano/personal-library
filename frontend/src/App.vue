<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { watch } from 'vue'

const store = useAppStore()
if (store.isDark) document.documentElement.classList.add('dark')
watch(() => store.isDark, (v) => document.documentElement.classList.toggle('dark', v))
</script>

<template>
  <DefaultLayout />
</template>
