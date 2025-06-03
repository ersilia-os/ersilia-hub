CREATE TABLE IF NOT EXISTS ErsiliaUser (
    Id text NOT NULL,
    Username text NOT NULL,
    FirstName text NOT NULL,
    LastName text NOT NULL,
    Email text,
    SignUpDate timestamp NOT NULL,
    LastUpdated timestamp NOT NULL
);

ALTER TABLE ErsiliaUser
  ADD CONSTRAINT USER_PKEY PRIMARY KEY (
    Id
  );

ALTER TABLE ErsiliaUser
  ADD CONSTRAINT USER_UKEY UNIQUE (
    Username
  );
