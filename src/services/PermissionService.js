import { listRepository } from '../repositories'
import { ListRole } from '../domain/entities/enums'

const CAN_EDIT_ANY_TASK = [ListRole.OWNER, ListRole.EDITOR]
const CAN_MANAGE_MEMBERS = [ListRole.OWNER]
const CAN_DELETE_LIST = [ListRole.OWNER]

export class PermissionService {
  async getRole(listId, userId) {
    return listRepository.getUserRole(listId, userId)
  }

  async canViewList(listId, userId) {
    const role = await this.getRole(listId, userId)
    return role !== null
  }

  async canCreateTask(listId, userId) {
    const role = await this.getRole(listId, userId)
    return CAN_EDIT_ANY_TASK.includes(role)
  }

  async canEditTask(task, userId) {
    // Задача без списка (listId = null) — приватный/личный объект без
    // ролевой модели списка: править её может создатель или назначенный
    // исполнитель. Это осознанное упрощение (см. допущение "список
    // необязателен"): полноценные ACL для задач-сирот вне scope MVP.
    if (!task.listId) {
      return task.createdBy === userId || task.assigneeId === userId
    }
    const role = await this.getRole(task.listId, userId)
    if (CAN_EDIT_ANY_TASK.includes(role)) return true
    if (role === ListRole.ASSIGNEE && task.assigneeId === userId) return true
    return false
  }

  async canAssign(listId, userId) {
    const role = await this.getRole(listId, userId)
    return CAN_EDIT_ANY_TASK.includes(role)
  }

  async canManageMembers(listId, userId) {
    const role = await this.getRole(listId, userId)
    return CAN_MANAGE_MEMBERS.includes(role)
  }

  async canDeleteList(listId, userId) {
    const role = await this.getRole(listId, userId)
    return CAN_DELETE_LIST.includes(role)
  }

  async getAccessibleListIds(userId) {
    return listRepository.getAccessibleListIds(userId)
  }

  isTaskVisible(task, { role, userId }) {
    if (!role) return false
    if (role === ListRole.ASSIGNEE) {
      return task.assigneeId === userId || task.watcherIds.includes(userId)
    }
    return true
  }
}

export const permissionService = new PermissionService()
