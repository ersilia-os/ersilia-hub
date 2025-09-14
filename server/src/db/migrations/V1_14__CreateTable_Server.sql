CREATE TABLE IF NOT EXISTS Server (
    ServerId text NOT NULL,
    StartupTime timestamp NOT NULL,
    LastCheckIn timestamp NOT NULL,
    IsHealthy int NOT NULL
);

ALTER TABLE Server
  ADD CONSTRAINT SERVER_PK_SERVERID PRIMARY KEY (ServerId);

