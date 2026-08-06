/**
 * Единая точка внедрения репозиториев. При переходе на v2 здесь достаточно
 * заменить mock-импорты на http-реализации — остальной код (services, stores, UI)
 * не меняется, так как все они обращаются только к этим экспортам.
 */
import { mockTaskRepository } from './mock/MockTaskRepository'
import { mockListRepository } from './mock/MockListRepository'
import { mockUserRepository } from './mock/MockUserRepository'
import { mockHistoryRepository } from './mock/MockHistoryRepository'
import { mockRecurrenceRepository } from './mock/MockRecurrenceRepository'
import { mockSavedViewRepository } from './mock/MockSavedViewRepository'
import { mockChecklistRepository } from './mock/MockChecklistRepository'
import { mockNoteRepository } from './mock/MockNoteRepository'
import { mockCommentRepository } from './mock/MockCommentRepository'

export const taskRepository = mockTaskRepository
export const listRepository = mockListRepository
export const userRepository = mockUserRepository
export const historyRepository = mockHistoryRepository
export const recurrenceRepository = mockRecurrenceRepository
export const savedViewRepository = mockSavedViewRepository
export const checklistRepository = mockChecklistRepository
export const noteRepository = mockNoteRepository
export const commentRepository = mockCommentRepository
