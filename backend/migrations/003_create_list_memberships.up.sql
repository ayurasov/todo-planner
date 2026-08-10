-- list_memberships: маппится на createListMembership + ListRole enum,
-- источник правды для PermissionService.getRole()/canEditTask/canManageMembers.
CREATE TABLE list_memberships (
  id       TEXT PRIMARY KEY,
  list_id  TEXT NOT NULL REFERENCES lists(id) ON DELETE CASCADE,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role     TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'assignee', 'viewer')),
  added_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  UNIQUE (list_id, user_id)
);

CREATE INDEX idx_list_memberships_list_user ON list_memberships (list_id, user_id);
