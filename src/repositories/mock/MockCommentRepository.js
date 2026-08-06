import { CommentRepository } from '../contracts/CommentRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { nextId } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('comments')

export class MockCommentRepository extends CommentRepository {
  constructor() {
    super()
    this._comments = storage.load([])
  }

  _persist() { storage.save(this._comments) }

  async getByTaskId(taskId) {
    return this._comments.filter((c) => c.taskId === taskId).sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
  }

  async create(commentData) {
    const comment = { id: nextId('comment'), createdAt: new Date().toISOString(), editedAt: null, mentions: [], ...commentData }
    this._comments.push(comment)
    this._persist()
    return comment
  }

  async update(id, patch) {
    const idx = this._comments.findIndex((c) => c.id === id)
    if (idx === -1) throw new Error('Comment not found')
    this._comments[idx] = { ...this._comments[idx], ...patch, editedAt: new Date().toISOString() }
    this._persist()
    return this._comments[idx]
  }

  async remove(id) {
    this._comments = this._comments.filter((c) => c.id !== id)
    this._persist()
    return true
  }
}

export const mockCommentRepository = new MockCommentRepository()
