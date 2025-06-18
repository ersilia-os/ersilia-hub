ALTER TABLE WorkRequest
  DROP COLUMN RequestPayload,
  ADD COLUMN PodReadyTimestamp timestamp,
  ADD COLUMN JobSubmissionTimestamp timestamp,
  ADD COLUMN ProcessedTimestamp timestamp;

