import { defineStore } from 'pinia'
import { departmentRepository } from '../repositories'
import { useNotificationsStore } from './notificationsStore'
import { withPermissionHandling } from './utils/withPermissionHandling'
import { router } from '../router'

/**
 * departmentsStore -- плоский справочник отделов/служб (без иерархии).
 * CRUD -- только для global admin (зеркало backend-guardа в
 * departments/routes.py). Связь "руководитель <-> отделы" -- many-to-many
 * (один руководитель может вести несколько отделов одновременно).
 */
export const useDepartmentsStore = defineStore('departments', {
  state: () => ({ departments: [], loaded: false }),
  getters: {
    byId: (state) => (id) => state.departments.find((d) => d.id === id) || null,
    sortedDepartments: (state) => [...state.departments].sort((a, b) => a.name.localeCompare(b.name, 'ru')),
  },
  actions: {
    async load() {
      if (this.loaded) return
      this.departments = await departmentRepository.getAll()
      this.loaded = true
    },

    async refresh() {
      this.departments = await departmentRepository.getAll()
    },

    async createDepartment(payload) {
      return withPermissionHandling(async () => {
        const created = await departmentRepository.create(payload)
        this.departments.push(created)
        return created
      }, { notificationsStore: useNotificationsStore(), router })
    },

    async updateDepartment(id, patch) {
      return withPermissionHandling(async () => {
        const updated = await departmentRepository.update(id, patch)
        const idx = this.departments.findIndex((d) => d.id === id)
        if (idx !== -1) this.departments[idx] = updated
        return updated
      }, { notificationsStore: useNotificationsStore(), router })
    },

    async deleteDepartment(id) {
      return withPermissionHandling(async () => {
        await departmentRepository.remove(id)
        this.departments = this.departments.filter((d) => d.id !== id)
      }, { notificationsStore: useNotificationsStore(), router })
    },

    async getManagers(departmentId) {
      return departmentRepository.getManagers(departmentId)
    },

    /** Задать полный список руководителей отдела (массив userId). */
    async setManagers(departmentId, userIds) {
      return withPermissionHandling(async () => {
        return departmentRepository.setManagers(departmentId, userIds)
      }, { notificationsStore: useNotificationsStore(), router })
    },
  },
})
