import { defineStore } from 'pinia'
import { listRepository } from '../repositories'
import { useUsersStore } from './usersStore'

export const useListsStore = defineStore('lists', {
  state: () => ({ lists: [], memberships: {}, loaded: false }),
  getters: {
    byId: (state) => (id) => state.lists.find((l) => l.id === id) || null,
  },
  actions: {
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
      const updated = await listRepository.update(id, patch)
      const idx = this.lists.findIndex((l) => l.id === id)
      if (idx !== -1) this.lists[idx] = updated
      return updated
    },

    async createList(payload) {
      const usersStore = useUsersStore()
      const list = await listRepository.create({ ...payload, ownerIds: [usersStore.currentUser.id] })
      this.lists.push(list)
      this.memberships[list.id] = await listRepository.getMembers(list.id)
      return list
    },

    async addMember(listId, userId, role) {
      const membership = await listRepository.addMember(listId, userId, role)
      this.memberships[listId] = await listRepository.getMembers(listId)
      return membership
    },

    async updateMemberRole(listId, userId, role) {
      await listRepository.updateMemberRole(listId, userId, role)
      this.memberships[listId] = await listRepository.getMembers(listId)
    },

    async removeMember(listId, userId) {
      await listRepository.removeMember(listId, userId)
      this.memberships[listId] = await listRepository.getMembers(listId)
    },
  },
})
