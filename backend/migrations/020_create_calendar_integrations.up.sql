-- calendar_integrations: маппится на createCalendarIntegration
-- (src/integrations/calendar CalendarProvider abstraction).
CREATE TABLE calendar_integrations (
  id             TEXT PRIMARY KEY,
  user_id        TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  provider       TEXT NOT NULL DEFAULT 'none' CHECK (provider IN ('none', 'exchange', 'google')),
  status         TEXT NOT NULL DEFAULT 'disconnected' CHECK (status IN ('disconnected', 'connected', 'error')),
  sync_settings  TEXT NOT NULL DEFAULT '{}',
  last_synced_at TEXT
);
