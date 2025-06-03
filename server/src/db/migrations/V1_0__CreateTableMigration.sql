
CREATE TABLE IF NOT EXISTS Migration (
    Id text NOT NULL,
    MigrationName text NOT NULL,
    Checksum text NOT NULL,
    TMStamp timestamp NOT NULL
);

ALTER TABLE Migration
  ADD CONSTRAINT MIGRATION_PKEY PRIMARY KEY (
    Id
  );

ALTER TABLE Migration
  ADD CONSTRAINT MIGRATION_UKEY UNIQUE (
    MigrationName
  );
