import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/my-tasks' },
  { path: '/my-tasks', name: 'my-tasks', component: () => import('../views/MyTasksView.vue') },
  { path: '/team-tasks', name: 'team-tasks', component: () => import('../views/TeamTasksView.vue') },
  { path: '/lists/:id', name: 'list-view', component: () => import('../views/ListView.vue'), props: true },
  { path: '/lists-manager', name: 'lists-manager', component: () => import('../views/ListsManagerView.vue') },
  { path: '/recurring', name: 'recurring', component: () => import('../views/RecurringTasksView.vue') },
  { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue') },
  { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
