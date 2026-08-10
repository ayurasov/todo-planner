-- task_watchers: нормализованный аналог Task.watcherIds, используется
-- PermissionService.isTaskVisible для роли ASSIGNEE (watcherIds.includes(userId)).
CREATE TABLE task_watchers (
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (task_id, user_id)
);
