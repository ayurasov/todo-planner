/**
 * Контракт репозитория задач. Mock- и HTTP-реализации должны
 * реализовывать этот же набор методов, чтобы UI не менялся при переходе на v2.
 */
export class TaskRepository {
  async getAll(_filters = {}) { throw new Error('Not implemented') }
  async getById(_id) { throw new Error('Not implemented') }
  async getChildren(_parentTaskId) { throw new Error('Not implemented') }
  async create(_taskData) { throw new Error('Not implemented') }
  async update(_id, _patch, _actorId) { throw new Error('Not implemented') }
  async remove(_id, _actorId) { throw new Error('Not implemented') }
  async complete(_id, _actorId) { throw new Error('Not implemented') }
  async reschedule(_id, _newDueDate, _actorId) { throw new Error('Not implemented') }
  async assign(_id, _assigneeId, _actorId) { throw new Error('Not implemented') }
}
