CREATE TABLE IF NOT EXISTS Model (
    Id text NOT NULL,
    Enabled boolean NOT NULL,
    Details jsonb NOT NULL,
    LastUpdated timestamp NOT NULL
);

ALTER TABLE Model
  ADD CONSTRAINT MODEL_PKEY PRIMARY KEY (
    Id
  );
