CREATE TABLE IF NOT EXISTS WorkRequestData (
    RequestId bigint NOT NULL,
    RequestPayload jsonb NOT NULL,
    RequestDate timestamp NOT NULL
);

ALTER TABLE WorkRequestData
  ADD CONSTRAINT WORKREQUESTDATA_FK_REQUESTID FOREIGN KEY (RequestId)
  REFERENCES WorkRequest (Id);

CREATE INDEX WORKREQUESTDATA_REQUESTDATE_INDEX ON WorkRequestData (RequestDate);