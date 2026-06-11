import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshPromise: Promise<string> | null = null

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config
    if (!originalRequest) return Promise.reject(err)

    if (err.response?.status === 401) {
      const url = originalRequest.url || ''
      if (['/auth/login', '/auth/register', '/auth/token', '/auth/refresh'].some(p => url.includes(p))) {
        return Promise.reject(err)
      }

      if (!refreshPromise) {
        refreshPromise = authApi.refresh()
          .then((r) => {
            const token = r.data.access_token as string
            localStorage.setItem('token', token)
            return token
          })
          .catch((refreshErr) => {
            localStorage.removeItem('token')
            window.location.replace('/login')
            throw refreshErr
          })
          .finally(() => {
            refreshPromise = null
          })
      }

      try {
        const newToken = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch {
        return Promise.reject(err)
      }
    }
    return Promise.reject(err)
  },
)

// Auth
export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  refresh: () => api.post('/auth/refresh'),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data: { nickname?: string }) => api.patch('/auth/profile', data),
}

// Articles
export const articlesApi = {
  list: (params?: { tag_id?: string }) => api.get('/articles', { params }),
  get: (id: string) => api.get(`/articles/${id}`),
  create: (data: { title: string; raw_text: string }) => api.post('/articles', data),
  update: (id: string, data: { title?: string; raw_text?: string }) =>
    api.patch(`/articles/${id}`, data),
  delete: (id: string) => api.delete(`/articles/${id}`),
  trash: () => api.get('/articles/trash/list'),
  restore: (id: string) => api.patch(`/articles/${id}/restore`),
  permanentDelete: (id: string) => api.delete(`/articles/${id}/permanent`),
  addTag: (articleId: string, tagId: string) =>
    api.post(`/articles/${articleId}/tags/${tagId}`),
  removeTag: (articleId: string, tagId: string) =>
    api.delete(`/articles/${articleId}/tags/${tagId}`),
  batchAddTag: (data: { article_ids: string[]; tag_id: string }) =>
    api.post('/articles/batch-tag', data),
  batchSetTags: (articleId: string, data: { tag_ids: string[] }) =>
    api.post(`/articles/${articleId}/tags/batch`, data),
}

// Tags
export const tagsApi = {
  list: () => api.get('/tags'),
  create: (data: { name: string; color?: string }) => api.post('/tags', data),
  delete: (id: string) => api.delete(`/tags/${id}`),
}

// Collections
export const collectionsApi = {
  list: () => api.get('/collections'),
  get: (id: string) => api.get(`/collections/${id}`),
  create: (data: { name: string; description?: string; color?: string; icon?: string }) =>
    api.post('/collections', data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/collections/${id}`, data),
  addArticle: (collectionId: string, articleId: string) =>
    api.post(`/collections/${collectionId}/articles/${articleId}`),
  removeArticle: (collectionId: string, articleId: string) =>
    api.delete(`/collections/${collectionId}/articles/${articleId}`),
  updateArticleSort: (collectionId: string, articleId: string, sortOrder: number) =>
    api.patch(`/collections/${collectionId}/articles/${articleId}/sort`, null, {
      params: { sort_order: sortOrder },
    }),
  batchAddArticles: (collectionId: string, data: { article_ids: string[] }) =>
    api.post(`/collections/${collectionId}/articles/batch`, data),
  moveArticle: (collectionId: string, articleId: string, direction: 'up' | 'down') =>
    api.post(`/collections/${collectionId}/articles/${articleId}/move`, { direction }),
  delete: (id: string) => api.delete(`/collections/${id}`),
}

// Settings
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: Record<string, unknown>) => api.patch('/settings', data),
}

// Novels
export const novelsApi = {
  list: (params?: { page?: number; size?: number }) => api.get('/novels', { params }),
  get: (id: string) => api.get(`/novels/${id}`),
  update: (id: string, data: { title?: string; author?: string }) =>
    api.patch(`/novels/${id}`, data),
  delete: (id: string) => api.delete(`/novels/${id}`),
  getChapter: (novelId: string, chapterId: string) =>
    api.get(`/novels/${novelId}/chapters/${chapterId}`),
  updateChapter: (novelId: string, chapterId: string, data: { title?: string; chapter_number?: number; content?: string }) =>
    api.patch(`/novels/${novelId}/chapters/${chapterId}`, data),
  getProgress: (novelId: string) => api.get(`/novels/${novelId}/progress`),
  updateProgress: (novelId: string, data: { chapter_id: string; percentage: number; updated_at?: string }) =>
    api.put(`/novels/${novelId}/progress`, data),
  upload: (form: FormData) => api.post('/novels/upload', form, { timeout: 120000 }),
  batchDelete: (ids: string[]) => api.post('/novels/batch-delete', { novel_ids: ids }),
  trash: () => api.get('/novels/trash'),
  restore: (id: string) => api.patch(`/novels/${id}/restore`),
  permanentDelete: (id: string) => api.delete(`/novels/${id}/permanent`),
}

// Fonts
export const fontsApi = {
  list: () => api.get('/fonts'),
  upload: (form: FormData) => api.post('/fonts', form),
  delete: (id: string) => api.delete(`/fonts/${id}`),
}

// Admin
export const adminApi = {
  importPath: (data: { subpath: string; collection_name?: string; encoding?: string; encoding_errors?: string }) =>
    api.post('/admin/import-path', data),
  getImportProgress: (taskId: string) => api.get(`/admin/import-path/${taskId}`),
}

export default api
