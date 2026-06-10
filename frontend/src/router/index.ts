import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/home' },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/pages/HomePage.vue'),
      meta: { title: '文章', navId: 'bookshelf' },
    },
    {
      path: '/reader/:id',
      name: 'reader',
      component: () => import('@/pages/ReaderPage.vue'),
      meta: { title: '阅读' },
    },
    {
      path: '/batch-upload',
      name: 'batch-upload',
      component: () => import('@/pages/BatchUploadPage.vue'),
      meta: { title: '批量导入' },
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('@/pages/UploadPage.vue'),
      meta: { title: '上传' },
    },
    {
      path: '/editor',
      name: 'editor',
      component: () => import('@/pages/EditorPage.vue'),
      meta: { title: '编辑' },
    },
    {
      path: '/collections',
      name: 'collections',
      component: () => import('@/pages/CollectionsPage.vue'),
      meta: { title: '合集', navId: 'explore' },
    },
    {
      path: '/collection/:id',
      name: 'collection-detail',
      component: () => import('@/pages/CollectionDetailPage.vue'),
      meta: { title: '合集详情' },
    },
    {
      path: '/groups',
      name: 'groups',
      component: () => import('@/pages/BookGroupPage.vue'),
      meta: { title: '分组' },
    },
    {
      path: '/mine',
      name: 'mine',
      component: () => import('@/pages/MinePage.vue'),
      meta: { title: '我的' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/SettingsPage.vue'),
      meta: { title: '设置' },
    },
    {
      path: '/trash',
      name: 'trash',
      component: () => import('@/pages/TrashPage.vue'),
      meta: { title: '回收站' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { title: '登录', hideSidebar: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/pages/RegisterPage.vue'),
      meta: { title: '注册', hideSidebar: true },
    },
    {
      path: '/novels',
      name: 'novels',
      component: () => import('@/pages/NovelListPage.vue'),
      meta: { title: '小说书架', navId: 'novels' },
    },
    {
      path: '/novels/upload',
      name: 'novel-upload',
      component: () => import('@/pages/NovelUploadPage.vue'),
      meta: { title: '上传小说' },
    },
    {
      path: '/tags',
      name: 'tags-manage',
      component: () => import('@/pages/TagsPage.vue'),
      meta: { title: '标签管理', navId: 'tags' },
    },
    {
      path: '/fonts',
      name: 'fonts',
      component: () => import('@/pages/FontManagePage.vue'),
      meta: { title: '字体管理' },
    },
    {
      path: '/novels/:id',
      name: 'novel-reader',
      component: () => import('@/pages/NovelReaderPage.vue'),
      meta: { title: '阅读' },
    },
  ],
})

const publicPaths = ['/login', '/register']
router.beforeEach((to, _from) => {
  if (publicPaths.includes(to.path)) return true
  if (!localStorage.getItem('token')) return '/login'
  return true
})

export default router
