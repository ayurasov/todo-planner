import { createRouter, createWebHistory } from 'vue-router'
import { useUsersStore } from '../stores/usersStore'
import { useNotificationsStore } from '../stores/notificationsStore'
import { useAuthStore } from '../stores/authStore'
import { apiMode } from '../repositories'

const routes = [
  { path: '/', redirect: '/my-tasks' },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/my-tasks', name: 'my-tasks', component: () => import('../views/MyTasksView.vue') },
  { path: '/team-tasks', name: 'team-tasks', component: () => import('../views/TeamTasksView.vue') },
  { path: '/lists/:id', name: 'list-view', component: () => import('../views/ListView.vue'), props: true },
  { path: '/meetings', name: 'meetings', component: () => import('../views/MeetingsView.vue') },
  { path: '/meetings/:id', name: 'meeting-detail', component: () => import('../views/MeetingDetailView.vue'), props: true },
  { path: '/lists-manager', name: 'lists-manager', component: () => import('../views/ListsManagerView.vue') },
  { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue') },
  { path: '/analytics', name: 'analytics', component: () => import('../views/AnalyticsView.vue') },
  { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
  {
    path: '/settings/users',
    name: 'users',
    component: () => import('../views/UsersView.vue'),
    meta: { requiresAdmin: true },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * В http-режиме любой не-public переход требует authStore.checked/authenticated.
 * main.js вызывает authStore.bootstrap() до app.mount(), но guard добавлен как fallback
 * (прямые перегрузки страниц без повторного main.js).
 * В mock-режиме apiMode !== 'http', поэтому ветка авторизации никогда не срабатывает, поведение
 * не изменилось.
 */
router.beforeEach(async (to) => {
  if (apiMode === 'http' && !to.meta?.public) {
    const authStore = useAuthStore()
    if (!authStore.checked) {
      await authStore.bootstrap()
    }
    if (!authStore.authenticated) {
      return { path: '/login' }
    }
  }

  if (!to.meta?.requiresAdmin) return true

  const usersStore = useUsersStore()
  if (!usersStore.loaded) {
    await usersStore.load()
  }

  const isAdmin = usersStore.currentUser?.globalRole === 'admin'
  if (isAdmin) return true

  const notificationsStore = useNotificationsStore()
  notificationsStore.items.unshift({
    id: `local_${Date.now()}`,
    userId: usersStore.currentUser?.id,
    type: 'status_changed',
    taskId: null,
    listId: null,
    title: 'Доступ только для администраторов',
    body: `Раздел «${to.path}» доступен только пользователям с ролью «Администратор».`,
    createdAt: new Date().toISOString(),
    read: false,
    actorId: null,
  })

  return { path: '/my-tasks' }
})
