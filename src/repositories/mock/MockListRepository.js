import { ListRepository } from '../contracts/ListRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedLists, seedMemberships } from './seedData'
import { nextId } from '../../domain/entities/factories'
import { ListRole, GroupByMode, SortField } from '../../domain/entities/enums'

const listsStorage = new LocalStorageAdapter('lists')
const membershipsStorage = new LocalStorageAdapter('memberships')

// Дефолтные settings нового списка. Раньше create() не проставлял это поле
// вовсе (list.settings оставался undefined), а ListSettingsModal.vue сразу
// обращается к form.allowedViews.indexOf(...) и другим полям settings без
// доп. проверок — открытие настроек свежесозданного списка бросало
// TypeError и «вешало» страницу. Теперь любой новый список создаётся уже
// с полным набором настроек, идентичным тому, что ожидает форма.
function defaultListSettings() {
  return {
    icon: 'folder',
    allowComments: true,
    allowGuestViewers: false,
    defaultGroupBy: GroupByMode.NONE,
    defaultSortField: SortField.SCORE,
    showCompletedByDefault: false,
    autoArchiveDoneAfterDays: 0,
    requireDueDateOnCreate: false,
    allowedViews: ['list', 'tree', 'grouped'],
    recurringMeeting: {
      enabled: false,
      title: '',
      description: '',
      link: '',
      dayOfWeek: 'monday',
      time: '10:00',
      frequency: 'weekly',
    },
  }
}

export class MockListRepository extends ListRepository {
  constructor() {
    super()
    this._lists = listsStorage.load(seedLists)
    this._memberships = membershipsStorage.load(seedMemberships)
  }

  _persistLists() { listsStorage.save(this._lists) }
  _persistMemberships() { membershipsStorage.save(this._memberships) }

  async getAll(userId) {
    if (!userId) return [...this._lists]
    const accessibleListIds = this._memberships.filter((m) => m.userId === userId).map((m) => m.listId)
    return this._lists.filter((l) => accessibleListIds.includes(l.id))
  }

  async getAccessibleListIds(userId) {
    return this._memberships.filter((m) => m.userId === userId).map((m) => m.listId)
  }

  async getUserRole(listId, userId) {
    const m = this._memberships.find((x) => x.listId === listId && x.userId === userId)
    return m ? m.role : null
  }

  async getById(id) {
    return this._lists.find((l) => l.id === id) || null
  }

  async create(listData) {
    const { settings: settingsPatch, ...rest } = listData
    const list = {
      id: nextId('list'),
      description: '',
      color: '#4f7cff',
      isShared: false,
      defaultView: 'list',
      createdAt: new Date().toISOString(),
      ownerIds: [],
      ...rest,
      settings: { ...defaultListSettings(), ...(settingsPatch || {}) },
    }
    this._lists.push(list)
    if (listData.ownerIds) {
      for (const ownerId of listData.ownerIds) {
        this._memberships.push({ id: nextId('membership'), listId: list.id, userId: ownerId, role: ListRole.OWNER, addedAt: new Date().toISOString() })
      }
      this._persistMemberships()
    }
    this._persistLists()
    return list
  }

  async update(id, patch) {
    const idx = this._lists.findIndex((l) => l.id === id)
    if (idx === -1) throw new Error(`List ${id} not found`)
    this._lists[idx] = { ...this._lists[idx], ...patch }
    this._persistLists()
    return this._lists[idx]
  }

  async remove(id) {
    this._lists = this._lists.filter((l) => l.id !== id)
    this._memberships = this._memberships.filter((m) => m.listId !== id)
    this._persistLists()
    this._persistMemberships()
    return true
  }

  async getMembers(listId) {
    return this._memberships.filter((m) => m.listId === listId)
  }

  async addMember(listId, userId, role) {
    const existing = this._memberships.find((m) => m.listId === listId && m.userId === userId)
    if (existing) return this.updateMemberRole(listId, userId, role)
    const membership = { id: nextId('membership'), listId, userId, role, addedAt: new Date().toISOString() }
    this._memberships.push(membership)
    this._persistMemberships()
    return membership
  }

  async updateMemberRole(listId, userId, role) {
    const idx = this._memberships.findIndex((m) => m.listId === listId && m.userId === userId)
    if (idx === -1) throw new Error('Membership not found')
    this._memberships[idx] = { ...this._memberships[idx], role }
    this._persistMemberships()
    return this._memberships[idx]
  }

  async removeMember(listId, userId) {
    this._memberships = this._memberships.filter((m) => !(m.listId === listId && m.userId === userId))
    this._persistMemberships()
    return true
  }
}

export const mockListRepository = new MockListRepository()
