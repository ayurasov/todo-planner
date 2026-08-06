import { computed, ref, watch } from 'vue'
import { useUsersStore } from '../stores/usersStore'
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
    canToggleStatus.value = allowed
    reason.value = allowed ? '' : 'У вас нет прав редактировать эту задачу (роль в списке не позволяет)'
    loaded.value = true
  }

  watch(
    () => {
      const task = typeof taskRef === 'function' ? taskRef() : taskRef.value
      return task ? `${task.id}:${task.assigneeId}:${task.listId}` : null
    },
    refresh,
    { immediate: true },
  )

  return { canEditThisTask, canToggleStatus, reason, loaded, refresh }
}

export function useCurrentUserRole() {
  const usersStore = useUsersStore()
  return computed(() => usersStore.currentUser?.globalRole || 'user')
}

export function useIsAdmin() {
  const roleRef = useCurrentUserRole()
  return computed(() => roleRef.value === 'admin')
}
