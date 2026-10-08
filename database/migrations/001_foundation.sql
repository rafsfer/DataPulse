-- Applied only on a new PostgreSQL volume; future changes need explicit migrations.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(32) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO schema_migrations (version) VALUES ('001_foundation')
ON CONFLICT (version) DO NOTHING;
