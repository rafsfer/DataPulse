ALTER TABLE pipeline_runs ADD COLUMN validation_as_of TIMESTAMPTZ;
INSERT INTO schema_migrations(version) VALUES ('003_execution_reference') ON CONFLICT DO NOTHING;
