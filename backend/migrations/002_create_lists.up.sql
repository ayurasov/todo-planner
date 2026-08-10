-- lists: маппится на domain/entities/factories.js:createList. ownerIds фронтенда
-- материализуется через list_memberships.role = 'owner' (см. 003), поэтому
-- отдельного массива owner_ids в схеме нет — единый источник правды о ролях.
CREATE TABLE lists (
  id           TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT NOT NULL DEFAULT '',
  color        TEXT NOT NULL DEFAULT '#4f7cff',
  is_shared    INTEGER NOT NULL DEFAULT 0 CHECK (is_shared IN (0, 1)),
  default_view TEXT NOT NULL DEFAULT 'list',
  settings     TEXT NOT NULL DEFAULT '{}',
  archived     INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
  order_index  INTEGER NOT NULL DEFAULT 0,
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
