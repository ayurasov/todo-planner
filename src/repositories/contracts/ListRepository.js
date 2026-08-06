export class ListRepository {
  async getAll(_userId) { throw new Error('Not implemented') }
  async getById(_id) { throw new Error('Not implemented') }
  async create(_listData) { throw new Error('Not implemented') }
  async update(_id, _patch) { throw new Error('Not implemented') }
  async remove(_id) { throw new Error('Not implemented') }
  async getMembers(_listId) { throw new Error('Not implemented') }
  async addMember(_listId, _userId, _role) { throw new Error('Not implemented') }
  async updateMemberRole(_listId, _userId, _role) { throw new Error('Not implemented') }
  async removeMember(_listId, _userId) { throw new Error('Not implemented') }
}
