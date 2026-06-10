<script setup lang="ts">
import type { Article } from '@/types'

defineProps<{ article: Article }>()
const emit = defineEmits<{ click: []; tagClick: [tagId: string] }>()

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div
    class="tactile-book-card bg-white rounded-xl p-5 flex flex-col justify-between relative cursor-pointer"
    @click="$emit('click')"
  >
    <div>
      <!-- 顶行元数据 -->
      <div class="flex justify-between items-center mb-3">
        <span class="text-[9px] font-mono text-[#8C7A76] tracking-wider uppercase">
          {{ article.source_type?.toUpperCase() || 'ARTICLE' }} · {{ article.id.slice(0, 4).toUpperCase() }}
        </span>
        <span class="text-[10px] font-mono text-neutral-300">
          {{ article.word_count || 0 }} 字
        </span>
      </div>

      <!-- 标题 -->
      <h3 class="serif-text text-base font-bold leading-snug line-clamp-1 text-[#2C2421] card-title-hover">
        {{ article.title }}
      </h3>

      <!-- 摘要 -->
      <p class="text-xs text-[#8C7A76] mt-2.5 line-clamp-3 leading-relaxed text-justify">
        {{ Array.from(article.raw_text || '').slice(0, 140).join('') || '暂无内容摘要...' }}
      </p>
    </div>

    <!-- 底部：标签 + 日期 -->
    <div class="mt-3 pt-3 border-t border-black/5 flex items-center justify-between">
      <div v-if="article.tags?.length" class="flex gap-1.5 overflow-x-auto no-scrollbar max-w-[75%]">
        <span
          v-for="tag in article.tags"
          :key="tag.id"
          class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#FDFBF7] text-[#8C7A76] border border-black/5 whitespace-nowrap cursor-pointer hover:text-[#C85D5D] hover:border-[#C85D5D]/20 transition-colors"
          @click.stop="$emit('tagClick', tag.id)"
        >
          #{{ tag.name }}
        </span>
      </div>
      <span class="text-[9px] font-mono text-neutral-300 uppercase ml-auto">
        {{ fmtDate(article.created_at) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.serif-text { font-family: var(--font-serif); }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

/* ====== 3D 实体书卷厚度层叠 ====== */

.tactile-book-card {
  border: 1px solid rgba(62, 41, 37, 0.08);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 1px 2px rgba(62, 41, 37, 0.03),
    0 4px 12px rgba(62, 41, 37, 0.03);
  transition:
    transform 0.4s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 第二层纸张底衬 */
.tactile-book-card::before {
  content: "";
  position: absolute;
  width: 97%;
  height: 100%;
  left: 1.5%;
  bottom: -4px;
  background: #ffffff;
  border: 1px solid rgba(62, 41, 37, 0.07);
  border-radius: 12px;
  z-index: -1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 第三层纸张底衬 */
.tactile-book-card::after {
  content: "";
  position: absolute;
  width: 94%;
  height: 100%;
  left: 3%;
  bottom: -8px;
  background: #FCF9F5;
  border: 1px solid rgba(62, 41, 37, 0.05);
  border-radius: 12px;
  z-index: -2;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.01);
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 悬浮：物理位移 + 环境光晕染 */
.tactile-book-card:hover {
  transform: translateY(-8px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 12px 28px -4px rgba(62, 41, 37, 0.07),
    0 24px 48px -8px rgba(200, 93, 93, 0.04);
}
.tactile-book-card:hover::before {
  transform: translateY(2px);
}
.tactile-book-card:hover::after {
  transform: translateY(4px);
}

/* 标题悬停变色 */
.card-title-hover {
  transition: color 0.3s;
}
.tactile-book-card:hover .card-title-hover {
  color: #C85D5D;
}
</style>
