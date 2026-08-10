-- checklist_items: маппится на createChecklistItem.
CREATE TABLE checklist_items (
  id               TEXT PRIMARY KEY,
  task_id          TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  title            TEXT NOT NULL,
  done             INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
  order_index      INTEGER NOT NULL DEFAULT 0,
  recurrence_scope TEXT NOT NULL DEFAULT 'instance_only' CHECK (recurrence_scope IN ('instance_only', 'template'))
);

CREATE INDEX idx_checklist_items_task_id ON checklist_items (task_id);
