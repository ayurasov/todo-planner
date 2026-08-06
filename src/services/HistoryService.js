import { historyRepository } from '../repositories'
import { HistoryEventType } from '../domain/entities/enums'

/**
 * Централизует запись audit trail — все мутации задач должны проходить
 * через этот сервис, чтобы гарантировать полноту истории (раздел "Требования к истории").
 */
export class HistoryService {
  async recordCreated(taskId, actorId) {
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.CREATED })
  }

  async recordFieldChanged(taskId, actorId, field, oldValue, newValue) {
    if (oldValue === newValue) return null
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.FIELD_CHANGED, field, oldValue, newValue })
  }

  async recordAssigneeChanged(taskId, actorId, oldValue, newValue) {
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.ASSIGNEE_CHANGED, oldValue, newValue })
  }

  async recordRescheduled(taskId, actorId, oldValue, newValue) {
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.RESCHEDULED, oldValue, newValue })
  }

  async recordCompleted(taskId, actorId) {
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.COMPLETED })
  }

  async recordReopened(taskId, actorId) {
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.REOPENED })
  }

  async recordComment(taskId, actorId, comment) {
    return historyRepository.append({ taskId, actorId, type: HistoryEventType.COMMENTED, comment })
  }

  async getTaskTimeline(taskId) {
    return historyRepository.getByTaskId(taskId)
  }
}

export const historyService = new HistoryService()
