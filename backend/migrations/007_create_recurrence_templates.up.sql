-- recurrence_templates: маппится на createRecurrenceTemplate + RecurrenceService,
-- используется как источник tasks.recurrence_template_id.
CREATE TABLE recurrence_templates (
  id                          TEXT PRIMARY KEY,
  list_id                     TEXT NOT NULL REFERENCES lists(id) ON DELETE CASCADE,
  title_template              TEXT NOT NULL,
  type                        TEXT NOT NULL CHECK (type IN ('fixed_schedule', 'completion_based')),
  rule                        TEXT NOT NULL DEFAULT '{}',
  timezone                    TEXT NOT NULL DEFAULT 'Europe/Moscow',
  generate_ahead_count        INTEGER NOT NULL DEFAULT 1,
  last_generated_instance_date TEXT,
  checklist_template          TEXT NOT NULL DEFAULT '[]'
);
