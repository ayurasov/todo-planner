/**
 * Промпт 20: тесты той же ролевой матрицы, что покрыта на backend
 * (backend/tests/test_role_matrix.py) -- гарантируют зеркальность правил
 * между frontend PermissionService (UX-слой предварительной блокировки
 * кнопок) и backend permission_service.py (источник истины ACL).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ListRole } from '../../domain/entities/enums'

vi.mock('../../repositories', () => ({
  listRepository: { getUserRole: vi.fn(), getAccessibleListIds: vi.fn() },
  userRepository: { getById: vi.fn() },
}))

import { PermissionService } from '../PermissionService'
import { listRepository, userRepository } from '../../repositories'

const ADMIN_ID = 'admin-1'
const OWNER_ID = 'owner-1'
const EDITOR_ID = 'editor-1'
const VIEWER_ID = 'viewer-1'
const ASSIGNEE_ID = 'assignee-1'
const OUTSIDER_ID = 'outsider-1'
const LIST_ID = 'list-1'

function setupRoles() {
  userRepository.getById.mockImplementation(async (id) => {
    if (id === ADMIN_ID) return { id, globalRole: 'admin' }
    return { id, globalRole: 'user' }
  })
  listRepository.getUserRole.mockImplementation(async (listId, userId) => {
    if (listId !== LIST_ID) return null
    return (
      {
        [OWNER_ID]: ListRole.OWNER,
        [EDITOR_ID]: ListRole.EDITOR,
        [VIEWER_ID]: ListRole.VIEWER,
        [ASSIGNEE_ID]: ListRole.ASSIGNEE,
      }[userId] || null
    )
  })
}

describe('PermissionService role matrix', () => {
  let service

  beforeEach(() => {
    vi.clearAllMocks()
    setupRoles()
    service = new PermissionService()
  })

  describe('canViewList', () => {
    it('allows global admin regardless of membership', async () => {
      expect(await service.canViewList(LIST_ID, ADMIN_ID)).toBe(true)
    })

    it('allows any member (owner/editor/viewer/assignee)', async () => {
      for (const userId of [OWNER_ID, EDITOR_ID, VIEWER_ID, ASSIGNEE_ID]) {
        expect(await service.canViewList(LIST_ID, userId)).toBe(true)
      }
    })

    it('denies an outsider with no membership', async () => {
      expect(await service.canViewList(LIST_ID, OUTSIDER_ID)).toBe(false)
    })
  })

  describe('canCreateTask', () => {
    it('allows owner and editor', async () => {
      expect(await service.canCreateTask(LIST_ID, OWNER_ID)).toBe(true)
      expect(await service.canCreateTask(LIST_ID, EDITOR_ID)).toBe(true)
    })

    it('denies viewer and assignee', async () => {
      expect(await service.canCreateTask(LIST_ID, VIEWER_ID)).toBe(false)
      expect(await service.canCreateTask(LIST_ID, ASSIGNEE_ID)).toBe(false)
    })

    it('denies an outsider', async () => {
      expect(await service.canCreateTask(LIST_ID, OUTSIDER_ID)).toBe(false)
    })
  })

  describe('canEditTask', () => {
    const taskAssignedToEditor = { listId: LIST_ID, createdBy: OWNER_ID, assigneeId: EDITOR_ID }

    it('allows owner and editor to edit any task in the list', async () => {
      expect(await service.canEditTask(taskAssignedToEditor, OWNER_ID)).toBe(true)
      expect(await service.canEditTask(taskAssignedToEditor, EDITOR_ID)).toBe(true)
    })

    it('allows an assignee-role member to edit only their own assigned task', async () => {
      expect(await service.canEditTask(taskAssignedToEditor, ASSIGNEE_ID)).toBe(false)
      const taskAssignedToAssignee = { ...taskAssignedToEditor, assigneeId: ASSIGNEE_ID }
      expect(await service.canEditTask(taskAssignedToAssignee, ASSIGNEE_ID)).toBe(true)
    })

    it('denies a viewer regardless of assignment', async () => {
      expect(await service.canEditTask(taskAssignedToEditor, VIEWER_ID)).toBe(false)
    })

    it('for list-less tasks, allows only the creator or current assignee', async () => {
      const orphanTask = { listId: null, createdBy: OUTSIDER_ID, assigneeId: EDITOR_ID }
      expect(await service.canEditTask(orphanTask, OUTSIDER_ID)).toBe(true)
      expect(await service.canEditTask(orphanTask, EDITOR_ID)).toBe(true)
      expect(await service.canEditTask(orphanTask, VIEWER_ID)).toBe(false)
    })

    it('allows global admin to edit any task, even list-less ones with no matching creator/assignee', async () => {
      const orphanTask = { listId: null, createdBy: OUTSIDER_ID, assigneeId: EDITOR_ID }
      expect(await service.canEditTask(orphanTask, ADMIN_ID)).toBe(true)
    })
  })

  describe('canAssign', () => {
    it('mirrors canCreateTask rules (owner/editor only)', async () => {
      expect(await service.canAssign(LIST_ID, OWNER_ID)).toBe(true)
      expect(await service.canAssign(LIST_ID, EDITOR_ID)).toBe(true)
      expect(await service.canAssign(LIST_ID, VIEWER_ID)).toBe(false)
      expect(await service.canAssign(LIST_ID, ASSIGNEE_ID)).toBe(false)
    })
  })

  describe('canManageMembers', () => {
    it('allows only the owner', async () => {
      expect(await service.canManageMembers(LIST_ID, OWNER_ID)).toBe(true)
      expect(await service.canManageMembers(LIST_ID, EDITOR_ID)).toBe(false)
      expect(await service.canManageMembers(LIST_ID, VIEWER_ID)).toBe(false)
    })

    it('allows global admin', async () => {
      expect(await service.canManageMembers(LIST_ID, ADMIN_ID)).toBe(true)
    })
  })

  describe('canDeleteList', () => {
    it('allows only the owner (and admin)', async () => {
      expect(await service.canDeleteList(LIST_ID, OWNER_ID)).toBe(true)
      expect(await service.canDeleteList(LIST_ID, EDITOR_ID)).toBe(false)
      expect(await service.canDeleteList(LIST_ID, ADMIN_ID)).toBe(true)
    })
  })

  describe('canDeleteTask', () => {
    it('always allows the creator, regardless of current list role', async () => {
      const task = { listId: LIST_ID, createdBy: VIEWER_ID, assigneeId: null }
      expect(await service.canDeleteTask(task, VIEWER_ID)).toBe(true)
    })

    it('allows owner/editor to delete any task in the list', async () => {
      const task = { listId: LIST_ID, createdBy: VIEWER_ID, assigneeId: null }
      expect(await service.canDeleteTask(task, OWNER_ID)).toBe(true)
      expect(await service.canDeleteTask(task, EDITOR_ID)).toBe(true)
    })

    it('denies a non-creator assignee/viewer', async () => {
      const task = { listId: LIST_ID, createdBy: OWNER_ID, assigneeId: ASSIGNEE_ID }
      expect(await service.canDeleteTask(task, ASSIGNEE_ID)).toBe(false)
      expect(await service.canDeleteTask(task, VIEWER_ID)).toBe(false)
    })

    it('denies deletion of list-less tasks for non-creators', async () => {
      const task = { listId: null, createdBy: OWNER_ID, assigneeId: EDITOR_ID }
      expect(await service.canDeleteTask(task, EDITOR_ID)).toBe(false)
    })
  })

  describe('isTaskVisible', () => {
    it('is always visible to a global admin', () => {
      expect(service.isTaskVisible({ assigneeId: null, watcherIds: [] }, { isGlobalAdmin: true })).toBe(true)
    })

    it('is invisible when the caller has no role at all', () => {
      expect(service.isTaskVisible({ assigneeId: null, watcherIds: [] }, { role: null })).toBe(false)
    })

    it('restricts an assignee-role member to tasks assigned to them or watched by them', () => {
      const task = { assigneeId: ASSIGNEE_ID, watcherIds: [] }
      expect(service.isTaskVisible(task, { role: ListRole.ASSIGNEE, userId: ASSIGNEE_ID })).toBe(true)
      expect(service.isTaskVisible(task, { role: ListRole.ASSIGNEE, userId: OUTSIDER_ID })).toBe(false)

      const watchedTask = { assigneeId: OWNER_ID, watcherIds: [ASSIGNEE_ID] }
      expect(service.isTaskVisible(watchedTask, { role: ListRole.ASSIGNEE, userId: ASSIGNEE_ID })).toBe(true)
    })

    it('shows all tasks to owner/editor/viewer roles', () => {
      const task = { assigneeId: OUTSIDER_ID, watcherIds: [] }
      expect(service.isTaskVisible(task, { role: ListRole.OWNER, userId: OWNER_ID })).toBe(true)
      expect(service.isTaskVisible(task, { role: ListRole.VIEWER, userId: VIEWER_ID })).toBe(true)
    })
  })
})
