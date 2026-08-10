-- notifications: маппится на createNotification. task_id/list_id/actor_id —
-- ON DELETE SET NULL/CASCADE по смыслу: уведомление живёт своей жизнью для
-- получателя (user_id CASCADE — уведомления пользователя удаляются вместе с ним),
-- но не должно "тащить" за собой удаление задачи/списка/актёра.
CREATE TABLE notifications (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type       TEXT NOT NULL CHECK (type IN (
               'assigned', 'due_soon', 'overdue', 'comment', 'mention',
               'status_changed', 'rescheduled', 'subtask_completed', 'list_invite'
             )),
  task_id    TEXT REFERENCES tasks(id) ON DELETE SET NULL,
  list_id    TEXT REFERENCES lists(id) ON DELETE SET NULL,
  actor_id   TEXT REFERENCES users(id) ON DELETE SET NULL,
  title      TEXT NOT NULL,
  body       TEXT NOT NULL DEFAULT '',
  read       INTEGER NOT NULL DEFAULT 0 CHECK (read IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX idx_notifications_user_id ON notifications (user_id);
