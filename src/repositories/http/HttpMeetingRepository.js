import { MeetingRepository } from '../contracts/MeetingRepository'
import { apiClient } from './apiClient'

export class HttpMeetingRepository extends MeetingRepository {
  async getAll() {
    return apiClient.get('/meetings')
  }

  async getById(id) {
    return apiClient.get(`/meetings/${id}`)
  }

  async create(meetingData) {
    return apiClient.post('/meetings', meetingData)
  }

  async update(id, patch) {
    return apiClient.patch(`/meetings/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/meetings/${id}`)
    return true
  }
}

export const httpMeetingRepository = new HttpMeetingRepository()
