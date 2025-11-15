CREATE TABLE IF NOT EXISTS ModelInstance (
    ModelId text NOT NULL,
    WorkRequestId bigint NOT NULL,
    InstanceId text, -- pod name, if exists
    InstanceDetails jsonb, -- k8s pod, if exists
    State text NOT NULL,
    TerminationReason text, 
    JobSubmissionProcess jsonb,
    LastUpdated timestamp NOT NULL
);

ALTER TABLE ModelInstance
  ADD CONSTRAINT MODELINSTANCE_PK_MODELID_WORKREQUESTID PRIMARY KEY (ModelId, WorkRequestId);

CREATE INDEX MODELINSTANCE_MODELID_INDEX ON ModelInstance (ModelId);

ALTER TABLE ModelInstance
  ADD CONSTRAINT MODELINSTANCE_FK_MODELID FOREIGN KEY (ModelId)
  REFERENCES Model (Id);

ALTER TABLE ModelInstance
  ADD CONSTRAINT MODELINSTANCE_FK_WORKREQUESTID FOREIGN KEY (WorkRequestId)
  REFERENCES WorkRequest (Id);

