export interface Article {
  id: string
  title: string
  raw_text: string
  word_count: number
  source_type: string
  source_name: string | null
  status: string
  is_deleted: boolean
  user_id: string
  created_at: string
  updated_at: string
  content_hash: string
  tags?: Tag[]
  collection?: Collection
}

export interface Tag {
  id: string
  name: string
  color: string
}

export interface Collection {
  id: string
  name: string
  description: string
  color: string
  icon: string
  sort_order: number
  articles?: Article[]
}

export interface UserSettings {
  theme_mode: string
  bg_color: string
  bg_opacity: number
  font_family: string
  font_size: number
  line_height: number
  paragraph_spacing: number
  reader_max_width: number
  first_line_indent: boolean
  default_reformat: boolean
}

export interface Novel {
  id: string
  title: string
  author: string | null
  cover_path: string | null
  file_name: string
  file_size: number
  file_type: string
  total_chapters: number | null
  total_words: number | null
  is_read: boolean
  is_deleted: boolean
  created_at: string
  updated_at: string
  chapters?: Chapter[]
}

export interface Chapter {
  id: string
  chapter_number: number
  title: string
  word_count: number
  is_prologue: boolean
  content_hash: string
  needs_review: boolean
  content?: string
}

export interface ReadingProgress {
  chapter_id: string | null
  chapter_number: number | null
  chapter_title: string | null
  percentage: number | null
  content_hash: string | null
  updated_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}
