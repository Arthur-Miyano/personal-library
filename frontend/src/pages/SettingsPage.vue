<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsApi, fontsApi, authApi } from '@/api'
import type { UserSettings } from '@/types'
import { inject } from 'vue'
import { ElMessage } from 'element-plus'

const router = inject('router')
const changeTheme = inject<(t: string) => void>('changeTheme') || (() => {})

const isSuperuser = ref(false)
const settings = ref<UserSettings>({
  theme_mode: 'light', bg_color: '#FFFFFF', bg_opacity: 1,
  font_family: 'system-ui', font_size: 16, line_height: 1.9,
  paragraph_spacing: 12, reader_max_width: 800,
  first_line_indent: true, default_reformat: false,
})
const fonts = ref<{ id: string; font_family: string }[]>([])

onMounted(async () => {
  const [s, f, u] = await Promise.all([
    settingsApi.get(), fontsApi.list(),
    authApi.me().catch(() => ({ data: { is_superuser: false } })),
  ])
  Object.assign(settings.value, s.data)
  fonts.value = f.data
  isSuperuser.value = u.data.is_superuser
})

let debounceTimers: Record<string, ReturnType<typeof setTimeout>> = {}
function save(key: string, value: unknown) {
  clearTimeout(debounceTimers[key])
  debounceTimers[key] = setTimeout(() => {
    settingsApi.update({ [key]: value }).catch(() => {})
  }, 500)
}
</script>

<template>
  <div class="settings-page">
    <h2 class="page-title serif-text">阅读设置</h2>

    <div class="settings-section">
      <div class="setting-row">
        <span class="setting-label">字体</span>
        <select class="setting-select" :value="settings.font_family"
          @change="(e: any) => { settings.font_family = e.target.value; save('font_family', e.target.value) }">
          <option value="system-ui">system-ui</option>
          <option value="Noto Sans SC">思源黑体</option>
          <option value="PingFang SC">苹方</option>
          <option value="SimSun">宋体</option>
          <option value="KaiTi">楷体</option>
          <option v-for="f in fonts" :key="f.id" :value="f.font_family">{{ f.font_family }}</option>
        </select>
      </div>

      <div class="setting-row">
        <span class="setting-label">字号</span>
        <input type="range" :min="12" :max="32" :value="settings.font_size"
          @input="(e: any) => { settings.font_size = +e.target.value; save('font_size', +e.target.value) }" />
        <span class="setting-value">{{ settings.font_size }}px</span>
      </div>

      <div class="setting-row">
        <span class="setting-label">行高</span>
        <input type="range" :min="1.2" :max="3.0" step="0.1" :value="settings.line_height"
          @input="(e: any) => { settings.line_height = +e.target.value; save('line_height', +e.target.value) }" />
        <span class="setting-value">{{ settings.line_height }}</span>
      </div>

      <div class="setting-row">
        <span class="setting-label">阅读宽度</span>
        <input type="range" :min="400" :max="1200" step="50" :value="settings.reader_max_width"
          @input="(e: any) => { settings.reader_max_width = +e.target.value; save('reader_max_width', +e.target.value) }" />
        <span class="setting-value">{{ settings.reader_max_width }}px</span>
      </div>

      <div class="setting-row">
        <span class="setting-label">首行缩进</span>
        <label class="toggle">
          <input type="checkbox" :checked="settings.first_line_indent"
            @change="(e: any) => { settings.first_line_indent = e.target.checked; save('first_line_indent', e.target.checked) }" />
          <span class="toggle-knob"></span>
        </label>
      </div>

      <div class="setting-row">
        <span class="setting-label">段落间距</span>
        <input type="range" :min="0" :max="48" step="4" :value="settings.paragraph_spacing"
          @input="(e: any) => { settings.paragraph_spacing = +e.target.value; save('paragraph_spacing', +e.target.value) }" />
        <span class="setting-value">{{ settings.paragraph_spacing }}px</span>
      </div>

      <div class="setting-row">
        <span class="setting-label">背景色</span>
        <input type="color" :value="settings.bg_color"
          @input="(e: any) => { settings.bg_color = e.target.value; save('bg_color', e.target.value) }" />
      </div>
    </div>

    <div v-if="isSuperuser" class="admin-section">
      <h3 class="section-title">管理功能</h3>
      <button class="admin-btn" @click="ElMessage.info('请在侧边栏账号面板中操作')">服务器导入</button>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  padding: 24px 32px;
  max-width: 600px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--text-main);
}
.settings-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.setting-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}
.setting-label {
  width: 80px;
  font-size: 14px;
  color: var(--text-main);
  flex-shrink: 0;
}
.setting-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-surface);
  color: var(--text-main);
  font-size: 13px;
  outline: none;
}
.setting-select:focus { border-color: var(--primary); }
.setting-select option { background: var(--bg-surface); color: var(--text-main); }
.setting-value {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  min-width: 50px;
  text-align: right;
}

/* 自定义 range */
input[type="range"] {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: var(--border);
  outline: none;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary);
  cursor: pointer;
  border: 2px solid var(--bg-surface);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* 自定义 toggle */
.toggle {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  cursor: pointer;
}
.toggle input { display: none; }
.toggle-knob {
  position: absolute;
  inset: 0;
  background: var(--border);
  border-radius: 11px;
  transition: background 0.2s;
}
.toggle-knob::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 2px;
  bottom: 2px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle input:checked + .toggle-knob { background: var(--primary); }
.toggle input:checked + .toggle-knob::before { transform: translateX(18px); }

input[type="color"] {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  padding: 0;
  background: none;
}
input[type="color"]::-webkit-color-swatch-wrapper { padding: 2px; }
input[type="color"]::-webkit-color-swatch { border: 1px solid var(--border); border-radius: 6px; }

.admin-section {
  margin-top: 32px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-surface);
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.admin-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--text-main);
  font-size: 13px;
  cursor: pointer;
}
.admin-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

@media (max-width: 768px) {
  .settings-page { padding: 16px; }
}
</style>
