import { defineStore } from 'pinia'
import { meetingRepository } from '../repositories'
import { useUsersStore } from './usersStore'
import { meetingOccurrenceService } from '../services/MeetingOccurrenceService'

export const useMeetingsStore = defineStore('meetings', {
  state: () => ({ meetings: [], loaded: false }),
  getters: {
    meetingById: (state) => (id) => state.meetings.find((m) => m.id === id) || null,
    sortedByDate: (state) => [...state.meetings].filter((m) => !m.archived).sort((a, b) => new Date(b.date) - new Date(a.date)),
    // Сортировка по order используется в подменю сайдбара и на странице встреч
    // как результат пользовательского drag-n-drop, в отличие от sortedByDate.
    activeMeetings: (state) => [...state.meetings].filter((m) => !m.archived).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    archivedMeetings: (state) => [...state.meetings].filter((m) => m.archived).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),

    /**
     * Отсортированные по дате occurrences конкретной регулярной встречи. Подвстречи
     * теперь добавляются только вручную (см. addOccurrence) — здесь просто читаем
     * то, что реально сохранено, никакой автогенерации. Для разовой встречи — пустой
     * массив, так как понятие occurrence к ней неприменимо (см. MeetingDetailView).
     * Сортировка — от последней (самой новой) подвстречи к первой.
     */
    occurrencesOf: (state) => (meetingId) => {
      const meeting = state.meetings.find((m) => m.id === meetingId)
      if (!meeting || !meeting.recurrence) return []
      return [...(meeting.occurrences || [])].sort((a, b) => new Date(b.date) - new Date(a.date))
    },

    /**
     * Найти конкретную подвстречу по её id, не зная meetingId заранее — используется
     * в TaskRow для отображения бейджа "встреча + дата подвстречи" у задач, созданных
     * внутри конкретной подвстречи, а также в TaskDetailPanel для смены подвстречи задачи.
     */
    occurrenceById: (state) => (occurrenceId) => {
      for (const meeting of state.meetings) {
        const occ = (meeting.occurrences || []).find((o) => o.id === occurrenceId)
        if (occ) return { occurrence: occ, meeting }
      }
      return null
    },
  },
  actions: {
    async load() {
      this.meetings = await meetingRepository.getAll()
      this.loaded = true
    },

    async createMeeting(payload) {
      const usersStore = useUsersStore()
      const maxOrder = this.meetings.reduce((max, m) => Math.max(max, m.order ?? 0), -1)
      // Регулярная встреча при создании больше не порождает автоматически ни одной
      // подвстречи — только сама "встреча-серия". Первую и все следующие подвстречи
      // пользователь добавляет вручную кнопкой "Добавить подвстречу серии" (см.
      // MeetingDetailView.addOccurrenceForm/meetingsStore.addOccurrence).
      const meeting = await meetingRepository.create({
        createdBy: usersStore.currentUser?.id, order: maxOrder + 1, occurrences: [], ...payload,
      })
      this.meetings.push(meeting)
      return meeting
    },

    async updateMeeting(id, patch) {
      const updated = await meetingRepository.update(id, patch)
      const idx = this.meetings.findIndex((m) => m.id === id)
      if (idx !== -1) this.meetings[idx] = updated
      return updated
    },

    /**
     * Обновляет базовые поля серии (название, время, состав участников, ссылка,
     * описание, правило повтора). НИКОГДА не трогает существующие occurrences —
     * в отличие от старой автогенерации, правка серии больше не пересобирает
     * список подвстреч, поэтому не может оторвать от них задачи. Подвстречи
     * управляются отдельно через addOccurrence/updateOccurrence/removeOccurrence.
     */
    async updateMeetingSeries(id, patch) {
      // eslint-disable-next-line no-unused-vars
      const { occurrences, ...rest } = patch
      return this.updateMeeting(id, rest)
    },

    /**
     * Добавляет новую подвстречу серии. draft — { date, description, link },
     * date обязательна (предзаполняется в форме через
     * meetingOccurrenceService.computeNextSuggestedDate, но пользователь может
     * её поправить перед сохранением).
     */
    async addOccurrence(meetingId, draft) {
      const meeting = this.meetingById(meetingId)
      if (!meeting || !meeting.recurrence) return null
      const occurrence = meetingOccurrenceService.buildOccurrenceDraft(meeting, draft)
      const occurrences = [...(meeting.occurrences || []), occurrence]
      await this.updateMeeting(meetingId, { occurrences })
      return occurrence
    },

    /**
     * Обновляет описание/ссылку/дату конкретной подвстречи (не всей серии). Используется
     * при заполнении итогов встречи по каждому вхождению регулярной серии отдельно,
     * а также при правке уже добавленной подвстречи.
     */
    async updateOccurrence(meetingId, occurrenceId, patch) {
      const meeting = this.meetingById(meetingId)
      if (!meeting) return null
      const occurrences = (meeting.occurrences || []).map((o) => (o.id === occurrenceId ? { ...o, ...patch } : o))
      return this.updateMeeting(meetingId, { occurrences })
    },

    /**
     * Удаляет подвстречу серии. Задачи, привязанные к ней (task.occurrenceId),
     * не удаляются — только теряют привязку к подвстрече (backend делает это
     * автоматически через ON DELETE SET NULL при пересборке всего occurrences-списка;
     * здесь мы явно отвязываем их на фронте до сохранения, чтобы UI сразу
     * показал задачи как "без подвстречи", а не потребовал перезагрузки).
     */
    async removeOccurrence(meetingId, occurrenceId, { tasksStore } = {}) {
      const meeting = this.meetingById(meetingId)
      if (!meeting) return null
      const occurrences = (meeting.occurrences || []).filter((o) => o.id !== occurrenceId)
      if (tasksStore) {
        const affected = tasksStore.tasks.filter((t) => t.occurrenceId === occurrenceId)
        for (const t of affected) {
          await tasksStore.updateTaskField(t.id, 'occurrenceId', null)
        }
      }
      return this.updateMeeting(meetingId, { occurrences })
    },

    async removeMeeting(id) {
      await meetingRepository.remove(id)
      this.meetings = this.meetings.filter((m) => m.id !== id)
    },

    async archiveMeeting(id) {
      return this.updateMeeting(id, { archived: true })
    },

    async unarchiveMeeting(id) {
      return this.updateMeeting(id, { archived: false })
    },

    async reorderMeetings(orderedIds) {
      await Promise.all(orderedIds.map((id, index) => {
        const meeting = this.meetingById(id)
        if (!meeting || meeting.order === index) return Promise.resolve()
        return this.updateMeeting(id, { order: index })
      }))
    },
  },
})
