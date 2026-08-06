import { listRepository, userRepository } from '../repositories'
import { ListRole } from '../domain/entities/enums'

const CAN_EDIT_ANY_TASK = [ListRole.OWNER, ListRole.EDITOR]
const CAN_MANAGE_MEMBERS = [ListRole.OWNER]
const CAN_DELETE_LIST = [ListRole.OWNER]

export class PermissionService {
  /**
   * Глобальный admin (usersStore.currentUser.globalRole === 'admin') должен
   * иметь полный доступ ко всем задачам и спискам независимо от своей роли
   * в конкретном списке, от авторства задачи и от того, назначен ли он
   * исполнителем прямо сейчас. Раньше это правило не было реализовано:
   * canEditTask/canDeleteTask/canAssign/canManageMembers/canDeleteList
   * проверяли только ListRole и createdBy/assigneeId, поэтому админ, снявший
   * с себя назначение (assigneeId = null) на задаче без списка или с ролью
   * ниже Editor, полностью терял возможность что-либо делать с задачей —
   * это и есть баг из фидбека. Теперь любая проверка прав начинается с
   * admin-bypass.
   */
  async _isGlobalAdmin(userId) {
    if (!userId) return false
    const user = await userRepository.getById(userId)
    return user?.globalRole === 'admin'
  }

  async getRole(listId, userId) {
    return listRepository.getUserRole(listId, userId)
  }

  async canViewList(listId, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    const role = await this.getRole(listId, userId)
    return role !== null
  }

  async canCreateTask(listId, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    const role = await this.getRole(listId, userId)
    return CAN_EDIT_ANY_TASK.includes(role)
  }

  async canEditTask(task, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    // Задача без списка (listId = null) — приватный/личный объект без
    // ролевой модели списка: править её может создатель или назначенный
    // исполнитель. Это осознанное упрощение: полноценные ACL для задач-сирот вне scope MVP.
    if (!task.listId) {
      return task.createdBy === userId || task.assigneeId === userId
    }
    const role = await this.getRole(task.listId, userId)
    if (CAN_EDIT_ANY_TASK.includes(role)) return true
    if (role === ListRole.ASSIGNEE && task.assigneeId === userId) return true
    return false
  }

  async canAssign(listId, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    const role = await this.getRole(listId, userId)
    return CAN_EDIT_ANY_TASK.includes(role)
  }

  async canManageMembers(listId, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    const role = await this.getRole(listId, userId)
    return CAN_MANAGE_MEMBERS.includes(role)
  }

  async canDeleteList(listId, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    const role = await this.getRole(listId, userId)
    return CAN_DELETE_LIST.includes(role)
  }

  /**
   * Создатель задачи может удалить её всегда, независимо от текущей роли
   * в списке; Owner/Editor списка также могут удалять любую задачу списка.
   * Глобальный admin может удалить любую задачу.
   */
  async canDeleteTask(task, userId) {
    if (await this._isGlobalAdmin(userId)) return true
    if (task.createdBy === userId) return true
    if (!task.listId) return false
    const role = await this.getRole(task.listId, userId)
    return CAN_EDIT_ANY_TASK.includes(role)
  }

  async getAccessibleListIds(userId) {
    return listRepository.getAccessibleListIds(userId)
  }

  isTaskVisible(task, { role, userId, isGlobalAdmin }) {
    if (isGlobalAdmin) return true
    if (!role) return false
    if (role === ListRole.ASSIGNEE) {
      return task.assigneeId === userId || task.watcherIds.includes(userId)
    }
    return true
  }
}

export const permissionService = new PermissionService()
