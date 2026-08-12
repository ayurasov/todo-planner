export class DepartmentRepository {
  async getAll() { throw new Error('Not implemented') }
  async create(_payload) { throw new Error('Not implemented') }
  async update(_id, _patch) { throw new Error('Not implemented') }
  async remove(_id) { throw new Error('Not implemented') }
  /** Список userId руководителей отдела. */
  async getManagers(_departmentId) { throw new Error('Not implemented') }
  /** Полная замена списка руководителей отдела (массив userId). */
  async setManagers(_departmentId, _userIds) { throw new Error('Not implemented') }
}
