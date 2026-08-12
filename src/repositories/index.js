/**
 * Единая точка внедрения репозиториев. За выбор реализации ответает
 * VITE_API_MODE ('mock' | 'http'). services/stores/UI не меняются, так как все они
 * обращаются только к этим итоговым экспортам ('mock' по умолчанию, если переменная
 * не задана -- поведение по умолчанию не изменилось).
 *
 * mock-режим не удаляется и остаётся работоспособным без бэкенда -- это важно для
 * локальной разработки UI и для demo/preview без backend.
 */
const API_MODE = import.meta.env.VITE_API_MODE || 'mock'

let repos

if (API_MODE === 'http') {
  const { httpTaskRepository } = await import('./http/HttpTaskRepository')
  const { httpListRepository } = await import('./http/HttpListRepository')
  const { httpUserRepository } = await import('./http/HttpUserRepository')
  const { httpHistoryRepository } = await import('./http/HttpHistoryRepository')
  const { httpRecurrenceRepository } = await import('./http/HttpRecurrenceRepository')
  const { httpSavedViewRepository } = await import('./http/HttpSavedViewRepository')
  const { httpChecklistRepository } = await import('./http/HttpChecklistRepository')
  const { httpNoteRepository } = await import('./http/HttpNoteRepository')
  const { httpCommentRepository } = await import('./http/HttpCommentRepository')
  const { httpNotificationRepository } = await import('./http/HttpNotificationRepository')
  const { httpMeetingRepository } = await import('./http/HttpMeetingRepository')
  const { httpDepartmentRepository } = await import('./http/HttpDepartmentRepository')

  repos = {
    taskRepository: httpTaskRepository,
    listRepository: httpListRepository,
    userRepository: httpUserRepository,
    historyRepository: httpHistoryRepository,
    recurrenceRepository: httpRecurrenceRepository,
    savedViewRepository: httpSavedViewRepository,
    checklistRepository: httpChecklistRepository,
    noteRepository: httpNoteRepository,
    commentRepository: httpCommentRepository,
    notificationRepository: httpNotificationRepository,
    meetingRepository: httpMeetingRepository,
    departmentRepository: httpDepartmentRepository,
  }
} else {
  const { mockTaskRepository } = await import('./mock/MockTaskRepository')
  const { mockListRepository } = await import('./mock/MockListRepository')
  const { mockUserRepository } = await import('./mock/MockUserRepository')
  const { mockHistoryRepository } = await import('./mock/MockHistoryRepository')
  const { mockRecurrenceRepository } = await import('./mock/MockRecurrenceRepository')
  const { mockSavedViewRepository } = await import('./mock/MockSavedViewRepository')
  const { mockChecklistRepository } = await import('./mock/MockChecklistRepository')
  const { mockNoteRepository } = await import('./mock/MockNoteRepository')
  const { mockCommentRepository } = await import('./mock/MockCommentRepository')
  const { mockNotificationRepository } = await import('./mock/MockNotificationRepository')
  const { mockMeetingRepository } = await import('./mock/MockMeetingRepository')
  const { MockDepartmentRepository } = await import('./mock/MockDepartmentRepository')

  repos = {
    taskRepository: mockTaskRepository,
    listRepository: mockListRepository,
    userRepository: mockUserRepository,
    historyRepository: mockHistoryRepository,
    recurrenceRepository: mockRecurrenceRepository,
    savedViewRepository: mockSavedViewRepository,
    checklistRepository: mockChecklistRepository,
    noteRepository: mockNoteRepository,
    commentRepository: mockCommentRepository,
    notificationRepository: mockNotificationRepository,
    meetingRepository: mockMeetingRepository,
    departmentRepository: new MockDepartmentRepository(mockUserRepository),
  }
}

export const taskRepository = repos.taskRepository
export const listRepository = repos.listRepository
export const userRepository = repos.userRepository
export const historyRepository = repos.historyRepository
export const recurrenceRepository = repos.recurrenceRepository
export const savedViewRepository = repos.savedViewRepository
export const checklistRepository = repos.checklistRepository
export const noteRepository = repos.noteRepository
export const commentRepository = repos.commentRepository
export const notificationRepository = repos.notificationRepository
export const meetingRepository = repos.meetingRepository
export const departmentRepository = repos.departmentRepository

export const apiMode = API_MODE
