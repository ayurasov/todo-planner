-- users: маппится на domain/entities/factories.js:createUser + User.globalRole/isActive (PermissionService._isGlobalAdmin)
CREATE TABLE users (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  login         TEXT UNIQUE,
  password_hash TEXT,
  timezone      TEXT NOT NULL DEFAULT 'Europe/Moscow',
  avatar_url    TEXT,
  global_role   TEXT NOT NULL DEFAULT 'user' CHECK (global_role IN ('admin', 'user')),
  is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
