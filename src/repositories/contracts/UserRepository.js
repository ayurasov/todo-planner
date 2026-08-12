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
  /** Полное удаление пользователя администратором. */
  async deleteUser(_id) { throw new Error('Not implemented') }
  /**
   * Загрузка аватара пользователя (файл через FormData, поле "avatar").
   * Доступно самому пользователю (свой профиль) и администратору (любой
   * пользователь) — см. backend/app/users/routes.py upload_avatar.
   * Возвращает обновлённого пользователя.
   */
  async uploadAvatar(_id, _file) { throw new Error('Not implemented') }
  /** Сброс аватара на стандартный (заглушку с инициалами). */
  async deleteAvatar(_id) { throw new Error('Not implemented') }
  /**
   * Смена пароля текущим авторизованным пользователем.
   * Принимает { currentPassword, newPassword }.
   */
  async changePassword(_payload) { throw new Error('Not implemented') }
}
