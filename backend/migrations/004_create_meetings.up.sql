-- meetings: маппится на createMeeting (продуктовая ветка с регулярными
-- встречами списка). recurrence хранится как JSON правило, т.к. на фронте
-- это произвольная структура (frequency/dayOfWeek/...), а не набор колонок.
CREATE TABLE meetings (
  id          TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  date        TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  link        TEXT NOT NULL DEFAULT '',
  color       TEXT NOT NULL DEFAULT '#4f7cff',
  archived    INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
  order_index INTEGER NOT NULL DEFAULT 0,
  recurrence  TEXT,
  created_by  TEXT REFERENCES users(id) ON DELETE SET NULL,
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
