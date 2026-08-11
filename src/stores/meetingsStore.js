import { defineStore } from 'pinia'
import { meetingRepository } from '../repositories'
import { useUsersStore } from './usersStore'
import { useTasksStore } from './tasksStore'
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
     * Отсортированные по дате occurrences конкретной регулярной встречи (включая
     * первую, дата которой равна meeting.date). Для разовой встречи — пустой массив,
     * так как понятие occurrence к ней неприменимо (см. MeetingDetailView).
     * Сортировка — от последней (самой новой) подвстречи к первой: пользователю
     * важнее видеть свежие итоги встреч сверху, а не пролистывать всю историю серии.
     */
    occurrencesOf: (state) => (meetingId) => {
      const meeting = state.meetings.find((m) => m.id === meetingId)
      if (!meeting || !meeting.recurrence) return []
      return [...(meeting.occurrences || [])].sort((a, b) => new Date(b.date) - new Date(a.date))
    },

    /**
     * Найти конкретную подвстречу по её id, не зная meetingId заранее — используется
     * в TaskRow для отображения бейджа "встреча + дата подвстречи" у задач, созданных
     * внутри конкретной подвстречи.
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
      // Догенерируем подвстречи для всех регулярных встреч сразу после загрузки —
      // это гарантирует, что пользователь никогда не увидит пустой список подвстреч у
      // регулярной встречи и что "завтрашняя" подвстреча появится без ручных действий.
      await Promise.all(this.meetings.filter((m) => m.recurrence).map((m) => this.ensureOccurrences(m.id)))
    },

    /**
     * Пересчитывает и, если появились новые подвстречи или у существующих была
     * исправлена заглушшая полночь 00:00, сохраняет их. Безопасно вызывать многократно
     * (идемпотентно) — вызов на уже корректных данных ничего не изменит.
     */
    async ensureOccurrences(meetingId) {
      const meeting = this.meetingById(meetingId)
      if (!meeting || !meeting.recurrence) return meeting
      const rebuilt = meetingOccurrenceService.buildOccurrences(meeting)
      const before = meeting.occurrences || []
      const changed = rebuilt.length !== before.length
        || rebuilt.some((occ, i) => occ.date !== before[i]?.date)
      if (!changed) return meeting
      return this.updateMeeting(meetingId, { occurrences: rebuilt })
    },

    async createMeeting(payload) {
      const usersStore = useUsersStore()
      const maxOrder = this.meetings.reduce((max, m) => Math.max(max, m.order ?? 0), -1)
      const meeting = await meetingRepository.create({ createdBy: usersStore.currentUser?.id, order: maxOrder + 1, ...payload })
      this.meetings.push(meeting)
      if (meeting.recurrence) await this.ensureOccurrences(meeting.id)
      return meeting
    },

    async updateMeeting(id, patch) {
      const updated = await meetingRepository.update(id, patch)
      const idx = this.meetings.findIndex((m) => m.id === id)
      if (idx !== -1) this.meetings[idx] = updated
      return updated
    },

    /**
     * Безопасное обновление регулярной серии встречи: используется вместо
     * прямого updateMeeting(id, { ...patch, occurrences: [] }) при правке
     * состава/времени/регулярности. Прошлые подвстречи и будущие подвстречи
     * с уже существующими задачами сохраняют свои id (и, соответственно,
     * привязку задач через occurrence_id) — пересобираются только "свободные"
     * будущие слоты по новому правилу повторения. См. MeetingOccurrenceService
     * .buildMergedOccurrences и баг "исчезают задачи подвстречи при правке серии".
     */
    async updateMeetingSeries(id, patch) {
      const meeting = this.meetingById(id)
      if (!meeting) return null
      const tasksStore = useTasksStore()
      const hasTasks = (occurrenceId) => tasksStore.tasks.some((t) => t.occurrenceId === occurrenceId)
      const nextRecurrence = 'recurrence' in patch ? patch.recurrence : meeting.recurrence
      const nextDate = 'date' in patch ? patch.date : meeting.date

      let occurrences
      if (!nextRecurrence) {
        occurrences = []
      } else {
        occurrences = meetingOccurrenceService.buildMergedOccurrences(meeting, {
          date: nextDate,
          recurrence: nextRecurrence,
          hasTasks,
        })
      }

      return this.updateMeeting(id, { ...patch, occurrences })
    },

    /**
     * Обновляет описание/ссылку конкретной подвстречи (не всей серии). Используется
     * при заполнении итогов встречи по каждому вхождению регулярной серии отдельно.
     */
    async updateOccurrence(meetingId, occurrenceId, patch) {
      const meeting = this.meetingById(meetingId)
      if (!meeting) return null
      const occurrences = (meeting.occurrences || []).map((o) => (o.id === occurrenceId ? { ...o, ...patch } : o))
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
