import { MeetingRepository } from '../contracts/MeetingRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedMeetings } from './seedData'
import { nextId } from '../../domain/entities/factories'

const meetingsStorage = new LocalStorageAdapter('meetings')

export class MockMeetingRepository extends MeetingRepository {
  constructor() {
    super()
    this._meetings = meetingsStorage.load(seedMeetings)
  }

  _persist() { meetingsStorage.save(this._meetings) }

  async getAll() {
    return [...this._meetings]
  }

  async getById(id) {
    return this._meetings.find((m) => m.id === id) || null
  }

  async create(meetingData) {
    const meeting = {
      id: nextId('meeting'), description: '', createdBy: null,
      createdAt: new Date().toISOString(), ...meetingData,
    }
    this._meetings.push(meeting)
    this._persist()
    return meeting
  }

  async update(id, patch) {
    const idx = this._meetings.findIndex((m) => m.id === id)
    if (idx === -1) throw new Error(`Meeting ${id} not found`)
    this._meetings[idx] = { ...this._meetings[idx], ...patch }
    this._persist()
    return this._meetings[idx]
  }

  async remove(id) {
    this._meetings = this._meetings.filter((m) => m.id !== id)
    this._persist()
    return true
  }
}

export const mockMeetingRepository = new MockMeetingRepository()
