/**
 * 过程式封面生成引擎
 * 基于 content_hash (SHA256) 或 SimHash 分桶（1024 个桶），
 * 确保相同文章永远对应相同视觉风格，彻底摒弃对素材图片的依赖。
 */

const BUCKET_COUNT = 1024

const THEMES = [
  { bg: 'linear-gradient(135deg, #FDFBF7 0%, #EFE8E1 100%)', text: '#C85D5D' },
  { bg: 'linear-gradient(135deg, #F4F7F9 0%, #E0E8ED 100%)', text: '#5A849B' },
  { bg: 'linear-gradient(135deg, #F5F7F2 0%, #E3E8E3 100%)', text: '#6A8D73' },
] as const

function hashToBucket(hash: string): number {
  let n = 0
  for (let i = 0; i < hash.length; i++) {
    n = ((n << 5) - n + hash.charCodeAt(i)) | 0
  }
  return Math.abs(n) % BUCKET_COUNT
}

export interface ProceduralStyle {
  background: string
  color: string
  border: string
}

/**
 * 基于 content_hash 生成稳定的过程式封面样式。
 * 未来可扩展为接收 BigInt SimHash 直接分桶。
 */
export function getProceduralStyle(id: string, contentHash?: string): ProceduralStyle {
  const bucket = contentHash
    ? hashToBucket(contentHash)
    : hashToBucket(id)
  const theme = THEMES[bucket % THEMES.length]
  return {
    background: theme.bg,
    color: theme.text,
    border: '1px solid rgba(0,0,0,0.03)',
  }
}
