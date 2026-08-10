import { CommentRepository } from '../contracts/CommentRepository'
import { apiClient } from './apiClient'

export class HttpCommentRepository extends CommentRepository {
  async getByTaskId(taskId) {
    return apiClient.get(`/tasks/${taskId}/comments`)
  }

  async create(commentData) {
    const { taskId, ...rest } = commentData
    return apiClient.post(`/tasks/${taskId}/comments`, rest)
  }

  async update(id, patch) {
    return apiClient.patch(`/comments/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/comments/${id}`)
    return true
  }
}

export const httpCommentRepository = new HttpCommentRepository()
