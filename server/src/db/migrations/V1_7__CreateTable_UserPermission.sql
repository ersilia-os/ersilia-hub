CREATE TABLE IF NOT EXISTS UserPermission (
    UserId text NOT NULL,
    Permissions jsonb NOT NULL,
    LastUpdated timestamp NOT NULL
);

ALTER TABLE UserPermission
  ADD CONSTRAINT USERPERMISSION_UKEY UNIQUE (
    UserId
  );

ALTER TABLE UserPermission
  ADD CONSTRAINT USERPERMISSION_FK_USERID FOREIGN KEY (UserId)
  REFERENCES ErsiliaUser (Id);
