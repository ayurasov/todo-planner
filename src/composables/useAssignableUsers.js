import { computed } from 'vue'
import { useUsersStore } from '../stores/usersStore'
import { useMeetingsStore } from '../stores/meetingsStore'

/**
 * Список пользователей, которых можно назначить исполнителем задачи.
 * Для задач, привязанных к встрече, доступны только участники этой встречи.
 * Это правило применяется и к подзадачам: они используют meetingId родительской
 * задачи и не могут быть назначены пользователю вне состава встречи.
 *
 * @param {() => object|null} taskOrContextRef - функция, возвращающая задачу
 *   либо контекст создания задачи ({ meetingId }).
 */
export function useAssignableUsers(taskOrContextRef) {
  const usersStore = useUsersStore()
  const meetingsStore = useMeetingsStore()

  return computed(() => {
    const source = typeof taskOrContextRef === 'function' ? taskOrContextRef() : taskOrContextRef?.value
    const meetingId = source?.meetingId
    if (!meetingId) return usersStore.users

    const meeting = meetingsStore.meetingById(meetingId)
    if (!meeting) return []

    const attendeeIds = new Set(meeting.attendeeIds || [])
    return usersStore.users.filter((user) => attendeeIds.has(user.id))
  })
}
