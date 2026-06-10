/**
 * 动态生成封面样式，基于 content_hash / id 稳定映射
 * 使用与主题色系匹配的柔和渐变
 */
export const getProceduralStyle = (id: string, hash?: string) => {
  const code = hash
    ? hash.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
    : id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
  const bucket = code & 1023
  const gradients = [
    'linear-gradient(135deg, rgba(200,93,93,0.04) 0%, rgba(200,93,93,0.10) 100%)',
    'linear-gradient(135deg, rgba(90,132,155,0.04) 0%, rgba(90,132,155,0.10) 100%)',
    'linear-gradient(135deg, rgba(106,141,115,0.04) 0%, rgba(106,141,115,0.10) 100%)',
    'linear-gradient(135deg, rgba(140,122,118,0.06) 0%, rgba(140,122,118,0.12) 100%)',
  ]
  return {
    background: gradients[bucket % gradients.length],
    boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.04)',
  }
}
