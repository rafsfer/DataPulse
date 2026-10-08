CREATE TABLE regional_sales (
 batch_id TEXT NOT NULL, region TEXT NOT NULL, category TEXT NOT NULL,
 revenue NUMERIC(20,2) NOT NULL, orders BIGINT NOT NULL, units BIGINT NOT NULL,
 run_id UUID NOT NULL REFERENCES pipeline_runs(id),
 PRIMARY KEY(batch_id,region,category)
);
INSERT INTO schema_migrations(version) VALUES ('004_gold_serving') ON CONFLICT DO NOTHING;
