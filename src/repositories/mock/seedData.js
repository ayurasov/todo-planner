import { createUser, createList, createListMembership, createTask, createChecklistItem, createNote, createHistoryEntry, createRecurrenceTemplate, createMeeting } from '../../domain/entities/factories'
import { TaskStatus, TaskPriority, ListRole, HistoryEventType, RecurrenceType, RecurrenceFreq } from '../../domain/entities/enums'

const now = new Date()
const iso = (offsetDays = 0, hours = 0) => {
  const d = new Date(now)
  d.setDate(d.getDate() + offsetDays)
  d.setHours(d.getHours() + hours)
  return d.toISOString()
}

export const CURRENT_USER_ID = 'user_1'

export const seedUsers = [
  createUser({ id: 'user_1', name: 'Александр Юрасов', email: 'a.yurasov@example.com', globalRole: 'admin' }),
  createUser({ id: 'user_2', name: 'Мария Соколова', email: 'm.sokolova@example.com', globalRole: 'user' }),
  createUser({ id: 'user_3', name: 'Дмитрий Ким', email: 'd.kim@example.com', globalRole: 'user' }),
  createUser({ id: 'user_4', name: 'Елена Волкова', email: 'e.volkova@example.com', globalRole: 'user' }),
]

export const seedLists = [
  createList({ id: 'list_1', title: 'ERP-проект: интеграция', description: 'Внедрение Odoo, интеграции', ownerIds: ['user_1'], isShared: true, order: 0 }),
  createList({ id: 'list_2', title: 'Личные задачи', description: 'Личный список', ownerIds: ['user_1'], isShared: false, order: 1 }),
  createList({ id: 'list_3', title: 'Команда — операционка', description: 'Текущие задачи команды', ownerIds: ['user_1', 'user_2'], isShared: true, order: 2 }),
]

export const seedMemberships = [
  createListMembership({ listId: 'list_1', userId: 'user_1', role: ListRole.OWNER }),
  createListMembership({ listId: 'list_1', userId: 'user_2', role: ListRole.EDITOR }),
  createListMembership({ listId: 'list_1', userId: 'user_3', role: ListRole.ASSIGNEE }),
  createListMembership({ listId: 'list_2', userId: 'user_1', role: ListRole.OWNER }),
  createListMembership({ listId: 'list_3', userId: 'user_1', role: ListRole.OWNER }),
  createListMembership({ listId: 'list_3', userId: 'user_2', role: ListRole.OWNER }),
  createListMembership({ listId: 'list_3', userId: 'user_3', role: ListRole.EDITOR }),
  createListMembership({ listId: 'list_3', userId: 'user_4', role: ListRole.VIEWER }),
]

const t1 = createTask({
  id: 'task_1', listId: 'list_1', title: 'Согласовать техническое задание по интеграции AlterOffice',
  description: 'Проверить спецификацию, отправить на согласование заказчику.',
  priority: TaskPriority.HIGH, assigneeId: 'user_1', dueDate: iso(-1),
  createdAt: iso(-5), updatedAt: iso(0, -2), lastActivityAt: iso(0, -2), pinned: true,
  tags: ['integration', 'urgent-review'], meetingId: 'meeting_1',
})
const t2 = createTask({
  id: 'task_2', listId: 'list_1', parentTaskId: 'task_1', title: 'Собрать замечания от отдела безопасности',
  priority: TaskPriority.MEDIUM, assigneeId: 'user_3', dueDate: iso(0),
  createdAt: iso(-3), updatedAt: iso(-1), lastActivityAt: iso(-1),
})
const t3 = createTask({
  id: 'task_3', listId: 'list_1', parentTaskId: 'task_1', title: 'Обновить раздел рисков в ТЗ',
  priority: TaskPriority.LOW, assigneeId: 'user_1', dueDate: iso(2),
  createdAt: iso(-2), updatedAt: iso(-2), lastActivityAt: iso(-2),
})
const t4 = createTask({
  id: 'task_4', listId: 'list_1', title: 'Провести аудит текущей архитектуры Odoo',
  priority: TaskPriority.URGENT, assigneeId: 'user_2', dueDate: iso(1),
  createdAt: iso(-10), updatedAt: iso(0, -0.5), lastActivityAt: iso(0, -0.5),
})
const t5 = createTask({
  id: 'task_5', listId: 'list_2', title: 'Проверить показатели pH в пруду',
  priority: TaskPriority.MEDIUM, assigneeId: 'user_1', dueDate: iso(0),
  createdAt: iso(-1), updatedAt: iso(-1), lastActivityAt: iso(-1),
})
const t6 = createTask({
  id: 'task_6', listId: 'list_3', title: 'Еженедельный ревью статусов проекта',
  priority: TaskPriority.MEDIUM, assigneeId: 'user_2', dueDate: iso(3),
  createdAt: iso(-1), updatedAt: iso(-1), lastActivityAt: iso(-1),
  recurrenceTemplateId: 'rectpl_1',
})
const t7 = createTask({
  id: 'task_7', listId: 'list_3', title: 'Обновить дорожную карту релиза',
  priority: TaskPriority.HIGH, assigneeId: 'user_1', status: TaskStatus.DONE, dueDate: iso(-2),
  createdAt: iso(-6), updatedAt: iso(-1), lastActivityAt: iso(-1), completedAt: iso(-1),
})

export const seedTasks = [t1, t2, t3, t4, t5, t6, t7]

export const seedChecklistItems = [
  createChecklistItem({ taskId: 'task_1', title: 'Проверить версию документа', done: true, order: 0 }),
  createChecklistItem({ taskId: 'task_1', title: 'Собрать подписи согласующих', done: false, order: 1 }),
  createChecklistItem({ taskId: 'task_4', title: 'Список модулей Odoo', done: false, order: 0 }),
]

export const seedNotes = [
  createNote({ taskId: 'task_1', contentJSON: { type: 'doc', content: [{ type: 'paragraph', text: 'Черновик согласован с юр. отделом.' }] } }),
]

export const seedHistory = [
  createHistoryEntry({ taskId: 'task_1', actorId: 'user_1', type: HistoryEventType.CREATED, timestamp: iso(-5) }),
  createHistoryEntry({ taskId: 'task_1', actorId: 'user_1', type: HistoryEventType.FIELD_CHANGED, field: 'priority', oldValue: 'medium', newValue: 'high', timestamp: iso(-3) }),
  createHistoryEntry({ taskId: 'task_1', actorId: 'user_2', type: HistoryEventType.COMMENTED, comment: 'Нужно уточнить сроки с юр. отделом.', timestamp: iso(-1) }),
  createHistoryEntry({ taskId: 'task_7', actorId: 'user_1', type: HistoryEventType.COMPLETED, timestamp: iso(-1) }),
  createHistoryEntry({ taskId: 'task_4', actorId: 'user_2', type: HistoryEventType.ASSIGNEE_CHANGED, oldValue: 'user_1', newValue: 'user_2', timestamp: iso(-4) }),
]

export const seedRecurrenceTemplates = [
  createRecurrenceTemplate({
    id: 'rectpl_1', listId: 'list_3', titleTemplate: 'Еженедельный ревью статусов проекта',
    type: RecurrenceType.FIXED_SCHEDULE,
    rule: { freq: RecurrenceFreq.WEEKLY, interval: 1, byWeekday: ['MO'], endCondition: null },
    generateAheadCount: 2,
  }),
]

export const seedMeetings = [
  createMeeting({ id: 'meeting_1', title: 'Планёрка по ERP-проекту', date: iso(-2, 10), description: 'Синхронизация статусов интеграции Odoo, обсуждение блокеров.', createdBy: 'user_1', order: 0 }),
  createMeeting({ id: 'meeting_2', title: 'Еженедельный ревью команды', date: iso(1, 11), description: 'Обзор текущих задач и приоритетов на неделю.', createdBy: 'user_1', order: 1 }),
]
