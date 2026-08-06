import { defineStore } from 'pinia'
import { recurrenceRepository } from '../repositories'

export const useRecurrenceStore = defineStore('recurrence', {
  state: () => ({ templates: [], loaded: false }),
  actions: {
    async load() {
      this.templates = await recurrenceRepository.getAll()
      this.loaded = true
    },
    async createTemplate(payload) {
      const template = await recurrenceRepository.create(payload)
      this.templates.push(template)
      return template
    },
    async updateTemplate(id, patch) {
      const updated = await recurrenceRepository.update(id, patch)
      const idx = this.templates.findIndex((t) => t.id === id)
      this.templates[idx] = updated
      return updated
    },
    async removeTemplate(id) {
      await recurrenceRepository.remove(id)
      this.templates = this.templates.filter((t) => t.id !== id)
    },
  },
})
