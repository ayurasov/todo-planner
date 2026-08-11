export class UserRepository {
  async getAll() { throw new Error('Not implemented') }
  async getById(_id) { throw new Error('Not implemented') }
  async getCurrentUser() { throw new Error('Not implemented') }
  /**
   * Частичное обновление пользователя (globalRole, isActive и т.д.).
   * В v2 станет PATCH /api/users/:id — сигнатура не меняется, поэтому
   * store и UI переживут переход на backend без переписывания.
   */
  async updateUser(_id, _patch) { throw new Error('Not implemented') }
  /** Создание пользователя администратором. Возвращает { ...user, temporaryPassword }. */
  async createUser(_payload) { throw new Error('Not implemented') }
  /** Сброс пароля администратором. Возвращает { ...user, temporaryPassword }. */
  async resetPassword(_id) { throw new Error('Not implemented') }
}
