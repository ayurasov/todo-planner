-- attachments: маппится на createAttachment (файл может относиться либо
-- к задаче, либо к заметке — ровно один из двух, отсюда CHECK).
CREATE TABLE attachments (
  id          TEXT PRIMARY KEY,
  task_id     TEXT REFERENCES tasks(id) ON DELETE CASCADE,
  note_id     TEXT REFERENCES notes(id) ON DELETE CASCADE,
  file_name   TEXT NOT NULL,
  mime_type   TEXT NOT NULL,
  url         TEXT NOT NULL,
  size        INTEGER NOT NULL DEFAULT 0,
  uploaded_by TEXT REFERENCES users(id) ON DELETE SET NULL,
  uploaded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  CHECK ((task_id IS NOT NULL) OR (note_id IS NOT NULL))
);

CREATE INDEX idx_attachments_task_id ON attachments (task_id);
CREATE INDEX idx_attachments_note_id ON attachments (note_id);
