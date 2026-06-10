import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { articlesApi, tagsApi } from '@/api'
import type { Article, Tag } from '@/types'

export const useArticleStore = defineStore('article', () => {
  const articles = ref<Article[]>([])
  const tags = ref<Tag[]>([])
  const activeTagId = ref<string | null>(null)
  const loading = ref(false)

  const filteredArticles = computed(() => {
    if (!activeTagId.value) return articles.value
    return articles.value.filter(a =>
      a.tags?.some(t => t.id === activeTagId.value),
    )
  })

  const activeTagName = computed(() => {
    if (!activeTagId.value) return null
    return tags.value.find(t => t.id === activeTagId.value)?.name ?? null
  })

  async function fetchArticles() {
    loading.value = true
    try {
      const { data } = await articlesApi.list()
      articles.value = Array.isArray(data) ? data : (data.items ?? [])
    } finally {
      loading.value = false
    }
  }

  async function fetchTags() {
    const { data } = await tagsApi.list()
    tags.value = data
  }

  async function init() {
    loading.value = true
    try {
      const [aRes, tRes] = await Promise.all([articlesApi.list(), tagsApi.list()])
      articles.value = Array.isArray(aRes.data) ? aRes.data : (aRes.data.items ?? [])
      tags.value = tRes.data
    } finally {
      loading.value = false
    }
  }

  function filterByTag(tagId: string) {
    activeTagId.value = tagId
  }

  function clearTag() {
    activeTagId.value = null
  }

  return {
    articles,
    tags,
    activeTagId,
    activeTagName,
    loading,
    filteredArticles,
    fetchArticles,
    fetchTags,
    init,
    filterByTag,
    clearTag,
  }
})
