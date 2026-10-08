# Demonstration governance and retention policy

Dataset ownership, classification, schema and lineage are served by /api/datasets.
All datasets are synthetic. Quarantine originals require the administrative key.
Administrative execution and retry require an API key; read-only aggregate views
are intentionally public on local-only bindings. This is a local portfolio auth
model, not a multi-tenant identity system.

Proposed retention: Bronze and quarantine 30 days, Silver/Gold 90 days, execution
and incident audit 365 days. This policy is documented but automatic deletion is
not implemented. Do not remove source batches required by unresolved incidents.
Back up PostgreSQL and the pipeline_data volume before manual retention work.
Never version .env or real credentials. API keys are held only in browser memory,
not persisted in localStorage or embedded in the frontend bundle.

The fixture uses a fixed 2026-10-07 timestamp for reproducibility. For historical
validation use --as-of 2026-10-07T12:00:00+00:00; later dates intentionally increase
late-record violations. Store the validation reference in each attempt so retries
reproduce the same freshness decision.
