CREATE TABLE pipeline_runs (
 id UUID PRIMARY KEY, batch_id TEXT NOT NULL, pipeline TEXT NOT NULL DEFAULT 'commerce',
 status TEXT NOT NULL CHECK(status IN ('running','success','failed')),
 started_at TIMESTAMPTZ NOT NULL DEFAULT now(), finished_at TIMESTAMPTZ,
 total INTEGER NOT NULL DEFAULT 0, valid INTEGER NOT NULL DEFAULT 0,
 duplicates INTEGER NOT NULL DEFAULT 0, source TEXT NOT NULL,
 error TEXT, duration_seconds DOUBLE PRECISION, sla_seconds INTEGER NOT NULL DEFAULT 120
);
CREATE TABLE quality_issues (
 run_id UUID NOT NULL REFERENCES pipeline_runs(id), dataset TEXT NOT NULL,
 rule_id TEXT NOT NULL, severity TEXT NOT NULL, affected INTEGER NOT NULL,
 checked_at TIMESTAMPTZ NOT NULL DEFAULT now(), result TEXT NOT NULL,
 PRIMARY KEY(run_id,dataset,rule_id)
);
CREATE TABLE quarantine (
 run_id UUID NOT NULL REFERENCES pipeline_runs(id), dataset TEXT NOT NULL,
 row_number INTEGER NOT NULL, original JSONB NOT NULL, reasons JSONB NOT NULL,
 PRIMARY KEY(run_id,dataset,row_number)
);
CREATE TABLE sales (
 batch_id TEXT NOT NULL, order_id TEXT NOT NULL, customer_id TEXT NOT NULL,
 product_id TEXT NOT NULL, region TEXT NOT NULL, category TEXT NOT NULL,
 quantity INTEGER NOT NULL, amount NUMERIC(16,2) NOT NULL,
 ordered_at TIMESTAMPTZ NOT NULL, run_id UUID NOT NULL REFERENCES pipeline_runs(id),
 PRIMARY KEY(batch_id,order_id)
);
CREATE TABLE incidents (
 id UUID PRIMARY KEY, run_id UUID NOT NULL REFERENCES pipeline_runs(id),
 severity TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
 cause TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 resolved_at TIMESTAMPTZ, retry_run_id UUID REFERENCES pipeline_runs(id)
);
CREATE TABLE dataset_catalog (
 name TEXT PRIMARY KEY, description TEXT NOT NULL, source TEXT NOT NULL,
 owner TEXT NOT NULL, sensitivity TEXT NOT NULL, frequency TEXT NOT NULL,
 schema JSONB NOT NULL, lineage JSONB NOT NULL, updated_at TIMESTAMPTZ
);
CREATE INDEX ix_runs_started ON pipeline_runs(started_at DESC);
CREATE INDEX ix_issues_run ON quality_issues(run_id);
INSERT INTO dataset_catalog VALUES
('orders','Commerce orders','CSV or demonstration API','Atlas Data Operations','synthetic','daily',
'{"order_id":"string","customer_id":"string","product_id":"string","quantity":"integer","amount":"decimal","ordered_at":"ISO8601"}',
'["orders.csv","bronze/orders","silver/sales","gold/sales","PostgreSQL sales"]',NULL),
('customers','Synthetic customer dimension','CSV','Atlas Customer Analytics','synthetic','daily',
'{"customer_id":"string","region":"string"}','["customers.csv","bronze/customers","silver/customers"]',NULL),
('products','Synthetic product dimension','CSV','Atlas Merchandising','public synthetic','daily',
'{"product_id":"string","category":"string"}','["products.csv","bronze/products","silver/products"]',NULL);

INSERT INTO schema_migrations(version) VALUES ('002_data_platform') ON CONFLICT DO NOTHING;
