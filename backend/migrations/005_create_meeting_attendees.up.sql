-- meeting_attendees: нормализованный аналог Meeting.attendeeIds (массив в domain-модели).
CREATE TABLE meeting_attendees (
  meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (meeting_id, user_id)
);
