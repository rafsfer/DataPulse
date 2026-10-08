-- Populate Gold for batches published before the Gold serving table existed.
INSERT INTO regional_sales(batch_id,region,category,revenue,orders,units,run_id)
SELECT batch_id,region,category,sum(amount),count(*),sum(quantity),run_id
FROM sales GROUP BY batch_id,region,category,run_id
ON CONFLICT (batch_id,region,category) DO NOTHING;
INSERT INTO schema_migrations(version) VALUES ('005_gold_backfill') ON CONFLICT DO NOTHING;
