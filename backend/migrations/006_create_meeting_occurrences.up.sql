-- meeting_occurrences: маппится на createMeetingOccurrence
-- (MeetingOccurrenceService.ensureOccurrences) — материализованные подвстречи
-- регулярной серии. tasks.occurrence_id (см. 008) ссылается на эту таблицу.
CREATE TABLE meeting_occurrences (
  id           TEXT PRIMARY KEY,
  meeting_id   TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  date         TEXT NOT NULL,
  description  TEXT NOT NULL DEFAULT '',
  link         TEXT NOT NULL DEFAULT '',
  generated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX idx_meeting_occurrences_meeting_id ON meeting_occurrences (meeting_id);
