-- task_tags: нормализованный аналог Task.tags (массив строк во frontend).
CREATE TABLE task_tags (
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  tag     TEXT NOT NULL,
  PRIMARY KEY (task_id, tag)
);

CREATE INDEX idx_task_tags_tag ON task_tags (tag);
