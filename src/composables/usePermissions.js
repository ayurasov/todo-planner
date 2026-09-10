import { computed, ref, watch } from 'vue'
import { useUsersStore } from '../stores/usersStore'
import { useListsStore } from '../stores/listsStore'
import { useTasksStore } from '../stores/tasksStore'
import { permissionService } from '../services/PermissionService'

/**
 * Composable-обёртка над PermissionService для использования в компонентах.
 * Инкапсулирует асинхронную природу проверки прав (что важно для плавного
 * перехода на backend v2 — там getRole/canEditTask станут реальными HTTP-
 * запросами, а не синхронными обращениями к localStorage).
 *
 * Использование:
 *   const { canEdit, canAssign, canManageMembers, role } = useListPermissions(listId)
 *   const { canEditThisTask } = useTaskPermissions(task)
 */
export function useListPermissions(listIdRef) {
  const usersStore = useUsersStore()
  const role = ref(null)
  const canCreateTask = ref(false)
  const canAssign = ref(false)
  const canManageMembers = ref(false)
  const canDeleteList = ref(false)
  const loaded = ref(false)

  async function refresh() {
    const listId = typeof listIdRef === 'function' ? listIdRef() : listIdRef.value
    const userId = usersStore.currentUser?.id
    if (!listId || !userId) {
      role.value = null
      loaded.value = true
      return
    }
    role.value = await permissionService.getRole(listId, userId)
    canCreateTask.value = await permissionService.canCreateTask(listId, userId)
    canAssign.value = await permissionService.canAssign(listId, userId)
    canManageMembers.value = await permissionService.canManageMembers(listId, userId)
    canDeleteList.value = await permissionService.canDeleteList(listId, userId)
    loaded.value = true
  }

  watch(
    () => (typeof listIdRef === 'function' ? listIdRef() : listIdRef.value),
    refresh,
    { immediate: true },
  )

  return { role, canCreateTask, canAssign, canManageMembers, canDeleteList, loaded, refresh }
}

export function useTaskPermissions(taskRef) {
  const usersStore = useUsersStore()
  const canEditThisTask = ref(true)
  const canToggleStatus = ref(true)
  const canDeleteThisTask = ref(false)
  const loaded = ref(false)
  const reason = ref('')

  async function refresh() {
    const task = typeof taskRef === 'function' ? taskRef() : taskRef.value
    const userId = usersStore.currentUser?.id
    if (!task || !userId) {
      loaded.value = true
      return
    }
    const allowed = await permissionService.canEditTask(task, userId)
    canEditThisTask.value = allowed
    // Галочка выполнения — отдельное право: его имеет и назначенный редактор
    // встречи (task.meetingId), даже если остальные поля задачи ему недоступны.
    canToggleStatus.value = await permissionService.canToggleTaskStatus(task, userId)
    canDeleteThisTask.value = await permissionService.canDeleteTask(task, userId)
    reason.value = allowed ? '' : 'У вас нет прав редактировать эту задачу (роль в списке не позволяет)'
    loaded.value = true
  }

  watch(
    () => {
      const task = typeof taskRef === 'function' ? taskRef() : taskRef.value
      return task ? `${task.id}:${task.assigneeId}:${task.listId}:${task.createdBy}` : null
    },
    refresh,
    { immediate: true },
  )

  return { canEditThisTask, canToggleStatus, canDeleteThisTask, reason, loaded, refresh }
}

export function useCurrentUserRole() {
  const usersStore = useUsersStore()
  return computed(() => usersStore.currentUser?.globalRole || 'user')
}

/**
 * Права на действия над встречей. Назначенный редактор встречи
 * (meeting.editorIds) может делать все правки встречи, кроме удаления:
 * canEditMeeting включает редактора, canDeleteMeeting — нет.
 * Владельцы/редакторы связанных списков задач сохраняют оба права (как раньше
 * в MeetingDetailView.canManageMeeting), глобальный admin — тоже.
 *
 * Принимает ref/getter встречи. checkMeeting(meeting) — синхронная проверка
 * для отдельных встреч (например, карточек на странице встреч).
 */
export function useMeetingPermissions(meetingRef) {
  const usersStore = useUsersStore()
  const listsStore = useListsStore()
  const tasksStore = useTasksStore()
  const isAdmin = useIsAdmin()

  const resolve = () => (typeof meetingRef === 'function' ? meetingRef() : meetingRef?.value)

  function checkMeeting(meeting) {
    const userId = usersStore.currentUser?.id
    if (!meeting || !userId) return { edit: false, delete: false }
    const isCreator = meeting.createdBy === userId
    const isEditor = (meeting.editorIds || []).includes(userId)
    const relatedListIds = new Set(
      tasksStore.tasks.filter((t) => t.meetingId === meeting.id).map((t) => t.listId).filter(Boolean),
    )
    const isRelatedListManager = [...relatedListIds].some((listId) =>
      ['owner', 'editor'].includes(listsStore.memberships[listId]?.find((m) => m.userId === userId)?.role))
    return {
      edit: isAdmin.value || isCreator || isEditor || isRelatedListManager,
      // Удаление встречи редактору недоступно — «все правки, кроме удаления»
      delete: isAdmin.value || isCreator || isRelatedListManager,
    }
  }

  const canEditMeeting = computed(() => checkMeeting(resolve()).edit)
  const canDeleteMeeting = computed(() => checkMeeting(resolve()).delete)
  const isMeetingEditor = computed(() => (resolve()?.editorIds || []).includes(usersStore.currentUser?.id))

  return { canEditMeeting, canDeleteMeeting, isMeetingEditor, checkMeeting }
}

export function useIsAdmin() {
  const roleRef = useCurrentUserRole()
  return computed(() => roleRef.value === 'admin')
}
