-- comments: маппится на createComment. author_id — ON DELETE SET NULL,
-- чтобы удаление автора не уничтожало обсуждение задачи.
CREATE TABLE comments (
  id         TEXT PRIMARY KEY,
  task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  author_id  TEXT REFERENCES users(id) ON DELETE SET NULL,
  text       TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  edited_at  TEXT
);

CREATE INDEX idx_comments_task_id ON comments (task_id);
