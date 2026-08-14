CREATE TABLE IF NOT EXISTS meeting_editors (
  meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  user_id    TEXT NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
  PRIMARY KEY (meeting_id, user_id)
);
