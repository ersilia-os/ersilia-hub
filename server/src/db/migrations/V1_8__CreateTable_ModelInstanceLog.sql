CREATE TABLE IF NOT EXISTS ModelInstanceLog (
    ModelId text NOT NULL,
    InstanceId text NOT NULL, -- pod name
    CorrelationId text NOT NULL, -- e.g. workrequest id, possibly EMPTY, but don't allow null
    InstanceDetails jsonb NOT NULL,
    LogEvent text NOT NULL, -- reason for event
    LogTimestamp timestamp NOT NULL
);

ALTER TABLE ModelInstanceLog
  ADD CONSTRAINT MODELINSTANCELOG_UKEY UNIQUE (
    ModelId,
    InstanceId,
    LogTimestamp
  );

CREATE INDEX MODELINSTANCELOG_MODEL_TIMESTAMP_INDEX ON ModelInstanceLog (ModelId, LogTimestamp);
CREATE INDEX MODELINSTANCELOG_MODEL_EVENT_INDEX ON ModelInstanceLog (ModelId, LogEvent);
CREATE INDEX MODELINSTANCELOG_INSTANCE_INDEX ON ModelInstanceLog (InstanceId);
CREATE INDEX MODELINSTANCELOG_CORRELATION_INDEX ON ModelInstanceLog (CorrelationId);
