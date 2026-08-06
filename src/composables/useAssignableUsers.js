import { computed } from 'vue'
import { useUsersStore } from '../stores/usersStore'
import { useMeetingsStore } from '../stores/meetingsStore'

/**
 * Список пользователей, которых можно назначить исполнителем задачи.
 * Если задача привязана к встрече (meetingId) и у этой встречи заданы
 * участники (attendeeIds) — доступны только они (владелец встречи
 * настраивает состав в разделе редактирования встречи). Если встреча не
 * привязана, либо участники для неё не настроены — доступны все
 * пользователи (обратная совместимость).
 *
 * @param {() => object|null} taskOrContextRef - функция, возвращающая либо
 *   задачу ({ meetingId }), либо контекст создания ({ meetingId }).
 */
export function useAssignableUsers(taskOrContextRef) {
  const usersStore = useUsersStore()
  const meetingsStore = useMeetingsStore()

  return computed(() => {
    const source = typeof taskOrContextRef === 'function' ? taskOrContextRef() : taskOrContextRef?.value
    const meetingId = source?.meetingId
    if (!meetingId) return usersStore.users
    const meeting = meetingsStore.meetingById(meetingId)
    if (!meeting?.attendeeIds?.length) return usersStore.users
    return usersStore.users.filter((u) => meeting.attendeeIds.includes(u.id))
  })
}
