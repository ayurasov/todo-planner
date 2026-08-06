import { defineStore } from 'pinia'
import { taskRepository, checklistRepository, noteRepository, commentRepository } from '../repositories'
import { historyService } from '../services/HistoryService'
import { recurrenceService } from '../services/RecurrenceService'
import { sortTasksByRanking } from '../domain/ranking/rankingScore'
import { useUsersStore } from './usersStore'
import { useListsStore } from './listsStore'
import { usePreferencesStore } from './preferencesStore'

/**
 * Определяет, должна ли задача (в т.ч. подзадача) отображаться как самостоятельная
 * строка в общих представлениях (Мои задачи / Задачи команды / List View — корневой уровень).
 * По умолчанию подзадачи видны только внутри дерева родителя. Исключение — глобальная
 * настройка showSubtasksStandalone, либо индивидуальный флаг task.displayStandalone.
 */
function isVisibleStandalone(task, prefs) {
  if (!task.parentTaskId) return true
  return prefs.showSubtasksStandalone || task.displayStandalone
}

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    tasks: [],
    checklistByTask: {},
    notesByTask: {},
    commentsByTask: {},
    loaded: false,
  }),
  getters: {
    byId: (state) => (id) => state.tasks.find((t) => t.id === id) || null,
    childrenOf: (state) => (parentId) => state.tasks.filter((t) => t.parentTaskId === parentId),
    rootTasksOfList: (state) => (listId) => state.tasks.filter((t) => t.listId === listId && !t.parentTaskId),

    myTasksRanked: (state) => {
      const usersStore = useUsersStore()
      const prefs = usePreferencesStore()
      const currentUserId = usersStore.currentUser?.id
      const mine = state.tasks.filter((t) => t.assigneeId === currentUserId && isVisibleStandalone(t, prefs))
      return sortTasksByRanking(mine, { currentUserId })
    },

    teamTasksRanked: (state) => {
      const usersStore = useUsersStore()
      const prefs = usePreferencesStore()
      const currentUserId = usersStore.currentUser?.id
      const visible = state.tasks.filter((t) => isVisibleStandalone(t, prefs))
      return sortTasksByRanking(visible, { currentUserId })
    },

    tasksByAssignee: (state) => {
      const map = {}
      for (const t of state.tasks) {
        if (!t.assigneeId) continue
        if (!map[t.assigneeId]) map[t.assigneeId] = []
        map[t.assigneeId].push(t)
      }
      return map
    },
  },
  actions: {
    async load() {
      this.tasks = await taskRepository.getAll()
      this.loaded = true
    },

    rankedTasksForList(listId) {
      const usersStore = useUsersStore()
      const prefs = usePreferencesStore()
      const currentUserId = usersStore.currentUser?.id
      const listTasks = this.tasks.filter((t) => t.listId === listId && isVisibleStandalone(t, prefs))
      return sortTasksByRanking(listTasks, { currentUserId })
    },

    async createTask(payload) {
      const usersStore = useUsersStore()
      const task = await taskRepository.create(payload)
      this.tasks.push(task)
      await historyService.recordCreated(task.id, usersStore.currentUser.id)
      if (payload.parentTaskId) {
        await this.touchActivity(payload.parentTaskId)
      }
      return task
    },

    async updateTaskField(id, field, value) {
      const usersStore = useUsersStore()
      const task = this.byId(id)
      const oldValue = task[field]
      const updated = await taskRepository.update(id, { [field]: value })
      const idx = this.tasks.findIndex((t) => t.id === id)
      this.tasks[idx] = updated

      if (field === 'assigneeId') {
        await historyService.recordAssigneeChanged(id, usersStore.currentUser.id, oldValue, value)
      } else if (field === 'dueDate') {
        await historyService.recordRescheduled(id, usersStore.currentUser.id, oldValue, value)
      } else {
        await historyService.recordFieldChanged(id, usersStore.currentUser.id, field, oldValue, value)
      }
      return updated
    },

    async completeTask(id) {
      const usersStore = useUsersStore()
      const updated = await taskRepository.complete(id)
      const idx = this.tasks.findIndex((t) => t.id === id)
      this.tasks[idx] = updated
      await historyService.recordCompleted(id, usersStore.currentUser.id)
      const nextInstance = await recurrenceService.onTaskCompleted(updated)
      if (nextInstance) this.tasks.push(nextInstance)
      return updated
    },

    async reopenTask(id) {
      const usersStore = useUsersStore()
      const updated = await taskRepository.reopen(id)
      const idx = this.tasks.findIndex((t) => t.id === id)
      this.tasks[idx] = updated
      await historyService.recordReopened(id, usersStore.currentUser.id)
      return updated
    },

    async rescheduleTask(id, newDueDate) {
      return this.updateTaskField(id, 'dueDate', newDueDate)
    },

    async assignTask(id, assigneeId) {
      return this.updateTaskField(id, 'assigneeId', assigneeId)
    },

    async togglePin(id) {
      const task = this.byId(id)
      return this.updateTaskField(id, 'pinned', !task.pinned)
    },

    async removeTask(id) {
      await taskRepository.remove(id)
      const removedIds = new Set()
      const collect = (taskId) => {
        removedIds.add(taskId)
        this.tasks.filter((t) => t.parentTaskId === taskId).forEach((c) => collect(c.id))
      }
      collect(id)
      this.tasks = this.tasks.filter((t) => !removedIds.has(t.id))
    },

    /**
     * Обновляет lastActivityAt задачи без создания отдельной записи в истории —
     * используется при событиях "внутри" задачи (чек-лист, комментарии, подзадачи),
     * чтобы ranking score корректно учитывал недавнюю активность ("вываливание вверх").
     */
    async touchActivity(taskId) {
      const task = this.byId(taskId)
      if (!task) return
      const updated = await taskRepository.update(taskId, {})
      const idx = this.tasks.findIndex((t) => t.id === taskId)
      if (idx !== -1) this.tasks[idx] = updated
    },

    async loadChecklist(taskId) {
      this.checklistByTask[taskId] = await checklistRepository.getByTaskId(taskId)
    },

    async addChecklistItem(taskId, title) {
      const item = await checklistRepository.create({ taskId, title, order: (this.checklistByTask[taskId]?.length || 0) })
      if (!this.checklistByTask[taskId]) this.checklistByTask[taskId] = []
      this.checklistByTask[taskId].push(item)
      await this.touchActivity(taskId)
      return item
    },

    async toggleChecklistItem(taskId, itemId) {
      const list = this.checklistByTask[taskId] || []
      const item = list.find((i) => i.id === itemId)
      const updated = await checklistRepository.update(itemId, { done: !item.done })
      const idx = list.findIndex((i) => i.id === itemId)
      list[idx] = updated
      await this.touchActivity(taskId)
      return updated
    },

    async removeChecklistItem(taskId, itemId) {
      await checklistRepository.remove(itemId)
      this.checklistByTask[taskId] = (this.checklistByTask[taskId] || []).filter((i) => i.id !== itemId)
      await this.touchActivity(taskId)
    },

    async loadNotes(taskId) {
      this.notesByTask[taskId] = await noteRepository.getByTaskId(taskId)
    },

    async saveNote(taskId, noteId, contentJSON) {
      const usersStore = useUsersStore()
      let note
      if (noteId) {
        note = await noteRepository.update(noteId, { contentJSON, updatedBy: usersStore.currentUser.id })
        const list = this.notesByTask[taskId] || []
        const idx = list.findIndex((n) => n.id === noteId)
        if (idx !== -1) list[idx] = note
      } else {
        note = await noteRepository.create({ taskId, contentJSON, updatedBy: usersStore.currentUser.id })
        if (!this.notesByTask[taskId]) this.notesByTask[taskId] = []
        this.notesByTask[taskId].push(note)
      }
      return note
    },

    async loadComments(taskId) {
      this.commentsByTask[taskId] = await commentRepository.getByTaskId(taskId)
    },

    async addComment(taskId, text) {
      const usersStore = useUsersStore()
      const listsStore = useListsStore()
      const task = this.byId(taskId)
      const list = task ? listsStore.byId(task.listId) : null
      if (list && list.settings?.allowComments === false) {
        throw new Error('Комментарии отключены владельцем списка')
      }
      const comment = await commentRepository.create({ taskId, authorId: usersStore.currentUser.id, text })
      if (!this.commentsByTask[taskId]) this.commentsByTask[taskId] = []
      this.commentsByTask[taskId].push(comment)
      await historyService.recordComment(taskId, usersStore.currentUser.id, text)
      await this.touchActivity(taskId)
      return comment
    },

    async editComment(taskId, commentId, text) {
      const updated = await commentRepository.update(commentId, { text })
      const list = this.commentsByTask[taskId] || []
      const idx = list.findIndex((c) => c.id === commentId)
      if (idx !== -1) list[idx] = updated
      return updated
    },

    async removeComment(taskId, commentId) {
      await commentRepository.remove(commentId)
      this.commentsByTask[taskId] = (this.commentsByTask[taskId] || []).filter((c) => c.id !== commentId)
    },
  },
})
