CREATE TABLE IF NOT EXISTS WorkRequest (
    Id bigserial NOT NULL,
    ModelId text NOT NULL,
    UserId text NOT NULL,
    RequestPayload jsonb NOT NULL,
    RequestDate timestamp NOT NULL,
    RequestStatus text NOT NULL,
    RequestStatusReason text,
    ModelJobId text,
    Metadata jsonb NOT NULL,
    LastUpdated timestamp NOT NULL
);

ALTER TABLE WorkRequest
  ADD CONSTRAINT WORKREQUEST_PKEY PRIMARY KEY (
    Id
  );

ALTER TABLE WorkRequest
  ADD CONSTRAINT WORKREQUEST_FK_MODELID FOREIGN KEY (ModelId)
  REFERENCES Model (Id);

ALTER TABLE WorkRequest
  ADD CONSTRAINT WORKREQUEST_FK_USERID FOREIGN KEY (UserId)
  REFERENCES ErsiliaUser (Id);

CREATE INDEX WORKREQUEST_MODEL_REQUESTS_INDEX ON WorkRequest (ModelId, RequestDate);
CREATE INDEX WORKREQUEST_USER_REQUESTS_INDEX ON WorkRequest (UserId, RequestDate);
CREATE INDEX WORKREQUEST_REQUEST_STATUS_INDEX ON WorkRequest (RequestStatus, RequestDate);
CREATE INDEX WORKREQUEST_MODEL_REQUEST_STATUS_INDEX ON WorkRequest (ModelId, RequestStatus, RequestDate);