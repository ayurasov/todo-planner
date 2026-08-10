-- tasks: маппится на createTask — центральная сущность. list_id остаётся
-- основным контейнером (ON DELETE CASCADE: удаление списка удаляет его задачи,
-- это ожидаемый UX, а не потеря чужих данных). meeting_id/occurrence_id —
-- nullable и ON DELETE SET NULL: удаление встречи не должно уничтожать
-- задачи, которые уже "отвязались" в отдельные объекты (displayStandalone).
-- author/assignee — ON DELETE SET NULL: удаление пользователя не должно
-- удалять чужие задачи, только обезличивать их (см. п.4 запроса).
CREATE TABLE tasks (
  id                     TEXT PRIMARY KEY,
  list_id                TEXT REFERENCES lists(id) ON DELETE CASCADE,
  parent_task_id         TEXT REFERENCES tasks(id) ON DELETE SET NULL,
  meeting_id             TEXT REFERENCES meetings(id) ON DELETE SET NULL,
  occurrence_id          TEXT REFERENCES meeting_occurrences(id) ON DELETE SET NULL,
  recurrence_template_id TEXT REFERENCES recurrence_templates(id) ON DELETE SET NULL,
  title                  TEXT NOT NULL,
  description            TEXT NOT NULL DEFAULT '',
  status                 TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'done', 'cancelled')),
  priority               TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
  assignee_id            TEXT REFERENCES users(id) ON DELETE SET NULL,
  created_by             TEXT REFERENCES users(id) ON DELETE SET NULL,
  updated_by             TEXT REFERENCES users(id) ON DELETE SET NULL,
  due_date               TEXT,
  start_date             TEXT,
  pinned                 INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1)),
  display_standalone     INTEGER NOT NULL DEFAULT 0 CHECK (display_standalone IN (0, 1)),
  created_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  last_activity_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  completed_at           TEXT
);

CREATE INDEX idx_tasks_list_id      ON tasks (list_id);
CREATE INDEX idx_tasks_assignee_id  ON tasks (assignee_id);
CREATE INDEX idx_tasks_status       ON tasks (status);
CREATE INDEX idx_tasks_due_date     ON tasks (due_date);
CREATE INDEX idx_tasks_created_at   ON tasks (created_at);
CREATE INDEX idx_tasks_completed_at ON tasks (completed_at);
CREATE INDEX idx_tasks_meeting_id   ON tasks (meeting_id);
