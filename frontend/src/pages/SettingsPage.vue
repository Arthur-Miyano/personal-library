<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { settingsApi, fontsApi } from '@/api'
import type { UserSettings } from '@/types'

const router = useRouter()
const settings = ref<UserSettings>({
  theme_mode: 'light', bg_color: '#FFFFFF', bg_opacity: 1,
  font_family: 'system-ui', font_size: 16, line_height: 1.9,
  paragraph_spacing: 12, reader_max_width: 800,
  first_line_indent: true, default_reformat: false,
})
const fonts = ref<{ id: string; font_family: string }[]>([])

onMounted(async () => {
  const [s, f] = await Promise.all([settingsApi.get(), fontsApi.list()])
  Object.assign(settings.value, s.data)
  fonts.value = f.data
})

async function save(key: string, value: unknown) {
  await settingsApi.update({ [key]: value })
}
</script>

<template>
  <div class="settings-page">
    <h2>阅读设置</h2>
    <div class="setting-item">
      <span>字体</span>
      <el-select :model-value="settings.font_family" style="width:180px"
        @change="(v: string) => { settings.font_family = v; save('font_family', v) }">
        <el-option label="system-ui" value="system-ui" />
        <el-option label="思源黑体" value="Noto Sans SC" />
        <el-option label="苹方" value="PingFang SC" />
        <el-option label="宋体" value="SimSun" />
        <el-option label="楷体" value="KaiTi" />
        <el-option v-for="f in fonts" :key="f.id" :label="f.font_family" :value="f.font_family" />
      </el-select>
      <el-button text size="small" @click="router.push('/fonts')">管理字体</el-button>
    </div>
    <div class="setting-item">
      <span>字体大小</span>
      <el-slider :model-value="settings.font_size" :min="12" :max="32" style="width:200px"
        @change="(v: number) => { settings.font_size = v; save('font_size', v) }" />
      <span>{{ settings.font_size }}px</span>
    </div>
    <div class="setting-item">
      <span>行高</span>
      <el-slider :model-value="settings.line_height" :min="1.2" :max="3.0" :step="0.1" style="width:200px"
        @change="(v: number) => { settings.line_height = v; save('line_height', v) }" />
      <span>{{ settings.line_height }}</span>
    </div>
    <div class="setting-item">
      <span>阅读宽度</span>
      <el-slider :model-value="settings.reader_max_width" :min="400" :max="1200" :step="50" style="width:200px"
        @change="(v: number) => { settings.reader_max_width = v; save('reader_max_width', v) }" />
      <span>{{ settings.reader_max_width }}px</span>
    </div>
    <div class="setting-item">
      <span>首行缩进</span>
      <el-switch :model-value="settings.first_line_indent"
        @change="(v: boolean) => { settings.first_line_indent = v; save('first_line_indent', v) }" />
    </div>
    <div class="setting-item">
      <span>背景颜色</span>
      <el-color-picker :model-value="settings.bg_color"
        @change="(v: string | null) => { if (v) { settings.bg_color = v; save('bg_color', v) } }" />
    </div>
  </div>
</template>

<style scoped>
.settings-page { padding: 12px 16px; }
.settings-page h2 { font-size: 20px; margin-bottom: 16px; }
.setting-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.setting-item > span:first-child { width: 80px; font-size: 15px; flex-shrink: 0; }
</style>
