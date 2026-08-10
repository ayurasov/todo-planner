-- task_history_entries: маппится на createHistoryEntry (HistoryService).
-- actor_id — ON DELETE SET NULL, история не должна пропадать при удалении автора.
CREATE TABLE task_history_entries (
  id        TEXT PRIMARY KEY,
  task_id   TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  actor_id  TEXT REFERENCES users(id) ON DELETE SET NULL,
  timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  type      TEXT NOT NULL CHECK (type IN (
              'created', 'field_changed', 'commented', 'assignee_changed',
              'rescheduled', 'completed', 'reopened'
            )),
  field     TEXT,
  old_value TEXT,
  new_value TEXT,
  comment   TEXT
);

CREATE INDEX idx_task_history_task_id_timestamp ON task_history_entries (task_id, timestamp);
