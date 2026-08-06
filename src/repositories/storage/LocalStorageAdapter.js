/**
 * Абстракция персистентности для mock-репозиториев (решение по допущению #3:
 * данные должны переживать обновление страницы). Интерфейс TaskRepository и др.
 * не зависит от этого класса — он используется только внутри mock-реализаций.
 */
const NAMESPACE = 'todo-planner:v1:'

export class LocalStorageAdapter {
  constructor(key) {
    this.key = NAMESPACE + key
  }

  load(defaultValue) {
    try {
      const raw = localStorage.getItem(this.key)
      if (!raw) return structuredClone(defaultValue)
      return JSON.parse(raw)
    } catch (e) {
      console.warn(`LocalStorageAdapter: failed to load ${this.key}`, e)
      return structuredClone(defaultValue)
    }
  }

  save(value) {
    try {
      localStorage.setItem(this.key, JSON.stringify(value))
    } catch (e) {
      console.warn(`LocalStorageAdapter: failed to save ${this.key}`, e)
    }
  }

  clear() {
    localStorage.removeItem(this.key)
  }
}
