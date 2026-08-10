import { defineStore } from 'pinia'
import { listRepository } from '../repositories'
import { useUsersStore } from './usersStore'
import { useNotificationsStore } from './notificationsStore'
import { withPermissionHandling } from './utils/withPermissionHandling'
import { router } from '../router'

export const useListsStore = defineStore('lists', {
  state: () => ({ lists: [], memberships: {}, loaded: false }),
  getters: {
    byId: (state) => (id) => state.lists.find((l) => l.id === id) || null,
    // Списки везде выводятся в порядке order (ручная сортировка drag-n-drop),
    // активные/архивные разделены, чтобы архив не мешался с актуальными списками.
    activeLists: (state) => [...state.lists].filter((l) => !l.archived).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    archivedLists: (state) => [...state.lists].filter((l) => l.archived).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
  },
  actions: {
    /**
     * См. tasksStore._guarded — единая обёртка над withPermissionHandling для
     * мутирующих действий над списками (create/update/remove/memberships), чтобы
     * 403 от backend откатывал optimistic UI и показывал toast, а 401 уводил на /login.
     */
    _guarded(action, opts = {}) {
      return withPermissionHandling(action, {
        notificationsStore: useNotificationsStore(),
        router,
        ...opts,
      })
    },

    async load() {
      const usersStore = useUsersStore()
      await usersStore.load()
      this.lists = await listRepository.getAll(usersStore.currentUser?.id)
      const memberships = {}
      for (const list of this.lists) {
        memberships[list.id] = await listRepository.getMembers(list.id)
      }
      this.memberships = memberships
      this.loaded = true
    },

    async updateList(id, patch) {
      return this._guarded(async () => {
        const updated = await listRepository.update(id, patch)
        const idx = this.lists.findIndex((l) => l.id === id)
        if (idx !== -1) this.lists[idx] = updated
        return updated
      })
    },

    async createList(payload) {
      return this._guarded(async () => {
        const usersStore = useUsersStore()
        // Новый список всегда ставится последним в своей группе (order),
        // иначе он бы всегда получал order: 0 и перескакивал все остальные.
        const maxOrder = this.lists.reduce((max, l) => Math.max(max, l.order ?? 0), -1)
        const list = await listRepository.create({ ...payload, ownerIds: [usersStore.currentUser.id], order: maxOrder + 1 })
        this.lists.push(list)
        this.memberships[list.id] = await listRepository.getMembers(list.id)
        return list
      })
    },

    // Repository.remove(id) уже был реализован в MockListRepository, но никто его
    // не вызывал — в store не было соответствующего action, а в UI отсутствовала
    // кнопка удаления — поэтому списки было невозможно удалить.
    async removeList(id) {
      return this._guarded(async () => {
        await listRepository.remove(id)
        this.lists = this.lists.filter((l) => l.id !== id)
        delete this.memberships[id]
      })
    },

    async archiveList(id) {
      return this.updateList(id, { archived: true })
    },

    async unarchiveList(id) {
      return this.updateList(id, { archived: false })
    },

    // Пересчитывает order всех списков в переданном массиве согласно новому
    // порядку (используется после drag-n-drop) и сохраняет каждый через updateList.
    async reorderLists(orderedIds) {
      await Promise.all(orderedIds.map((id, index) => {
        const list = this.byId(id)
        if (!list || list.order === index) return Promise.resolve()
        return this.updateList(id, { order: index })
      }))
    },

    async addMember(listId, userId, role) {
      return this._guarded(async () => {
        const membership = await listRepository.addMember(listId, userId, role)
        this.memberships[listId] = await listRepository.getMembers(listId)
        return membership
      })
    },

    async updateMemberRole(listId, userId, role) {
      return this._guarded(async () => {
        await listRepository.updateMemberRole(listId, userId, role)
        this.memberships[listId] = await listRepository.getMembers(listId)
      })
    },

    async removeMember(listId, userId) {
      return this._guarded(async () => {
        await listRepository.removeMember(listId, userId)
        this.memberships[listId] = await listRepository.getMembers(listId)
      })
    },
  },
})
