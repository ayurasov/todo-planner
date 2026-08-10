-- comment_mentions: нормализованный аналог Comment.mentions (массив userId).
CREATE TABLE comment_mentions (
  comment_id TEXT NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (comment_id, user_id)
);
