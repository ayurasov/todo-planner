import { TaskStatus, TaskPriority } from './enums'

let idCounter = 1000
export function nextId(prefix = 'id') {
  idCounter += 1
  return `${prefix}_${idCounter}_${Date.now().toString(36)}`
}

export function createUser({ id, name, email, timezone = 'Europe/Moscow', avatarUrl = null, globalRole = 'user', isActive = true }) {
  return { id: id || nextId('user'), name, email, timezone, avatarUrl, globalRole, isActive }
}

export function createList({
  id, title, description = '', color = '#4f7cff', ownerIds = [], isShared = false,
  defaultView = 'list', createdAt = new Date().toISOString(),
  settings = {},
}) {
  const defaultSettings = {
    allowComments: true,
    allowGuestViewers: false,
    defaultGroupBy: 'none',
    defaultSortField: 'score',
    showCompletedByDefault: false,
    autoArchiveDoneAfterDays: 30,
    requireDueDateOnCreate: false,
    allowedViews: ['list', 'tree', 'grouped'],
    icon: '📋',
    recurringMeeting: {
      enabled: false,
      title: '',
      description: '',
      link: '',
      dayOfWeek: 'monday',
      time: '10:00',
      frequency: 'weekly',
    },
  }
  return {
    id: id || nextId('list'), title, description, color, ownerIds, isShared, defaultView, createdAt,
    settings: { ...defaultSettings, ...settings },
  }
}

export function createListMembership({ id, listId, userId, role, addedAt = new Date().toISOString() }) {
  return { id: id || nextId('membership'), listId, userId, role, addedAt }
}

export function createTask({
  id, listId, parentTaskId = null, title, description = '',
  status = TaskStatus.OPEN, priority = TaskPriority.MEDIUM,
  assigneeId = null, watcherIds = [], dueDate = null, startDate = null,
  recurrenceTemplateId = null, tags = [], pinned = false,
  createdAt = new Date().toISOString(), createdBy = null,
  updatedAt = new Date().toISOString(), updatedBy = null,
  lastActivityAt = new Date().toISOString(), completedAt = null,
  displayStandalone = false,
}) {
  return {
    id: id || nextId('task'), listId, parentTaskId, title, description,
    status, priority, assigneeId, watcherIds, dueDate, startDate,
    recurrenceTemplateId, tags, pinned,
    createdAt, createdBy, updatedAt, updatedBy, lastActivityAt, completedAt,
    displayStandalone,
  }
}

export function createChecklistItem({ id, taskId, title, done = false, order = 0, recurrenceScope = 'instance_only' }) {
  return { id: id || nextId('checklist'), taskId, title, done, order, recurrenceScope }
}

export function createNote({ id, taskId, contentJSON = { type: 'doc', content: [] }, createdAt = new Date().toISOString(), updatedAt = new Date().toISOString(), updatedBy = null }) {
  return { id: id || nextId('note'), taskId, contentJSON, createdAt, updatedAt, updatedBy }
}

export function createAttachment({ id, taskId = null, noteId = null, fileName, mimeType, url, size, uploadedBy, uploadedAt = new Date().toISOString() }) {
  return { id: id || nextId('attach'), taskId, noteId, fileName, mimeType, url, size, uploadedBy, uploadedAt }
}

export function createRecurrenceTemplate({
  id, listId, titleTemplate, type, rule, timezone = 'Europe/Moscow',
  generateAheadCount = 1, lastGeneratedInstanceDate = null, checklistTemplate = [],
}) {
  return { id: id || nextId('rectpl'), listId, titleTemplate, type, rule, timezone, generateAheadCount, lastGeneratedInstanceDate, checklistTemplate }
}

export function createHistoryEntry({ id, taskId, actorId, timestamp = new Date().toISOString(), type, field = null, oldValue = null, newValue = null, comment = null }) {
  return { id: id || nextId('hist'), taskId, actorId, timestamp, type, field, oldValue, newValue, comment }
}

export function createSavedView({ id, userId, name, filters = {}, sort = { field: 'score', dir: 'desc' }, groupBy = null, pinned = false }) {
  return { id: id || nextId('view'), userId, name, filters, sort, groupBy, pinned }
}

export function createCalendarIntegration({ id, userId, provider = 'none', status = 'disconnected', syncSettings = {}, lastSyncedAt = null }) {
  return { id: id || nextId('calint'), userId, provider, status, syncSettings, lastSyncedAt }
}

export function createReminderTrigger({ id, taskId, type = 'time', timeOffset = null, geo = null, isEnabled = true }) {
  return { id: id || nextId('remind'), taskId, type, timeOffset, geo, isEnabled }
}

export function createComment({ id, taskId, authorId, text, createdAt = new Date().toISOString(), editedAt = null, mentions = [] }) {
  return { id: id || nextId('comment'), taskId, authorId, text, createdAt, editedAt, mentions }
}

export function createNotification({
  id, userId, type, taskId = null, listId = null, title, body = '',
  createdAt = new Date().toISOString(), read = false, actorId = null,
}) {
  return { id: id || nextId('notif'), userId, type, taskId, listId, title, body, createdAt, read, actorId }
}
