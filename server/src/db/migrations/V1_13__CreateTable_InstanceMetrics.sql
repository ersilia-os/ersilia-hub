CREATE TABLE IF NOT EXISTS InstanceMetrics (
    ModelId text NOT NULL,
    InstanceId text NOT NULL, -- pod name
    CpuRunningAverages jsonb NOT NULL,
    MemoryRunningAverages jsonb NOT NULL,
    TMstamp timestamp NOT NULL
);

ALTER TABLE InstanceMetrics
  ADD CONSTRAINT INSTANCEMETRICS_UKEY UNIQUE (
    ModelId,
    InstanceId
  );

CREATE INDEX INSTANCEMETRICS_MODEL_TIMESTAMP_INDEX ON InstanceMetrics (ModelId, TMstamp);
CREATE INDEX INSTANCEMETRICS_INSTANCE_INDEX ON InstanceMetrics (InstanceId);
