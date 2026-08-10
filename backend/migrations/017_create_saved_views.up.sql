-- saved_views: маппится на createSavedView (пользовательские фильтры/сортировки экранов).
CREATE TABLE saved_views (
  id       TEXT PRIMARY KEY,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name     TEXT NOT NULL,
  filters  TEXT NOT NULL DEFAULT '{}',
  sort     TEXT NOT NULL DEFAULT '{"field":"score","dir":"desc"}',
  group_by TEXT,
  pinned   INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1))
);

CREATE INDEX idx_saved_views_user_id ON saved_views (user_id);
