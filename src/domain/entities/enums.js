export const TaskStatus = {
  OPEN: 'open',
  IN_PROGRESS: 'in_progress',
  DONE: 'done',
  CANCELLED: 'cancelled',
}

export const TaskPriority = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
}

export const PRIORITY_WEIGHT = {
  [TaskPriority.LOW]: 0.25,
  [TaskPriority.MEDIUM]: 0.5,
  [TaskPriority.HIGH]: 0.75,
  [TaskPriority.URGENT]: 1.0,
}

export const PRIORITY_LABEL = {
  [TaskPriority.LOW]: 'Низкий',
  [TaskPriority.MEDIUM]: 'Средний',
  [TaskPriority.HIGH]: 'Высокий',
  [TaskPriority.URGENT]: 'Срочный',
}

export const ListRole = {
  OWNER: 'owner',
  EDITOR: 'editor',
  ASSIGNEE: 'assignee',
  VIEWER: 'viewer',
}

export const RecurrenceType = {
  FIXED_SCHEDULE: 'fixed_schedule',
  COMPLETION_BASED: 'completion_based',
}

export const RecurrenceFreq = {
  DAILY: 'daily',
  WEEKLY: 'weekly',
  MONTHLY: 'monthly',
  CUSTOM: 'custom',
}

export const HistoryEventType = {
  CREATED: 'created',
  FIELD_CHANGED: 'field_changed',
  COMMENTED: 'commented',
  ASSIGNEE_CHANGED: 'assignee_changed',
  RESCHEDULED: 'rescheduled',
  COMPLETED: 'completed',
  REOPENED: 'reopened',
}

export const ChecklistRecurrenceScope = {
  INSTANCE_ONLY: 'instance_only',
  TEMPLATE: 'template',
}

export const CalendarProviderType = {
  NONE: 'none',
  EXCHANGE: 'exchange',
  GOOGLE: 'google',
}

export const CalendarStatus = {
  DISCONNECTED: 'disconnected',
  CONNECTED: 'connected',
  ERROR: 'error',
}

export const ReminderType = {
  TIME: 'time',
  LOCATION: 'location',
}

// --- Настройки отображения (визуализация листов) ---
export const DensityMode = {
  COMPACT: 'compact',
  COMFORTABLE: 'comfortable',
  SPACIOUS: 'spacious',
}

export const GroupByMode = {
  NONE: 'none',
  STATUS: 'status',
  PRIORITY: 'priority',
  ASSIGNEE: 'assignee',
  DUE_DATE: 'due_date',
  LIST: 'list',
  TAG: 'tag',
}

export const SortField = {
  SCORE: 'score',
  DUE_DATE: 'due_date',
  PRIORITY: 'priority',
  CREATED_AT: 'created_at',
  UPDATED_AT: 'updated_at',
  TITLE: 'title',
}

export const ColorCodeMode = {
  NONE: 'none',
  PRIORITY: 'priority',
  LIST: 'list',
  ASSIGNEE: 'assignee',
  OVERDUE: 'overdue',
}

export const GROUP_LABEL = {
  none: 'Без группировки',
  status: 'По статусу',
  priority: 'По приоритету',
  assignee: 'По исполнителю',
  due_date: 'По сроку',
  list: 'По списку',
  tag: 'По тегу',
}

export const SORT_LABEL = {
  score: 'По актуальности (score)',
  due_date: 'По сроку',
  priority: 'По приоритету',
  created_at: 'По дате создания',
  updated_at: 'По дате изменения',
  title: 'По названию',
}

export const DENSITY_LABEL = {
  compact: 'Компактно',
  comfortable: 'Обычно',
  spacious: 'Свободно',
}

export const COLOR_CODE_LABEL = {
  none: 'Без цветовой маркировки',
  priority: 'По приоритету',
  list: 'По списку',
  assignee: 'По исполнителю',
  overdue: 'По просрочке',
}
