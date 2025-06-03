CREATE TABLE IF NOT EXISTS UserSession (
    UserId text NOT NULL,
    SessionId text NOT NULL,
    SessionToken text NOT NULL,
    AuthType text NOT NULL,
    SessionMaxAgeSeconds integer NOT NULL,
    SessionStartTime timestamp NOT NULL
);

ALTER TABLE UserSession
  ADD CONSTRAINT USERSESSION_PKEY PRIMARY KEY (
    UserId, SessionId
  );

ALTER TABLE UserSession
  ADD CONSTRAINT USERSESSION_FK_USERID FOREIGN KEY (UserId)
  REFERENCES ErsiliaUser (Id);

