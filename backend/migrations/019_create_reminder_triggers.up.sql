-- reminder_triggers: маппится на createReminderTrigger (напоминания по задаче,
-- время или геолокация).
CREATE TABLE reminder_triggers (
  id          TEXT PRIMARY KEY,
  task_id     TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  type        TEXT NOT NULL DEFAULT 'time' CHECK (type IN ('time', 'location')),
  time_offset INTEGER,
  geo         TEXT,
  is_enabled  INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1))
);

CREATE INDEX idx_reminder_triggers_task_id ON reminder_triggers (task_id);
